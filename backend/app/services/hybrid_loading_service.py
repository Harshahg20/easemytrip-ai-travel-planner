import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib

logger = logging.getLogger(__name__)


class HybridLoadingService:
    """
    Hybrid loading service that optimizes itinerary generation based on trip duration:
    - n ≤ 5: Single batched Gemini call (fastest, cohesive)
    - 5 < n ≤ 15: Async parallel day-wise calls (balanced)
    - n > 15: Batched async (groups of 5) (scalable)
    """
    
    def __init__(self, google_ai_service, google_maps_service):
        self.google_ai_service = google_ai_service
        self.google_maps_service = google_maps_service
        self.cache = {}  # Simple in-memory cache (can be replaced with Redis)
    
    async def generate_optimized_itinerary(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate itinerary using optimal strategy based on trip duration
        """
        duration = trip_data.get('duration', 3)
        destination = trip_data.get('destination', 'India')
        
        logger.info(f"Generating optimized itinerary for {duration}-day trip to {destination}")
        
        # Check cache first
        cache_key = self._generate_cache_key(trip_data)
        if cache_key in self.cache:
            logger.info("Returning cached itinerary")
            return self.cache[cache_key]
        
        # Choose optimal strategy
        if duration <= 5:
            result = await self._single_batch_strategy(trip_data)
        elif duration <= 15:
            result = await self._parallel_strategy(trip_data)
        else:
            result = await self._batched_parallel_strategy(trip_data)
        
        # Cache the result
        self.cache[cache_key] = result
        return result
    
    async def _single_batch_strategy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Single batched call for short trips (≤5 days)
        Time Complexity: O(1)
        Expected Latency: ~2-4s
        """
        logger.info("Using single batch strategy for short trip")
        
        try:
            # Generate all days in one call
            prompt = self._create_batch_prompt(trip_data)
            response = await self.google_ai_service._generate_content(prompt)
            itinerary = self._parse_batch_response(response, trip_data)
            
            # Enhance with coordinates
            itinerary = await self._enhance_with_coordinates(itinerary)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Single batch strategy failed: {e}")
            return await self._fallback_parallel_strategy(trip_data)
    
    async def _parallel_strategy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parallel day-wise calls for medium trips (6-15 days)
        Time Complexity: O(n) but parallel
        Expected Latency: ~2s (max single request)
        """
        logger.info("Using parallel strategy for medium trip")
        
        duration = trip_data.get('duration', 3)
        
        try:
            # Create tasks for all days
            tasks = []
            for day_num in range(1, duration + 1):
                task = self._generate_single_day(trip_data, day_num)
                tasks.append(task)
            
            # Execute all tasks in parallel
            day_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle errors
            itinerary = []
            for i, result in enumerate(day_results):
                if isinstance(result, Exception):
                    logger.error(f"Day {i+1} generation failed: {result}")
                    # Generate fallback day
                    fallback_day = await self._generate_fallback_day(trip_data, i+1)
                    itinerary.append(fallback_day)
                else:
                    itinerary.append(result)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Parallel strategy failed: {e}")
            return await self._fallback_parallel_strategy(trip_data)
    
    async def _batched_parallel_strategy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Batched parallel calls for long trips (>15 days)
        Time Complexity: O(n) but batched
        Expected Latency: ~2-4s per batch
        """
        logger.info("Using batched parallel strategy for long trip")
        
        duration = trip_data.get('duration', 3)
        batch_size = 5
        
        try:
            # Create batches
            batches = []
            for i in range(0, duration, batch_size):
                batch_days = list(range(i + 1, min(i + batch_size + 1, duration + 1)))
                batches.append(batch_days)
            
            # Process batches in parallel
            batch_tasks = []
            for batch_days in batches:
                task = self._generate_batch_days(trip_data, batch_days)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Flatten results
            itinerary = []
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    logger.error(f"Batch generation failed: {batch_result}")
                    # Generate fallback for this batch
                    fallback_batch = await self._generate_fallback_batch(trip_data, len(itinerary) + 1)
                    itinerary.extend(fallback_batch)
                else:
                    itinerary.extend(batch_result)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Batched parallel strategy failed: {e}")
            return await self._fallback_parallel_strategy(trip_data)
    
    async def _generate_single_day(self, trip_data: Dict[str, Any], day_num: int) -> Dict[str, Any]:
        """Generate a single day itinerary"""
        try:
            day_data = await self.google_ai_service.generate_daily_itinerary(trip_data, day_num)
            return day_data
        except Exception as e:
            logger.error(f"Failed to generate day {day_num}: {e}")
            raise
    
    async def _generate_batch_days(self, trip_data: Dict[str, Any], day_numbers: List[int]) -> List[Dict[str, Any]]:
        """Generate multiple days in a single batch"""
        try:
            # Create batch prompt for multiple days
            prompt = self._create_multi_day_prompt(trip_data, day_numbers)
            response = await self.google_ai_service._generate_content(prompt)
            days = self._parse_multi_day_response(response, trip_data, day_numbers)
            
            # Enhance with coordinates
            days = await self._enhance_with_coordinates(days)
            
            return days
        except Exception as e:
            logger.error(f"Failed to generate batch {day_numbers}: {e}")
            raise
    
    def _create_batch_prompt(self, trip_data: Dict[str, Any]) -> str:
        """Create prompt for single batch generation"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget = trip_data.get('total_budget', 50000)
        budget_per_day = budget / duration
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        return f"""
        You are an expert travel planner specializing in {destination}. 
        Create a complete {duration}-day itinerary for {destination}.
        
        IMPORTANT: All activities, restaurants, locations, and attractions MUST be specific to {destination}.
        Use real, famous places and attractions in {destination}.
        
        Trip Details:
        - Destination: {destination}
        - Duration: {duration} days
        - Total Budget: {budget} INR
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests/Themes: {themes}
        - Start Date: {trip_data.get('start_date', '2024-01-01')}
        - End Date: {trip_data.get('end_date', '2024-01-05')}
        
        Create a complete itinerary with ALL {duration} days.
        Each day should include:
        - Specific activities at real locations in {destination}
        - Restaurants with actual names or types common in {destination}
        - Accommodation suggestions appropriate for {destination}
        - Transportation details
        - Costs that add up to approximately {budget_per_day:.0f} INR per day
        
        Return ONLY valid JSON array with {duration} days (no markdown, no code blocks):
        [
            {{
                "day_number": 1,
                "date": "{trip_data.get('start_date', '2024-01-01')}",
                "activities": [...],
                "meals": [...],
                "accommodation": {{...}},
                "transportation": "...",
                "transportation_cost": 1000,
                "costs": 3500
            }},
            // ... {duration} days total
        ]
        """
    
    def _create_multi_day_prompt(self, trip_data: Dict[str, Any], day_numbers: List[int]) -> str:
        """Create prompt for multi-day batch generation"""
        destination = trip_data.get('destination', 'India')
        budget = trip_data.get('total_budget', 50000)
        duration = trip_data.get('duration', 3)
        budget_per_day = budget / duration
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        days_str = ', '.join(map(str, day_numbers))
        
        return f"""
        You are an expert travel planner specializing in {destination}. 
        Create itinerary for days {days_str} of a {duration}-day trip to {destination}.
        
        IMPORTANT: All activities, restaurants, locations, and attractions MUST be specific to {destination}.
        Use real, famous places and attractions in {destination}.
        
        Trip Details:
        - Destination: {destination}
        - Duration: {duration} days
        - Total Budget: {budget} INR
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests/Themes: {themes}
        
        Create itinerary for days {days_str} only.
        Each day should include:
        - Specific activities at real locations in {destination}
        - Restaurants with actual names or types common in {destination}
        - Accommodation suggestions appropriate for {destination}
        - Transportation details
        - Costs that add up to approximately {budget_per_day:.0f} INR per day
        
        Return ONLY valid JSON array with {len(day_numbers)} days (no markdown, no code blocks):
        [
            {{
                "day_number": {day_numbers[0]},
                "date": "calculated_date",
                "activities": [...],
                "meals": [...],
                "accommodation": {{...}},
                "transportation": "...",
                "transportation_cost": 1000,
                "costs": 3500
            }},
            // ... {len(day_numbers)} days total
        ]
        """
    
    def _parse_batch_response(self, response: str, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse batch response into day itineraries"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            days = json.loads(response)
            
            # Ensure we have the right number of days
            duration = trip_data.get('duration', 3)
            if len(days) != duration:
                logger.warning(f"Expected {duration} days, got {len(days)}")
                # Pad or truncate as needed
                while len(days) < duration:
                    days.append(self._create_fallback_day(len(days) + 1, trip_data))
                days = days[:duration]
            
            return days
            
        except Exception as e:
            logger.error(f"Failed to parse batch response: {e}")
            # Return fallback days
            return [self._create_fallback_day(i + 1, trip_data) for i in range(trip_data.get('duration', 3))]
    
    def _parse_multi_day_response(self, response: str, trip_data: Dict[str, Any], day_numbers: List[int]) -> List[Dict[str, Any]]:
        """Parse multi-day response into day itineraries"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            days = json.loads(response)
            
            # Ensure we have the right number of days
            if len(days) != len(day_numbers):
                logger.warning(f"Expected {len(day_numbers)} days, got {len(days)}")
                # Pad or truncate as needed
                while len(days) < len(day_numbers):
                    days.append(self._create_fallback_day(day_numbers[len(days)], trip_data))
                days = days[:len(day_numbers)]
            
            return days
            
        except Exception as e:
            logger.error(f"Failed to parse multi-day response: {e}")
            # Return fallback days
            return [self._create_fallback_day(day_num, trip_data) for day_num in day_numbers]
    
    async def _enhance_with_coordinates(self, itinerary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance itinerary with coordinates using Google Maps"""
        try:
            for day in itinerary:
                if day.get('activities'):
                    for activity in day['activities']:
                        if activity.get('location'):
                            coords = await self.google_maps_service.geocode_address(activity['location'])
                            if coords:
                                activity['coordinates'] = coords
                
                if day.get('meals'):
                    for meal in day['meals']:
                        if meal.get('location'):
                            coords = await self.google_maps_service.geocode_address(meal['location'])
                            if coords:
                                meal['coordinates'] = coords
                
                if day.get('accommodation') and day['accommodation'].get('location'):
                    coords = await self.google_maps_service.geocode_address(day['accommodation']['location'])
                    if coords:
                        day['accommodation']['coordinates'] = coords
            
            return itinerary
        except Exception as e:
            logger.error(f"Failed to enhance with coordinates: {e}")
            return itinerary
    
    def _create_fallback_day(self, day_number: int, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback day when generation fails"""
        destination = trip_data.get('destination', 'India')
        budget_per_day = trip_data.get('total_budget', 50000) / trip_data.get('duration', 3)
        
        return {
            "day_number": day_number,
            "date": trip_data.get('start_date', '2024-01-01'),
            "activities": [
                {
                    "time": "09:00",
                    "activity": f"Explore {destination}",
                    "location": f"Various locations in {destination}",
                    "duration": "4 hours",
                    "cost": int(budget_per_day * 0.3),
                    "description": f"General exploration of {destination}"
                }
            ],
            "meals": [
                {
                    "meal_type": "Lunch",
                    "restaurant": f"Local restaurant in {destination}",
                    "cuisine": "Local cuisine",
                    "cost": int(budget_per_day * 0.2),
                    "location": f"{destination}"
                }
            ],
            "accommodation": {
                "name": f"Hotel in {destination}",
                "type": "Standard Hotel",
                "location": f"{destination}",
                "cost": int(budget_per_day * 0.5)
            },
            "transportation": "Local transport",
            "transportation_cost": int(budget_per_day * 0.1),
            "costs": int(budget_per_day)
        }
    
    async def _generate_fallback_day(self, trip_data: Dict[str, Any], day_number: int) -> Dict[str, Any]:
        """Generate a fallback day using the original service"""
        try:
            return await self.google_ai_service.generate_daily_itinerary(trip_data, day_number)
        except Exception as e:
            logger.error(f"Fallback day generation failed: {e}")
            return self._create_fallback_day(day_number, trip_data)
    
    async def _generate_fallback_batch(self, trip_data: Dict[str, Any], start_day: int) -> List[Dict[str, Any]]:
        """Generate a fallback batch"""
        duration = trip_data.get('duration', 3)
        remaining_days = min(5, duration - start_day + 1)
        
        batch = []
        for i in range(remaining_days):
            day_num = start_day + i
            day = await self._generate_fallback_day(trip_data, day_num)
            batch.append(day)
        
        return batch
    
    async def _fallback_parallel_strategy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to simple parallel strategy"""
        logger.info("Using fallback parallel strategy")
        
        duration = trip_data.get('duration', 3)
        tasks = []
        
        for day_num in range(1, duration + 1):
            task = self._generate_fallback_day(trip_data, day_num)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def _generate_cache_key(self, trip_data: Dict[str, Any]) -> str:
        """Generate cache key for trip data"""
        # Create a hash of the trip data for caching
        data_str = json.dumps(trip_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Cache cleared")
