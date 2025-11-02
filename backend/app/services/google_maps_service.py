import googlemaps
import httpx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsService:
    def __init__(self):
        if not settings.google_maps_api_key or settings.google_maps_api_key == "your_google_maps_api_key_here":
            logger.warning("Google Maps API key not configured")
            self.client = None
        else:
            try:
                self.client = googlemaps.Client(key=settings.google_maps_api_key)
            except Exception as e:
                logger.error(f"Error initializing Google Maps client: {e}")
                self.client = None
    
    async def get_place_details(self, place_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get detailed information about a place including business status and opening hours"""
        if not self.client:
            return self._get_fallback_place_details(place_id)
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Default fields to include business status and opening hours
            if fields is None:
                fields = [
                    'place_id', 'name', 'formatted_address', 'geometry', 'rating',
                    'opening_hours', 'business_status', 'types', 'photos',
                    'formatted_phone_number', 'website', 'reviews', 'current_opening_hours'
                ]
            
            place_result = await loop.run_in_executor(
                None,
                lambda: self.client.place(place_id=place_id, fields=fields)
            )
            if place_result.get('result'):
                return self._format_place_details(place_result['result'])
            return self._get_fallback_place_details(place_id)
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return self._get_fallback_place_details(place_id)
    
    async def search_places(self, query: str, location: Optional[Tuple[float, float]] = None, 
                          radius: int = 5000, place_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for places near a location (optimized with parallel detail fetching)"""
        if not self.client:
            return self._get_fallback_search_results(query)
        
        try:
            import asyncio
            # Run blocking Google Maps calls in executor
            loop = asyncio.get_event_loop()
            
            if location:
                places_result = await loop.run_in_executor(
                    None,
                    lambda: self.client.places_nearby(
                        location=location,
                        radius=radius,
                        keyword=query,
                        type=place_type
                    )
                )
            else:
                places_result = await loop.run_in_executor(
                    None,
                    lambda: self.client.places(query=query, type=place_type)
                )
            
            places_list = places_result.get('results', [])
            
            # Format places first
            formatted_places = []
            places_needing_details = []
            
            for place in places_list[:10]:  # Limit to first 10 to avoid too many API calls
                formatted_place = self._format_place_details(place)
                # Track places that need detail fetching for photos
                if not formatted_place.get('photos') and formatted_place.get('place_id'):
                    places_needing_details.append((formatted_place, formatted_place['place_id']))
                formatted_places.append(formatted_place)
            
            # Fetch place details in parallel for places without photos
            if places_needing_details:
                async def fetch_place_detail(place_id):
                    def fetch_details(pid):
                        return self.client.place(
                            place_id=pid,
                            fields=['photos', 'name', 'formatted_address', 'rating', 'geometry']
                        )
                    return await loop.run_in_executor(None, fetch_details, place_id)
                
                # Fetch all place details in parallel
                detail_tasks = [fetch_place_detail(pid) for _, pid in places_needing_details]
                detail_results = await asyncio.gather(*detail_tasks, return_exceptions=True)
                
                # Update formatted places with photos
                for idx, (formatted_place, _) in enumerate(places_needing_details):
                    if idx < len(detail_results) and not isinstance(detail_results[idx], Exception):
                        place_details = detail_results[idx]
                        if place_details and place_details.get('result'):
                            formatted_place['photos'] = place_details['result'].get('photos', [])
                    elif isinstance(detail_results[idx], Exception):
                        logger.warning(f"Could not fetch place details: {detail_results[idx]}")
            
            return formatted_places
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return self._get_fallback_search_results(query)
    
    async def get_directions(self, origin: str, destination: str, 
                           mode: str = "driving", departure_time: Optional[int] = None,
                           alternatives: bool = False) -> Dict[str, Any]:
        """Get directions between two points with optional traffic data"""
        if not self.client:
            return self._get_fallback_directions(origin, destination)
        
        try:
            import asyncio
            from datetime import datetime
            loop = asyncio.get_event_loop()
            
            # Build directions parameters
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode
            }
            
            # Add departure_time for traffic data (must be now or in future)
            if departure_time:
                params["departure_time"] = departure_time
            elif mode == "driving":
                # Use current time for traffic-aware routing
                params["departure_time"] = "now"
            
            # Request alternative routes
            if alternatives:
                params["alternatives"] = True
            
            directions = await loop.run_in_executor(
                None,
                lambda: self.client.directions(**params)
            )
            return self._format_directions(directions, alternatives=alternatives)
        except Exception as e:
            logger.error(f"Error getting directions: {e}")
            return self._get_fallback_directions(origin, destination)
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates"""
        if not self.client:
            return self._get_fallback_coordinates(address)
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            geocode_result = await loop.run_in_executor(
                None,
                lambda: self.client.geocode(address)
            )
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return (location['lat'], location['lng'])
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
        
        return self._get_fallback_coordinates(address)
    
    async def get_nearby_restaurants(self, location: Tuple[float, float], 
                                   radius: int = 1000) -> List[Dict[str, Any]]:
        """Get nearby restaurants"""
        return await self.search_places(
            query="restaurant",
            location=location,
            radius=radius,
            place_type="restaurant"
        )
    
    async def get_nearby_hotels(self, location: Tuple[float, float], 
                              radius: int = 2000) -> List[Dict[str, Any]]:
        """Get nearby hotels"""
        return await self.search_places(
            query="hotel",
            location=location,
            radius=radius,
            place_type="lodging"
        )
    
    async def get_nearby_attractions(self, location: Tuple[float, float], 
                                   radius: int = 5000) -> List[Dict[str, Any]]:
        """Get nearby tourist attractions"""
        return await self.search_places(
            query="tourist attraction",
            location=location,
            radius=radius,
            place_type="tourist_attraction"
        )
    
    async def get_current_weather(self, location: Tuple[float, float]) -> Dict[str, Any]:
        """Get current weather conditions using Google Weather API"""
        if not settings.google_maps_api_key or settings.google_maps_api_key == "your_google_maps_api_key_here":
            logger.warning("Google Maps API key not configured for weather")
            return self._get_fallback_weather()
        
        try:
            lat, lng = location
            url = "https://weather.googleapis.com/v1/currentConditions:lookup"
            
            params = {
                "key": settings.google_maps_api_key,
                "location.latitude": lat,
                "location.longitude": lng
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._format_current_weather(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather: {e.response.status_code} - {e.response.text}")
            return self._get_fallback_weather()
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return self._get_fallback_weather()
    
    async def get_weather_forecast(self, location: Tuple[float, float], days: int = 5) -> Dict[str, Any]:
        """Get daily weather forecast using Google Weather API (up to 10 days)"""
        if not settings.google_maps_api_key or settings.google_maps_api_key == "your_google_maps_api_key_here":
            logger.warning("Google Maps API key not configured for weather")
            return self._get_fallback_forecast()
        
        try:
            lat, lng = location
            url = "https://weather.googleapis.com/v1/forecast:lookup"
            
            # Limit to 10 days as per API documentation
            days = min(days, 10)
            
            params = {
                "key": settings.google_maps_api_key,
                "location.latitude": lat,
                "location.longitude": lng,
                "days": days
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._format_forecast_weather(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching forecast: {e.response.status_code} - {e.response.text}")
            return self._get_fallback_forecast()
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_fallback_forecast()
    
    async def get_hourly_weather(self, location: Tuple[float, float], hours: int = 24) -> Dict[str, Any]:
        """Get hourly weather forecast using Google Weather API (up to 240 hours)"""
        if not settings.google_maps_api_key or settings.google_maps_api_key == "your_google_maps_api_key_here":
            logger.warning("Google Maps API key not configured for weather")
            return self._get_fallback_hourly()
        
        try:
            lat, lng = location
            url = "https://weather.googleapis.com/v1/hourlyForecast:lookup"
            
            # Limit to 240 hours as per API documentation
            hours = min(hours, 240)
            
            params = {
                "key": settings.google_maps_api_key,
                "location.latitude": lat,
                "location.longitude": lng,
                "hours": hours
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._format_hourly_weather(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching hourly forecast: {e.response.status_code} - {e.response.text}")
            return self._get_fallback_hourly()
        except Exception as e:
            logger.error(f"Error fetching hourly weather: {e}")
            return self._get_fallback_hourly()
    
    def _format_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google Weather API current conditions response"""
        try:
            # Google Weather API structure
            current = data.get('currentConditions', {})
            temperature = current.get('temperature', {})
            wind = current.get('wind', {})
            humidity = current.get('humidity', {})
            
            return {
                "type": "current",
                "timestamp": datetime.now().isoformat(),
                "temperature": {
                    "value": temperature.get('value', 0),
                    "unit": temperature.get('unit', 'celsius')
                },
                "condition": current.get('weatherCondition', 'Unknown'),
                "description": current.get('weatherDescription', ''),
                "icon_code": current.get('weatherIconCode', ''),
                "humidity": humidity.get('value', 0),
                "wind": {
                    "speed": wind.get('speed', {}).get('value', 0),
                    "direction": wind.get('direction', {}).get('degrees', 0),
                    "unit": wind.get('speed', {}).get('unit', 'km/h')
                },
                "pressure": current.get('atmosphericPressure', {}).get('value', 0),
                "visibility": current.get('visibility', {}).get('value', 0),
                "uv_index": current.get('uvIndex', {}).get('value', 0),
                "cloud_cover": current.get('cloudCover', 0),
                "precipitation": current.get('precipitation', {}).get('value', 0),
                "feels_like": current.get('apparentTemperature', {}).get('value', temperature.get('value', 0))
            }
        except Exception as e:
            logger.error(f"Error formatting current weather: {e}")
            return self._get_fallback_weather()
    
    def _format_forecast_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google Weather API daily forecast response"""
        try:
            daily_forecasts = []
            forecast_list = data.get('dailyForecasts', [])
            
            for day in forecast_list:
                temp = day.get('temperature', {})
                daily_forecasts.append({
                    "date": day.get('date', ''),
                    "temperature": {
                        "high": temp.get('high', {}).get('value', 0),
                        "low": temp.get('low', {}).get('value', 0),
                        "unit": temp.get('unit', 'celsius')
                    },
                    "condition": day.get('weatherCondition', 'Unknown'),
                    "description": day.get('weatherDescription', ''),
                    "icon_code": day.get('weatherIconCode', ''),
                    "precipitation_probability": day.get('precipitationProbability', 0),
                    "precipitation_amount": day.get('precipitation', {}).get('value', 0),
                    "humidity": day.get('humidity', {}).get('value', 0),
                    "wind_speed": day.get('wind', {}).get('speed', {}).get('value', 0),
                    "uv_index": day.get('uvIndex', {}).get('value', 0),
                    "sunrise": day.get('sunrise', ''),
                    "sunset": day.get('sunset', '')
                })
            
            return {
                "type": "forecast",
                "forecasts": daily_forecasts
            }
        except Exception as e:
            logger.error(f"Error formatting forecast weather: {e}")
            return self._get_fallback_forecast()
    
    def _format_hourly_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google Weather API hourly forecast response"""
        try:
            hourly_forecasts = []
            forecast_list = data.get('hourlyForecasts', [])
            
            for hour in forecast_list:
                temp = hour.get('temperature', {})
                hourly_forecasts.append({
                    "time": hour.get('time', ''),
                    "temperature": {
                        "value": temp.get('value', 0),
                        "unit": temp.get('unit', 'celsius')
                    },
                    "condition": hour.get('weatherCondition', 'Unknown'),
                    "description": hour.get('weatherDescription', ''),
                    "icon_code": hour.get('weatherIconCode', ''),
                    "precipitation_probability": hour.get('precipitationProbability', 0),
                    "precipitation_amount": hour.get('precipitation', {}).get('value', 0),
                    "humidity": hour.get('humidity', {}).get('value', 0),
                    "wind_speed": hour.get('wind', {}).get('speed', {}).get('value', 0),
                    "feels_like": hour.get('apparentTemperature', {}).get('value', 0)
                })
            
            return {
                "type": "hourly",
                "forecasts": hourly_forecasts
            }
        except Exception as e:
            logger.error(f"Error formatting hourly weather: {e}")
            return self._get_fallback_hourly()
    
    def _format_place_details(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Format place details from Google Maps API"""
        geometry = place.get('geometry', {})
        location = geometry.get('location', {})
        opening_hours = place.get('opening_hours', {})
        current_opening_hours = place.get('current_opening_hours', {})
        
        # Determine if place is open now
        is_open_now = None
        if current_opening_hours:
            is_open_now = current_opening_hours.get('open_now')
        elif opening_hours:
            is_open_now = opening_hours.get('open_now')
        
        return {
            "place_id": place.get('place_id'),
            "name": place.get('name'),
            "formatted_address": place.get('formatted_address'),
            "coordinates": {
                "lat": location.get('lat'),
                "lng": location.get('lng')
            },
            "rating": place.get('rating'),
            "price_level": place.get('price_level'),
            "types": place.get('types', []),
            "photos": place.get('photos', []),
            "opening_hours": opening_hours,
            "current_opening_hours": current_opening_hours,
            "weekday_text": opening_hours.get('weekday_text', []),
            "is_open_now": is_open_now,
            "business_status": place.get('business_status', 'OPERATIONAL'),  # OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY
            "reviews": place.get('reviews', [])[:3],  # Limit to 3 reviews
            "website": place.get('website'),
            "phone_number": place.get('formatted_phone_number')
        }
    
    def _format_directions(self, directions: List[Dict[str, Any]], alternatives: bool = False) -> Dict[str, Any]:
        """Format directions from Google Maps API with traffic data"""
        if not directions:
            return {}
        
        # If alternatives requested, return all routes
        if alternatives and len(directions) > 1:
            routes = []
            for route in directions:
                legs = route.get('legs', [])
                if legs:
                    leg = legs[0]
                    routes.append(self._format_single_route(route, leg))
            return {
                "routes": routes,
                "primary_route": self._format_single_route(directions[0], directions[0].get('legs', [{}])[0])
            }
        
        # Single route
        route = directions[0]
        legs = route.get('legs', [])
        
        if not legs:
            return {}
        
        leg = legs[0]
        return self._format_single_route(route, leg)
    
    def _format_single_route(self, route: Dict[str, Any], leg: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single route with traffic information"""
        steps = leg.get('steps', [])
        
        # Extract traffic info
        duration = leg.get('duration', {})
        duration_in_traffic = leg.get('duration_in_traffic', {})
        
        # Calculate traffic delay
        traffic_delay_seconds = 0
        if duration_in_traffic and duration:
            traffic_delay_seconds = duration_in_traffic.get('value', 0) - duration.get('value', 0)
        
        return {
            "distance": leg.get('distance', {}).get('text'),
            "distance_value": leg.get('distance', {}).get('value'),  # in meters
            "duration": duration.get('text'),
            "duration_value": duration.get('value'),  # in seconds
            "duration_in_traffic": duration_in_traffic.get('text') if duration_in_traffic else None,
            "duration_in_traffic_value": duration_in_traffic.get('value') if duration_in_traffic else None,
            "traffic_delay_seconds": traffic_delay_seconds,
            "has_traffic": traffic_delay_seconds > 60,  # More than 1 minute delay
            "start_address": leg.get('start_address'),
            "end_address": leg.get('end_address'),
            "steps": [
                {
                    "instruction": step.get('html_instructions'),
                    "distance": step.get('distance', {}).get('text'),
                    "duration": step.get('duration', {}).get('text'),
                    "travel_mode": step.get('travel_mode')
                }
                for step in steps
            ],
            "overview_polyline": route.get('overview_polyline', {}).get('points'),
            "summary": route.get('summary', '')
        }
    
    def _get_fallback_weather(self) -> Dict[str, Any]:
        """Fallback weather data when API fails"""
        return {
            "type": "current",
            "timestamp": datetime.now().isoformat(),
            "temperature": {
                "value": 25,
                "unit": "celsius"
            },
            "condition": "Unknown",
            "description": "Weather data unavailable",
            "icon_code": "",
            "humidity": 50,
            "wind": {
                "speed": 10,
                "direction": 0,
                "unit": "km/h"
            },
            "pressure": 1013,
            "visibility": 10,
            "uv_index": 5,
            "cloud_cover": 0,
            "precipitation": 0,
            "feels_like": 25,
            "error": "Weather API unavailable"
        }
    
    def _get_fallback_forecast(self) -> Dict[str, Any]:
        """Fallback forecast data when API fails"""
        forecasts = []
        for i in range(5):
            date = datetime.now() + timedelta(days=i)
            forecasts.append({
                "date": date.strftime("%Y-%m-%d"),
                "temperature": {
                    "high": 28,
                    "low": 18,
                    "unit": "celsius"
                },
                "condition": "Unknown",
                "description": "Forecast unavailable",
                "icon_code": "",
                "precipitation_probability": 0,
                "precipitation_amount": 0,
                "humidity": 50,
                "wind_speed": 10,
                "uv_index": 5,
                "sunrise": "06:00",
                "sunset": "18:00"
            })
        return {
            "type": "forecast",
            "forecasts": forecasts,
            "error": "Weather API unavailable"
        }
    
    def _get_fallback_hourly(self) -> Dict[str, Any]:
        """Fallback hourly forecast data when API fails"""
        forecasts = []
        for i in range(24):
            time = datetime.now() + timedelta(hours=i)
            forecasts.append({
                "time": time.isoformat(),
                "temperature": {
                    "value": 25,
                    "unit": "celsius"
                },
                "condition": "Unknown",
                "description": "Forecast unavailable",
                "icon_code": "",
                "precipitation_probability": 0,
                "precipitation_amount": 0,
                "humidity": 50,
                "wind_speed": 10,
                "feels_like": 25
            })
        return {
            "type": "hourly",
            "forecasts": forecasts,
            "error": "Weather API unavailable"
        }
    
    def _get_fallback_place_details(self, place_id: str) -> Dict[str, Any]:
        """Fallback place details when API fails"""
        return {
            "place_id": place_id,
            "name": "Sample Place",
            "formatted_address": "Sample Address",
            "coordinates": {"lat": 28.6139, "lng": 77.209},
            "rating": 4.0,
            "price_level": 2,
            "types": ["tourist_attraction"],
            "photos": [],
            "opening_hours": {},
            "current_opening_hours": {},
            "weekday_text": [],
            "is_open_now": True,
            "business_status": "OPERATIONAL",
            "reviews": [],
            "website": None,
            "phone_number": None
        }
    
    def _get_fallback_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search results when API fails"""
        return [
            {
                "place_id": f"fallback_{query}_1",
                "name": f"Sample {query.title()} 1",
                "formatted_address": "Sample Address 1",
                "coordinates": {"lat": 28.6139, "lng": 77.209},
                "rating": 4.0,
                "price_level": 2,
                "types": ["establishment"],
                "photos": [],
                "opening_hours": {},
                "reviews": [],
                "website": None,
                "phone_number": None
            },
            {
                "place_id": f"fallback_{query}_2",
                "name": f"Sample {query.title()} 2",
                "formatted_address": "Sample Address 2",
                "coordinates": {"lat": 28.6140, "lng": 77.210},
                "rating": 4.2,
                "price_level": 3,
                "types": ["establishment"],
                "photos": [],
                "opening_hours": {},
                "reviews": [],
                "website": None,
                "phone_number": None
            }
        ]
    
    def _get_fallback_directions(self, origin: str, destination: str) -> Dict[str, Any]:
        """Fallback directions when API fails"""
        return {
            "distance": "5 km",
            "distance_value": 5000,
            "duration": "15 minutes",
            "duration_value": 900,
            "duration_in_traffic": None,
            "duration_in_traffic_value": None,
            "traffic_delay_seconds": 0,
            "has_traffic": False,
            "start_address": origin,
            "end_address": destination,
            "steps": [
                {
                    "instruction": f"Start from {origin}",
                    "distance": "0 km",
                    "duration": "0 min",
                    "travel_mode": "driving"
                },
                {
                    "instruction": f"Drive to {destination}",
                    "distance": "5 km",
                    "duration": "15 min",
                    "travel_mode": "driving"
                }
            ],
            "overview_polyline": "",
            "summary": ""
        }
    
    def _get_fallback_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Fallback coordinates when geocoding fails"""
        # Return Delhi coordinates as fallback
        return (28.6139, 77.209)


# Create service instance
google_maps_service = GoogleMapsService()
