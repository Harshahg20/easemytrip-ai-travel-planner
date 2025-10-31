import google.generativeai as genai
from typing import Dict, List, Any, Optional
import json
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class GoogleAIService:
    def __init__(self):
        self.hybrid_service = None
        # Always load API key directly from .env file first (most reliable)
        api_key = None
        try:
            from dotenv import load_dotenv
            import os
            # Try multiple possible paths for .env file
            env_paths = [
                '.env',  # Current directory
                os.path.join(os.path.dirname(__file__), '..', '..', '.env'),  # Backend root
                os.path.join(os.getcwd(), '.env'),  # Absolute from cwd
            ]
            
            loaded = False
            for env_path in env_paths:
                abs_path = os.path.abspath(env_path)
                if os.path.exists(abs_path):
                    load_dotenv(dotenv_path=abs_path, override=True)
                    api_key = os.getenv('GOOGLE_AI_API_KEY')
                    if api_key:
                        loaded = True
                        logger.info(f"Loaded API key from {abs_path}: {api_key[:10]}...{api_key[-5:]}")
                        break
            
            if not loaded:
                # Fallback: try without specifying path
                load_dotenv(override=True)
                api_key = os.getenv('GOOGLE_AI_API_KEY')
                if api_key:
                    logger.info(f"Loaded API key from .env (auto-detect): {api_key[:10]}...{api_key[-5:]}")
            
            # Remove quotes if present
            if api_key:
                api_key = api_key.strip('"').strip("'")
        except Exception as e:
            logger.warning(f"Could not load API key from .env: {e}")
        
        # Fallback to settings if .env didn't work
        if not api_key or len(api_key) < 30:
            api_key = settings.google_ai_api_key
            if api_key:
                api_key = api_key.strip('"').strip("'")
                logger.info(f"Using API key from settings: {api_key[:10]}...{api_key[-5:]}")
        
        if not api_key or len(api_key) < 30:
            logger.warning("Google AI API key not configured or invalid")
            self.model = None
            return
        
        try:
            genai.configure(api_key=api_key)
            # Use Gemini 2.0 Flash for fastest responses
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info(f"✅ Google AI service initialized with Gemini 2.0 Flash: {api_key[:10]}...{api_key[-5:]}")
            
            # Initialize hybrid loading service
            self._initialize_hybrid_service()
        except Exception as e:
            logger.error(f"Error initializing Google AI service: {e}")
            self.model = None
    
    def _initialize_hybrid_service(self):
        """Initialize the hybrid loading service"""
        try:
            from .hybrid_loading_service import HybridLoadingService
            from .google_maps_service import GoogleMapsService
            
            # Initialize Google Maps service
            maps_service = GoogleMapsService()
            
            # Initialize hybrid service
            self.hybrid_service = HybridLoadingService(self, maps_service)
            logger.info("✅ Hybrid loading service initialized")
        except Exception as e:
            logger.warning(f"Could not initialize hybrid service: {e}")
            self.hybrid_service = None
    
    async def generate_trip_options(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple trip options using Google Gemini AI (optimized for speed)
        """
        if not self.model:
            logger.warning("Google AI model not available, using fallback options")
            return self._get_fallback_trip_options(trip_data)
        
        try:
            # Use optimized prompt based on trip duration
            prompt = self._create_optimized_trip_options_prompt(trip_data)
            response = await self._generate_content(prompt)
            options = self._parse_trip_options_response(response)
            
            if not options or len(options) == 0:
                logger.warning("No options generated, using fallback")
                return self._get_fallback_trip_options(trip_data)
            
            logger.info(f"Successfully generated {len(options)} trip options")
            return options
            
        except Exception as e:
            logger.error(f"Error generating trip options: {e}")
            return self._get_fallback_trip_options(trip_data)

    async def generate_optimized_trip_options(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate trip options using hybrid loading strategy for optimal performance
        """
        if not self.model:
            logger.warning("Google AI model not available, using fallback options")
            return self._get_fallback_trip_options(trip_data)
        
        # Use hybrid service if available
        if self.hybrid_service:
            try:
                logger.info("Using hybrid loading service for optimized generation")
                return await self.hybrid_service.generate_optimized_itinerary(trip_data)
            except Exception as e:
                logger.error(f"Hybrid service failed, falling back to standard: {e}")
        
        # Fallback to standard generation
        return await self.generate_trip_options(trip_data)

    async def generate_trip_options_lazy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trip options with only first day itinerary (lazy loading)"""
        try:
            logger.info(f"Generating lazy trip options for {trip_data.get('destination', 'destination')}")
            
            # Generate basic trip options without full daily itineraries
            options = await self._generate_lazy_trip_options(trip_data)
            
            if not options or len(options) == 0:
                logger.warning("No lazy options generated, using fallback")
                return self._get_fallback_trip_options_lazy(trip_data)
            
            logger.info(f"Successfully generated {len(options)} lazy trip options")
            return options
            
        except Exception as e:
            logger.error(f"Error generating lazy trip options: {e}")
            return self._get_fallback_trip_options_lazy(trip_data)

    async def _generate_lazy_trip_options(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trip options with only first day itinerary (lazy loading)"""
        try:
            # First, generate trip options using Gemini AI (not fallback!)
            if not self.model:
                logger.warning("Google AI model not available, falling back to standard options")
                return self._get_fallback_trip_options_lazy(trip_data)
            
            # Generate trip options using optimized Gemini prompt
            prompt = self._create_optimized_trip_options_prompt(trip_data)
            response = await self._generate_content(prompt)
            trip_options = self._parse_trip_options_response(response)
            
            # If parsing failed or returned empty, try fallback
            if not trip_options or len(trip_options) == 0:
                logger.warning("Failed to parse Gemini response, using fallback")
                trip_options = self._get_fallback_trip_options_lazy(trip_data)
            else:
                logger.info(f"Successfully generated {len(trip_options)} lazy trip options from Gemini")
            
            return trip_options
            
        except Exception as e:
            logger.error(f"Error in lazy trip generation: {e}")
            # Fallback to standard Gemini generation
            try:
                if self.model:
                    prompt = self._create_optimized_trip_options_prompt(trip_data)
                    response = await self._generate_content(prompt)
                    return self._parse_trip_options_response(response)
            except Exception as fallback_error:
                logger.error(f"Fallback generation also failed: {fallback_error}")
            
            return self._get_fallback_trip_options_lazy(trip_data)

    def _create_lazy_trip_options_prompt(self, trip_data: Dict[str, Any]) -> str:
        """Create prompt for generating lazy trip options (only first day)"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget = trip_data.get('total_budget', 50000)
        budget_per_day = budget / duration
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        return f"""
        You are an expert travel planner specializing in Indian destinations. 
        Create 3 detailed, destination-specific trip options for {destination}.
        
        IMPORTANT: All activities, restaurants, locations, and attractions MUST be specific to {destination}.
        Do NOT use generic placeholders. Use real, famous places and attractions in {destination}.
        
        Trip Details:
        - Destination: {destination}
        - Duration: {duration} days
        - Total Budget: {budget} INR
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests/Themes: {themes}
        - Start Date: {trip_data.get('start_date', '2024-01-01')}
        - End Date: {trip_data.get('end_date', '2024-01-05')}
        
        Create 3 distinct options:
        1. Adventure-focused option (theme: "adventure")
        2. Cultural/Heritage-focused option (theme: "cultural")
        3. Balanced option (theme: "balanced") - mix of adventure and culture
        
        For each option, provide ONLY the FIRST DAY itinerary in detail.
        The daily_itineraries array should contain ONLY ONE day (day 1).
        Each daily itinerary should include:
        - Specific activities at real locations in {destination} (name actual places)
        - Restaurants with actual names or types common in {destination}
        - Accommodation suggestions appropriate for {destination}
        - Transportation details
        - Costs that add up to approximately {budget_per_day:.0f} INR per day
        
        Return ONLY valid JSON array (no markdown, no code blocks, no explanations):
        [
            {{
                "option_name": "Adventure Explorer",
                "theme": "adventure",
                "description": "Thrilling adventure activities...",
                "daily_itineraries": [
                    {{
                        "day_number": 1,
                        "date": "{trip_data.get('start_date', '2024-01-01')}",
                        "activities": [
                            {{
                                "time": "09:00",
                                "activity": "Specific activity name",
                                "location": "Real location in {destination}",
                                "duration": "2 hours",
                                "cost": 1000,
                                "description": "Detailed description"
                            }}
                        ],
                        "meals": [
                            {{
                                "meal_type": "Breakfast",
                                "restaurant": "Real restaurant name",
                                "cuisine": "Local cuisine",
                                "cost": 500,
                                "location": "Real location"
                            }}
                        ],
                        "accommodation": {{
                            "name": "Real hotel name",
                            "type": "Hotel type",
                            "location": "Real location",
                            "cost": 2000
                        }},
                        "transportation": "Transportation details",
                        "transportation_cost": 1000,
                        "transportation_cost": 1000,
                        "costs": 3500
                    }}
                ],
                "total_cost": {budget * 0.8},
                "highlights": ["Highlight 1", "Highlight 2", "Highlight 3"]
            }}
        ]
        """

    def _get_fallback_trip_options_lazy(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback trip options with only first day (lazy loading)"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget = trip_data.get('total_budget', 50000)
        budget_per_day = budget / duration
        
        return [
            {
                "option_name": f"{destination} Adventure Explorer",
                "theme": "adventure",
                "description": f"Thrilling adventure activities in {destination}",
                "daily_itineraries": [
                    {
                        "day_number": 1,
                        "date": trip_data.get('start_date', '2024-01-01'),
                        "activities": [
                            {
                                "time": "09:00",
                                "activity": f"Explore {destination} city center",
                                "location": f"Downtown {destination}",
                                "duration": "3 hours",
                                "cost": 1000,
                                "description": f"Walking tour of {destination} highlights"
                            }
                        ],
                        "meals": [
                            {
                                "meal_type": "Lunch",
                                "restaurant": f"Local restaurant in {destination}",
                                "cuisine": "Local cuisine",
                                "cost": 800,
                                "location": f"Downtown {destination}"
                            }
                        ],
                        "accommodation": {
                            "name": f"Hotel in {destination}",
                            "type": "Budget Hotel",
                            "location": f"City center, {destination}",
                            "cost": 2000
                        },
                        "transportation": "Local transport",
                        "transportation_cost": 500,
                        "costs": 3800
                    }
                ],
                "total_cost": budget * 0.8,
                "highlights": [f"Explore {destination}", "Local cuisine", "City highlights"]
            },
            {
                "option_name": f"{destination} Cultural Immersion",
                "theme": "cultural",
                "description": f"Rich cultural experiences in {destination}",
                "daily_itineraries": [
                    {
                        "day_number": 1,
                        "date": trip_data.get('start_date', '2024-01-01'),
                        "activities": [
                            {
                                "time": "10:00",
                                "activity": f"Visit cultural sites in {destination}",
                                "location": f"Historic area, {destination}",
                                "duration": "4 hours",
                                "cost": 1200,
                                "description": f"Cultural tour of {destination}"
                            }
                        ],
                        "meals": [
                            {
                                "meal_type": "Lunch",
                                "restaurant": f"Traditional restaurant in {destination}",
                                "cuisine": "Traditional cuisine",
                                "cost": 600,
                                "location": f"Historic area, {destination}"
                            }
                        ],
                        "accommodation": {
                            "name": f"Heritage hotel in {destination}",
                            "type": "Heritage Hotel",
                            "location": f"Historic area, {destination}",
                            "cost": 2500
                        },
                        "transportation": "Local transport",
                        "transportation_cost": 500,
                        "costs": 4300
                    }
                ],
                "total_cost": budget * 0.8,
                "highlights": [f"Cultural sites in {destination}", "Traditional cuisine", "Heritage experience"]
            },
            {
                "option_name": f"{destination} Balanced Experience",
                "theme": "balanced",
                "description": f"Perfect mix of adventure and culture in {destination}",
                "daily_itineraries": [
                    {
                        "day_number": 1,
                        "date": trip_data.get('start_date', '2024-01-01'),
                        "activities": [
                            {
                                "time": "09:30",
                                "activity": f"City tour of {destination}",
                                "location": f"Various locations in {destination}",
                                "duration": "5 hours",
                                "cost": 1500,
                                "description": f"Comprehensive tour of {destination}"
                            }
                        ],
                        "meals": [
                            {
                                "meal_type": "Lunch",
                                "restaurant": f"Popular restaurant in {destination}",
                                "cuisine": "Mixed cuisine",
                                "cost": 700,
                                "location": f"City center, {destination}"
                            }
                        ],
                        "accommodation": {
                            "name": f"Comfortable hotel in {destination}",
                            "type": "Mid-range Hotel",
                            "location": f"City center, {destination}",
                            "cost": 2200
                        },
                        "transportation": "Local transport",
                        "transportation_cost": 500,
                        "costs": 4400
                    }
                ],
                "total_cost": budget * 0.8,
                "highlights": [f"City tour of {destination}", "Mixed experiences", "Comfortable stay"]
            }
        ]
    
    async def _generate_enhanced_trip_options_removed(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trip options using Gemini AI with ADK enhancement"""
        try:
            # First, generate trip options using Gemini AI (not fallback!)
            if not self.model:
                logger.warning("Google AI model not available, falling back to standard options")
                return self._get_fallback_trip_options(trip_data)
            
            # Generate trip options using Gemini
            prompt = self._create_trip_options_prompt(trip_data)
            response = await self._generate_content(prompt)
            trip_options = self._parse_trip_options_response(response)
            
            # If parsing failed or returned empty, try fallback
            if not trip_options or len(trip_options) == 0:
                logger.warning("Failed to parse Gemini response, using fallback")
                trip_options = self._get_fallback_trip_options(trip_data)
            else:
                logger.info(f"Successfully generated {len(trip_options)} trip options from Gemini")
            
            # Optionally enhance with ADK insights if agents are available
            if self.concierge_agent:
                try:
                    context = {
                        "trip_data": trip_data,
                        "request_type": "trip_planning"
                    }
                    
                    # Get ADK insights (optional enhancement)
                    try:
                        inspiration_response = await self.concierge_agent.subagents['inspiration'].process_request(
                            user_input=f"Inspire me with destinations like {trip_data.get('destination', 'popular destinations')}",
                            user_id="system",
                            context=context,
                            intent={"intent": "inspiration", "sub_agent": "inspiration", "confidence": 0.9, "entities": {}, "urgency": "low"}
                        )
                        
                        planning_response = await self.concierge_agent.subagents['planning'].process_request(
                            user_input=f"Plan a detailed itinerary for {trip_data.get('destination', 'destination')}",
                            user_id="system", 
                            context=context,
                            intent={"intent": "planning", "sub_agent": "planning", "confidence": 0.9, "entities": {}, "urgency": "low"}
                        )
                        
                        # Add ADK insights to options
                        for option in trip_options:
                            option['adk_insights'] = {
                                'inspiration': inspiration_response.get('message', ''),
                                'planning': planning_response.get('message', ''),
                                'enhanced_by_adk': True
                            }
                    except Exception as adk_error:
                        logger.warning(f"ADK enhancement failed, continuing without it: {adk_error}")
                        # Continue without ADK insights
                except Exception as e:
                    logger.warning(f"ADK agents not available for enhancement: {e}")
            
            return trip_options
            
        except Exception as e:
            logger.error(f"Error in enhanced trip generation: {e}")
            # Fallback to standard Gemini generation
            try:
                if self.model:
                    prompt = self._create_trip_options_prompt(trip_data)
                    response = await self._generate_content(prompt)
                    return self._parse_trip_options_response(response)
            except Exception as fallback_error:
                logger.error(f"Fallback generation also failed: {fallback_error}")
            
            return self._get_fallback_trip_options(trip_data)
    
    async def generate_daily_itinerary(self, trip_data: Dict[str, Any], day_number: int) -> Dict[str, Any]:
        """
        Generate detailed daily itinerary for a specific day with coordinates
        Supports weather-adjusted itineraries if weather_data is provided
        """
        try:
            # Check if weather data is provided for weather-adjusted itinerary
            weather_data = trip_data.get("weather_data")
            if weather_data:
                prompt = self._create_weather_adjusted_itinerary_prompt(trip_data, day_number, weather_data)
            else:
                prompt = self._create_daily_itinerary_prompt(trip_data, day_number)
            
            response = await self._generate_content(prompt)
            itinerary = self._parse_daily_itinerary_response(response)
            
            # Enhance with coordinates using Google Maps
            itinerary = await self._enhance_itinerary_with_coordinates(itinerary, trip_data.get('destination', ''))
            
            return itinerary
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
    
    def _create_optimized_trip_options_prompt(self, trip_data: Dict[str, Any]) -> str:
        """Create optimized prompt based on trip duration for faster responses"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget = trip_data.get('total_budget', 50000)
        budget_per_day = budget / duration
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        # Optimize prompt based on trip duration
        if duration <= 3:
            # Short trips - focus on highlights
            prompt_type = "short_trip"
            detail_level = "concise"
        elif duration <= 7:
            # Medium trips - balanced detail
            prompt_type = "medium_trip"
            detail_level = "moderate"
        else:
            # Long trips - comprehensive planning
            prompt_type = "long_trip"
            detail_level = "detailed"
        
        return f"""
        You are an expert travel planner specializing in {destination}. 
        Create 3 destination-specific trip options for a {duration}-day trip.
        
        IMPORTANT: Use only real places in {destination}. No generic placeholders. Keep the plan place-based (no hour-by-hour schedule).
        
        Trip Details:
        - Destination: {destination}
        - Duration: {duration} days
        - Total Budget: {budget} INR
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests/Themes: {themes}
        - Start Date: {trip_data.get('start_date', '2024-01-01')}
        - End Date: {trip_data.get('end_date', '2024-01-05')}
        
        Create 3 distinct options:
        1. Adventure-focused option (theme: "adventure")
        2. Cultural/Heritage-focused option (theme: "cultural")  
        3. Balanced option (theme: "balanced")
        
        For each option, provide ONLY the FIRST DAY as a place-based plan (no times). The JSON must include:
        - "places": array of objects with: place, location, description, estimated_cost
        - "meals": array with: meal_type, restaurant, cuisine, cost, location
        - "accommodation": with: name, type, location, cost
        - "transportation": string, and "transportation_cost": number
        - "costs": total estimated cost for the day
        
        Return ONLY valid JSON array (no markdown, no code blocks, no explanations):
        [
            {{
                "option_name": "Adventure Explorer",
                "theme": "adventure",
                "description": "Thrilling adventure activities...",
                "daily_itineraries": [
                    {{
                        "day_number": 1,
                        "date": "{trip_data.get('start_date', '2024-01-01')}",
                        "places": [
                            {{
                                "place": "Specific attraction name",
                                "location": "Real location in {destination}",
                                "description": "What to do/see here",
                                "estimated_cost": 1000
                            }}
                        ],
                        "meals": [
                            {{
                                "meal_type": "Breakfast",
                                "restaurant": "Real restaurant name",
                                "cuisine": "Local cuisine",
                                "cost": 500,
                                "location": "Real location"
                            }}
                        ],
                        "accommodation": {{
                            "name": "Real hotel name",
                            "type": "Hotel type",
                            "location": "Real location",
                            "cost": 2000
                        }},
                        "transportation": "Transportation details",
                        "transportation_cost": 1000,
                        "costs": 3500
                    }}
                ],
                "total_cost": {budget * 0.8},
                "highlights": ["Highlight 1", "Highlight 2", "Highlight 3"]
            }}
        ]
        """

    def _create_trip_options_prompt(self, trip_data: Dict[str, Any]) -> str:
        """Create prompt for generating trip options"""
        destination = trip_data.get('destination', 'India')
        duration = trip_data.get('duration', 3)
        budget = trip_data.get('total_budget', 50000)
        budget_per_day = budget / duration
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        return f"""
        You are an expert travel planner specializing in Indian destinations. 
        Create 3 detailed, destination-specific trip options for {destination}.
        
        IMPORTANT: All activities, restaurants, locations, and attractions MUST be specific to {destination}.
        Do NOT use generic placeholders. Use real, famous places and attractions in {destination}.
        
        Trip Details:
        - Destination: {destination}
        - Duration: {duration} days
        - Total Budget: {budget} INR
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests/Themes: {themes}
        - Start Date: {trip_data.get('start_date', '2024-01-01')}
        - End Date: {trip_data.get('end_date', '2024-01-05')}
        
        Create 3 distinct options:
        1. Adventure-focused option (theme: "adventure")
        2. Cultural/Heritage-focused option (theme: "cultural")
        3. Balanced option (theme: "balanced") - mix of adventure and culture
        
        For each option, provide COMPLETE daily itineraries for ALL {duration} days.
        Each daily itinerary should include:
        - Specific activities at real locations in {destination} (name actual places)
        - Restaurants with actual names or types common in {destination}
        - Accommodation suggestions appropriate for {destination}
        - Transportation details
        - Costs that add up to approximately {budget_per_day:.0f} INR per day
        
        Return ONLY valid JSON array (no markdown, no code blocks, no explanations):
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
        """Create prompt for generating daily itinerary (place-based, no hourly schedule)"""
        destination = trip_data.get('destination', 'India')
        budget_per_day = trip_data.get('total_budget', 10000) / trip_data.get('duration', 3)
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        
        return f"""
        Create a place-based daily plan (no hour-by-hour schedule) for Day {day_number} in {destination}.
        
        IMPORTANT: Use only real places in {destination}. No generic placeholders. Focus on places to visit and a simple plan.
        
        Trip Details:
        - Destination: {destination}
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests: {themes}
        - Day Number: {day_number}
        - Date: {trip_data.get('start_date', '2024-01-01')}
        
        Provide:
        - 3-5 places to cover (array of objects with: place, location, description, estimated_cost)
        - 2-3 meals (breakfast/lunch/dinner) with: meal_type, restaurant, cuisine, cost, location
        - Accommodation suggestion with: name, type, location, cost
        - Transportation summary string and transportation_cost number
        - daily_budget number and tips array
        
        Return ONLY valid JSON (no markdown, no code blocks, no explanations):
        {{
            "day_number": {day_number},
            "date": "2024-01-01",
            "places": [
                {{
                    "place": "Attraction name",
                    "location": "Area / Address",
                    "description": "What to do/see here",
                    "estimated_cost": 800
                }}
            ],
            "meals": [
                {{
                    "meal_type": "Breakfast",
                    "restaurant": "Restaurant name",
                    "cost": 500,
                    "cuisine": "Local",
                    "location": "Area"
                }}
            ],
            "accommodation": {{
                "name": "Hotel name",
                "type": "Budget/Mid-range/Luxury",
                "cost": 3000,
                "location": "Area"
            }},
            "transportation": "Taxi/Car/Metro ...",
            "transportation_cost": 600,
            "daily_budget": {budget_per_day:.0f},
            "costs": {budget_per_day:.0f},
            "tips": ["Local tip 1", "Local tip 2"]
        }}
        """
    
    def _create_weather_adjusted_itinerary_prompt(
        self, 
        trip_data: Dict[str, Any], 
        day_number: int,
        weather_data: Dict[str, Any]
    ) -> str:
        """Create prompt for generating weather-adjusted daily itinerary"""
        destination = trip_data.get('destination', 'India')
        budget_per_day = trip_data.get('total_budget', 10000) / trip_data.get('duration', 3)
        themes = ', '.join(trip_data.get('themes', ['cultural']))
        current_itinerary = trip_data.get('current_itinerary', {})
        
        weather_condition = weather_data.get("condition", "").lower()
        weather_desc = weather_data.get("description", "")
        temperature = weather_data.get("temperature", 0)
        rain = weather_data.get("rain", 0)
        
        # Build weather context
        weather_context = f"""
WEATHER CONDITIONS FOR THIS DAY:
- Condition: {weather_desc.title()}
- Temperature: {temperature:.1f}°C
- Rain: {rain}mm
- Weather Type: {weather_condition}

IMPORTANT ADJUSTMENTS NEEDED:
"""
        
        if weather_condition in ["rain", "thunderstorm", "drizzle"] or rain > 0:
            weather_context += "- Move outdoor activities indoors or reschedule\n"
            weather_context += "- Suggest indoor alternatives (museums, galleries, covered markets, indoor entertainment)\n"
            weather_context += "- Adjust meal locations to indoor restaurants\n"
        elif temperature < 5:
            weather_context += "- Suggest warm indoor activities\n"
            weather_context += "- Minimize time spent outdoors\n"
        elif temperature > 35:
            weather_context += "- Schedule outdoor activities early morning or late evening\n"
            weather_context += "- Suggest air-conditioned indoor venues for midday\n"
        
        return f"""
        Create a weather-adjusted place-based daily plan (no hour-by-hour schedule) for Day {day_number} in {destination}.
        
        {weather_context}
        
        IMPORTANT: Adjust the current itinerary based on weather conditions. Replace outdoor activities with suitable indoor alternatives when weather is adverse.
        
        CURRENT ITINERARY:
        {json.dumps(current_itinerary, indent=2)}
        
        Trip Details:
        - Destination: {destination}
        - Budget per day: {budget_per_day:.0f} INR
        - Travelers: {trip_data.get('travelers', 2)}
        - Interests: {themes}
        - Day Number: {day_number}
        - Date: {trip_data.get('start_date', '2024-01-01')}
        
        Provide adjusted itinerary with:
        - 3-5 places (indoor alternatives if weather is bad) with: place, location, description, estimated_cost
        - 2-3 meals (indoor restaurants) with: meal_type, restaurant, cuisine, cost, location
        - Accommodation suggestion with: name, type, location, cost
        - Transportation summary and transportation_cost
        - daily_budget and tips array
        
        Return ONLY valid JSON (no markdown, no code blocks, no explanations):
        {{
            "day_number": {day_number},
            "date": "{trip_data.get('start_date', '2024-01-01')}",
            "places": [
                {{
                    "place": "Indoor attraction name",
                    "location": "Area / Address",
                    "description": "What to do/see here (weather-appropriate)",
                    "estimated_cost": 800
                }}
            ],
            "meals": [
                {{
                    "meal_type": "Breakfast",
                    "restaurant": "Restaurant name",
                    "cost": 500,
                    "cuisine": "Local",
                    "location": "Area"
                }}
            ],
            "accommodation": {{
                "name": "Hotel name",
                "type": "Budget/Mid-range/Luxury",
                "cost": 3000,
                "location": "Area"
            }},
            "transportation": "Taxi/Car/Metro ...",
            "transportation_cost": 600,
            "daily_budget": {budget_per_day:.0f},
            "costs": {budget_per_day:.0f},
            "tips": ["Weather-adjusted tip 1", "Weather-adjusted tip 2"]
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
        
        # Configure generation parameters for better JSON output
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
        }
        
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text
    
    def _parse_trip_options_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response for trip options"""
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                # Remove code block markers
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            
            # Extract JSON from response
            start_idx = cleaned_response.find('[')
            end_idx = cleaned_response.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned_response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                # Validate that we got a list
                if isinstance(parsed_data, list) and len(parsed_data) > 0:
                    logger.info(f"Successfully parsed {len(parsed_data)} trip options from Gemini")
                    return parsed_data
                else:
                    logger.warning(f"Parsed data is empty or not a list: {type(parsed_data)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response preview: {response[:500]}")
        except Exception as e:
            logger.error(f"Error parsing trip options response: {e}")
        
        return []
    
    def _parse_daily_itinerary_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for daily itinerary"""
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                # Remove code block markers
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            
            # Extract JSON from response
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned_response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                # Validate that we got a dict
                if isinstance(parsed_data, dict) and len(parsed_data) > 0:
                    # Normalize to place-based format (no hour-wise schedule)
                    places = parsed_data.get('places') or []
                    # If model returned activities with time, convert them to places
                    if not places and parsed_data.get('activities'):
                        converted = []
                        for a in parsed_data.get('activities', []):
                            if not isinstance(a, dict):
                                continue
                            converted.append({
                                "place": a.get("activity") or a.get("place") or "Place",
                                "location": a.get("location"),
                                "description": a.get("description"),
                                "estimated_cost": a.get("cost") or 0,
                            })
                        places = converted
                    parsed_data['places'] = places
                    # Remove verbose fields if present
                    parsed_data.pop('activities', None)
                    # Remove meal time if present to keep things crisp
                    for m in parsed_data.get('meals', []) or []:
                        if isinstance(m, dict) and 'time' in m:
                            m.pop('time', None)
                    logger.info(f"Successfully parsed daily itinerary from Gemini (place-based)")
                    return parsed_data
                else:
                    logger.warning(f"Parsed data is empty or not a dict: {type(parsed_data)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response preview: {response[:500]}")
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
            "places": [
                {
                    "place": "City exploration",
                    "location": f"City center, {trip_data.get('destination','')}",
                    "description": "Explore key attractions and local markets",
                    "estimated_cost": 1000
                }
            ],
            "meals": [
                {
                    "meal_type": "Breakfast",
                    "restaurant": "Local restaurant",
                    "cost": 500,
                    "cuisine": "Local",
                    "location": f"City center, {trip_data.get('destination','')}"
                }
            ],
            "accommodation": {
                "name": "Local hotel",
                "type": "Mid-range",
                "cost": 3000,
                "location": f"City center, {trip_data.get('destination','')}"
            },
            "transportation": "Local transport",
            "transportation_cost": 500,
            "daily_budget": 5000,
            "costs": 5000
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
    
    async def _enhance_itinerary_with_coordinates(self, itinerary: Dict[str, Any], destination: str) -> Dict[str, Any]:
        """Enhance itinerary with coordinates using Google Maps"""
        try:
            from .google_maps_service import google_maps_service
            
            # Add coordinates to activities
            if itinerary.get('activities'):
                for activity in itinerary['activities']:
                    if not activity.get('coordinates') and activity.get('location'):
                        # Try to geocode the location
                        coords = await google_maps_service.geocode_address(f"{activity['location']}, {destination}")
                        if coords:
                            activity['coordinates'] = {
                                'lat': coords[0],
                                'lng': coords[1]
                            }
            # Add coordinates to places (new place-based format)
            if itinerary.get('places'):
                for place in itinerary['places']:
                    if isinstance(place, dict) and place.get('location') and not place.get('coordinates'):
                        coords = await google_maps_service.geocode_address(f"{place['location']}, {destination}")
                        if coords:
                            place['coordinates'] = {
                                'lat': coords[0],
                                'lng': coords[1]
                            }
            
            # Add coordinates to meals
            if itinerary.get('meals'):
                for meal in itinerary['meals']:
                    if not meal.get('coordinates') and meal.get('location'):
                        coords = await google_maps_service.geocode_address(f"{meal['location']}, {destination}")
                        if coords:
                            meal['coordinates'] = {
                                'lat': coords[0],
                                'lng': coords[1]
                            }
            
            # Add coordinates to accommodation
            if itinerary.get('accommodation') and not itinerary['accommodation'].get('coordinates'):
                if itinerary['accommodation'].get('location'):
                    coords = await google_maps_service.geocode_address(f"{itinerary['accommodation']['location']}, {destination}")
                    if coords:
                        itinerary['accommodation']['coordinates'] = {
                            'lat': coords[0],
                            'lng': coords[1]
                        }
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error enhancing itinerary with coordinates: {e}")
            return itinerary


# Create service instance
google_ai_service = GoogleAIService()
