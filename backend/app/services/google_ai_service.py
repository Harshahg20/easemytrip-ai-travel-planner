import google.generativeai as genai
from typing import Dict, List, Any, Optional
import json
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class GoogleAIService:
    def __init__(self):
        if not settings.google_ai_api_key or settings.google_ai_api_key == "your_google_ai_studio_api_key_here":
            logger.warning("Google AI API key not configured")
            self.model = None
            return
        
        try:
            genai.configure(api_key=settings.google_ai_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.error(f"Error initializing Google AI service: {e}")
            self.model = None
    
    async def generate_trip_options(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple trip options using Google Gemini AI
        """
        if not self.model:
            logger.warning("Google AI model not available, using fallback options")
            return self._get_fallback_trip_options(trip_data)
        
        try:
            prompt = self._create_trip_options_prompt(trip_data)
            response = await self._generate_content(prompt)
            return self._parse_trip_options_response(response)
        except Exception as e:
            logger.error(f"Error generating trip options: {e}")
            return self._get_fallback_trip_options(trip_data)
    
    async def generate_daily_itinerary(self, trip_data: Dict[str, Any], day_number: int) -> Dict[str, Any]:
        """
        Generate detailed daily itinerary for a specific day
        """
        try:
            prompt = self._create_daily_itinerary_prompt(trip_data, day_number)
            response = await self._generate_content(prompt)
            return self._parse_daily_itinerary_response(response)
        except Exception as e:
            logger.error(f"Error generating daily itinerary: {e}")
            return self._get_fallback_daily_itinerary(trip_data, day_number)
    
    async def get_travel_recommendations(self, destination: str, interests: List[str]) -> Dict[str, Any]:
        """
        Get travel recommendations for a destination
        """
        try:
            prompt = self._create_recommendations_prompt(destination, interests)
            response = await self._generate_content(prompt)
            return self._parse_recommendations_response(response)
        except Exception as e:
            logger.error(f"Error getting travel recommendations: {e}")
            return self._get_fallback_recommendations(destination, interests)
    
    def _create_trip_options_prompt(self, trip_data: Dict[str, Any]) -> str:
        """Create prompt for generating trip options"""
        return f"""
        You are an expert travel planner specializing in Indian destinations. 
        Create 3 different trip options for the following trip details:
        
        Destination: {trip_data.get('destination', 'India')}
        Duration: {trip_data.get('duration', '3-5 days')}
        Budget: {trip_data.get('total_budget', '50000')} INR
        Travelers: {trip_data.get('travelers', 2)}
        Interests: {', '.join(trip_data.get('themes', ['cultural']))}
        Start Date: {trip_data.get('start_date', '2024-01-01')}
        End Date: {trip_data.get('end_date', '2024-01-05')}
        
        Please create 3 options:
        1. Adventure-focused option
        2. Cultural/Heritage-focused option  
        3. Balanced option (mix of both)
        
        For each option, provide:
        - Option name and theme
        - Brief description
        - Daily itinerary with activities, meals, and accommodation suggestions
        - Estimated costs
        - Key highlights
        
        Return the response as a JSON array with the following structure:
        [
            {{
                "option_name": "Adventure Explorer",
                "theme": "adventure",
                "description": "Thrilling adventure activities...",
                "daily_itineraries": [
                    {{
                        "day_number": 1,
                        "date": "2024-01-01",
                        "activities": [
                            {{
                                "time": "09:00",
                                "activity": "Trekking to scenic viewpoint",
                                "location": "Mountain Trail",
                                "duration": "3 hours",
                                "cost": 2000,
                                "description": "Moderate difficulty trek",
                                "category": "Adventure"
                            }}
                        ],
                        "meals": [
                            {{
                                "meal_type": "Breakfast",
                                "restaurant": "Mountain View Cafe",
                                "cost": 500,
                                "cuisine": "Local"
                            }}
                        ],
                        "accommodation": {{
                            "name": "Adventure Lodge",
                            "type": "Budget",
                            "cost": 3000,
                            "location": "Near trailhead"
                        }}
                    }}
                ],
                "total_cost": 25000,
                "highlights": ["Trekking", "Rock climbing", "Nature photography"]
            }}
        ]
        """
    
    def _create_daily_itinerary_prompt(self, trip_data: Dict[str, Any], day_number: int) -> str:
        """Create prompt for generating daily itinerary"""
        return f"""
        Create a detailed daily itinerary for Day {day_number} of a trip to {trip_data.get('destination', 'India')}.
        
        Trip Details:
        - Destination: {trip_data.get('destination')}
        - Budget per day: {trip_data.get('total_budget', 10000) / trip_data.get('duration', 3)} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests: {', '.join(trip_data.get('themes', ['cultural']))}
        - Date: {trip_data.get('start_date', '2024-01-01')}
        
        Please provide a detailed schedule with:
        - Time-based activities
        - Restaurant recommendations for meals
        - Transportation details
        - Accommodation suggestions
        - Cost estimates
        - Local tips and insights
        
        Return as JSON with the following structure:
        {{
            "day_number": {day_number},
            "date": "2024-01-01",
            "activities": [
                {{
                    "time": "09:00",
                    "activity": "Activity name",
                    "location": "Location",
                    "duration": "2 hours",
                    "cost": 1000,
                    "description": "Detailed description",
                    "category": "Category",
                    "coordinates": {{"lat": 28.6139, "lng": 77.209}}
                }}
            ],
            "meals": [
                {{
                    "meal_type": "Breakfast",
                    "restaurant": "Restaurant name",
                    "cost": 500,
                    "cuisine": "Local",
                    "location": "Location",
                    "time": "08:00"
                }}
            ],
            "accommodation": {{
                "name": "Hotel name",
                "type": "Budget/Mid-range/Luxury",
                "cost": 3000,
                "location": "Location",
                "amenities": ["WiFi", "AC", "Restaurant"]
            }},
            "transport": {{
                "mode": "Car/Taxi/Public",
                "cost": 1000,
                "duration": "1 hour",
                "route": "Route description"
            }},
            "daily_budget": 5000,
            "tips": ["Local tip 1", "Local tip 2"]
        }}
        """
    
    def _create_recommendations_prompt(self, destination: str, interests: List[str]) -> str:
        """Create prompt for travel recommendations"""
        return f"""
        Provide comprehensive travel recommendations for {destination} based on these interests: {', '.join(interests)}.
        
        Include:
        - Top attractions and activities
        - Best restaurants and local cuisine
        - Accommodation recommendations
        - Transportation options
        - Best time to visit
        - Local customs and tips
        - Budget estimates
        - Safety considerations
        
        Return as JSON with the following structure:
        {{
            "destination": "{destination}",
            "attractions": [
                {{
                    "name": "Attraction name",
                    "description": "Description",
                    "category": "Category",
                    "cost": 500,
                    "duration": "2 hours",
                    "best_time": "Morning",
                    "coordinates": {{"lat": 28.6139, "lng": 77.209}}
                }}
            ],
            "restaurants": [
                {{
                    "name": "Restaurant name",
                    "cuisine": "Local/International",
                    "cost_range": "Budget/Mid-range/Luxury",
                    "specialties": ["Dish 1", "Dish 2"],
                    "location": "Location"
                }}
            ],
            "accommodation": [
                {{
                    "name": "Hotel name",
                    "type": "Budget/Mid-range/Luxury",
                    "cost_range": "1000-3000 INR",
                    "location": "Location",
                    "amenities": ["WiFi", "AC"]
                }}
            ],
            "transportation": {{
                "airport": "Airport details",
                "local_transport": ["Taxi", "Bus", "Metro"],
                "tips": ["Transport tip 1", "Transport tip 2"]
            }},
            "best_time": "October to March",
            "budget_estimate": {{
                "budget": "5000-8000 INR/day",
                "mid_range": "8000-15000 INR/day",
                "luxury": "15000+ INR/day"
            }},
            "tips": ["Tip 1", "Tip 2", "Tip 3"]
        }}
        """
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini AI"""
        if not self.model:
            raise Exception("Google AI model not available")
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def _parse_trip_options_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response for trip options"""
        try:
            # Extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing trip options response: {e}")
        
        return []
    
    def _parse_daily_itinerary_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for daily itinerary"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing daily itinerary response: {e}")
        
        return {}
    
    def _parse_recommendations_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for recommendations"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing recommendations response: {e}")
        
        return {}
    
    def _get_fallback_trip_options(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback trip options when AI fails"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget_per_day = trip_data.get('total_budget', 50000) / duration
        
        # Calculate actual trip dates
        start_date = trip_data.get('start_date')
        if start_date:
            from datetime import datetime, timedelta
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif hasattr(start_date, 'date'):
                start_date = start_date
            else:
                start_date = datetime.now()
        else:
            start_date = datetime.now()
        
        # Generate sample daily itineraries with unique content for each day
        daily_itineraries = []
        
        # Define different activities, meals, and locations for each day
        day_activities = [
            ["City Center Exploration", "Local Market Visit"],
            ["Historical Monuments Tour", "Art Gallery Visit"],
            ["Beach Activities", "Water Sports"],
            ["Mountain Hiking", "Scenic Viewpoints"],
            ["Cultural Village Tour", "Traditional Crafts Workshop"]
        ]
        
        day_meals = [
            ["Sunrise Cafe", "Heritage Restaurant", "Rooftop Bistro"],
            ["Local Dhaba", "Traditional Kitchen", "Garden Restaurant"],
            ["Beachside Cafe", "Seafood Shack", "Sunset Bar"],
            ["Mountain Lodge", "Forest Cafe", "Campfire Dinner"],
            ["Village Kitchen", "Artisan Bakery", "Cultural Center"]
        ]
        
        day_locations = [
            ["Downtown Area", "Historic Quarter", "City Center"],
            ["Old Town", "Cultural District", "Heritage Zone"],
            ["Beachfront", "Coastal Area", "Marina District"],
            ["Mountain Region", "Hill Station", "Nature Reserve"],
            ["Rural Village", "Artisan Quarter", "Traditional Area"]
        ]
        
        for day in range(1, duration + 1):
            day_idx = (day - 1) % len(day_activities)  # Cycle through available options
            
            # Calculate the actual date for this day
            current_date = start_date + timedelta(days=day-1)
            
            daily_itineraries.append({
                "day_number": day,
                "date": current_date.isoformat(),
                "activities": [
                    {
                        "time": "09:00",
                        "activity": f"{day_activities[day_idx][0]} - Day {day}",
                        "location": f"{day_locations[day_idx][0]}, {destination}",
                        "duration": "4 hours",
                        "cost": budget_per_day * 0.3,
                        "description": f"Discover the highlights of {destination} on day {day}",
                        "category": "Sightseeing"
                    },
                    {
                        "time": "14:00",
                        "activity": f"{day_activities[day_idx][1]} - Day {day}",
                        "location": f"{day_locations[day_idx][1]}, {destination}",
                        "duration": "3 hours",
                        "cost": budget_per_day * 0.2,
                        "description": f"Immerse in local culture and traditions on day {day}",
                        "category": "Cultural"
                    }
                ],
                "meals": [
                    {
                        "meal_type": "Breakfast",
                        "restaurant": f"{day_meals[day_idx][0]} in {destination}",
                        "cost": budget_per_day * 0.1,
                        "cuisine": "Local",
                        "location": f"{day_locations[day_idx][0]}, {destination}",
                        "time": "08:00"
                    },
                    {
                        "meal_type": "Lunch",
                        "restaurant": f"{day_meals[day_idx][1]} in {destination}",
                        "cost": budget_per_day * 0.15,
                        "cuisine": "Local specialties",
                        "location": f"{day_locations[day_idx][1]}, {destination}",
                        "time": "13:00"
                    },
                    {
                        "meal_type": "Dinner",
                        "restaurant": f"{day_meals[day_idx][2]} in {destination}",
                        "cost": budget_per_day * 0.2,
                        "cuisine": "Local & International",
                        "location": f"{day_locations[day_idx][2]}, {destination}",
                        "time": "19:00"
                    }
                ],
                "accommodation": {
                    "name": f"Day {day} Hotel in {destination}",
                    "type": "Mid-range",
                    "cost": budget_per_day * 0.4,
                    "location": f"{day_locations[day_idx][0]}, {destination}",
                    "amenities": ["WiFi", "AC", "Restaurant", "Room Service"]
                },
                "transport": {
                    "mode": "Taxi/Private Car",
                    "cost": budget_per_day * 0.1,
                    "duration": "2 hours",
                    "route": f"Day {day} city tour of {destination}"
                },
                "daily_budget": budget_per_day * (0.8 + (day * 0.1)),  # Vary budget by day (80% to 120%)
                "tips": [f"Best time to visit attractions in {destination} on day {day}", "Local customs and etiquette"]
            })
        
        return [
            {
                "option_name": "Cultural Heritage",
                "theme": "cultural",
                "description": "Explore the rich cultural heritage and historical sites",
                "daily_itineraries": daily_itineraries,
                "total_cost": trip_data.get('total_budget', 50000) * 0.8,
                "highlights": ["Historical sites", "Local culture", "Traditional food"]
            },
            {
                "option_name": "Adventure Explorer",
                "theme": "adventure",
                "description": "Thrilling adventure activities and outdoor experiences",
                "daily_itineraries": daily_itineraries,
                "total_cost": trip_data.get('total_budget', 50000) * 0.9,
                "highlights": ["Adventure sports", "Nature trails", "Outdoor activities"]
            },
            {
                "option_name": "Balanced Experience",
                "theme": "balanced",
                "description": "Perfect mix of culture, adventure, and relaxation",
                "daily_itineraries": daily_itineraries,
                "total_cost": trip_data.get('total_budget', 50000) * 0.85,
                "highlights": ["Cultural sites", "Moderate adventure", "Local experiences"]
            }
        ]
    
    def _get_fallback_daily_itinerary(self, trip_data: Dict[str, Any], day_number: int) -> Dict[str, Any]:
        """Fallback daily itinerary when AI fails"""
        return {
            "day_number": day_number,
            "date": trip_data.get('start_date', '2024-01-01'),
            "activities": [
                {
                    "time": "09:00",
                    "activity": "City exploration",
                    "location": "City center",
                    "duration": "3 hours",
                    "cost": 1000,
                    "description": "Explore the main attractions",
                    "category": "Sightseeing"
                }
            ],
            "meals": [
                {
                    "meal_type": "Breakfast",
                    "restaurant": "Local restaurant",
                    "cost": 500,
                    "cuisine": "Local"
                }
            ],
            "accommodation": {
                "name": "Local hotel",
                "type": "Mid-range",
                "cost": 3000,
                "location": "City center"
            },
            "daily_budget": 5000
        }
    
    def _get_fallback_recommendations(self, destination: str, interests: List[str]) -> Dict[str, Any]:
        """Fallback recommendations when AI fails"""
        return {
            "destination": destination,
            "attractions": [
                {
                    "name": "Main attraction",
                    "description": "Popular tourist spot",
                    "category": "Sightseeing",
                    "cost": 500
                }
            ],
            "restaurants": [
                {
                    "name": "Local restaurant",
                    "cuisine": "Local",
                    "cost_range": "Mid-range"
                }
            ],
            "accommodation": [
                {
                    "name": "Local hotel",
                    "type": "Mid-range",
                    "cost_range": "3000-5000 INR"
                }
            ],
            "tips": ["Plan ahead", "Book in advance", "Try local food"]
        }


# Create service instance
google_ai_service = GoogleAIService()
