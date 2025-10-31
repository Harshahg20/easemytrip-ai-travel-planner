"""
Smart Adjustments Service
Fetches real-time data for weather, traffic, and attractions to suggest itinerary adjustments
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class SmartAdjustmentsService:
    """Service to fetch and analyze real-time data for smart itinerary adjustments"""
    
    def __init__(self):
        self.weather_api_key = settings.openweather_api_key
        self.google_maps_key = settings.google_maps_api_key
    
    async def get_smart_adjustments(
        self, 
        trip_id: str,
        destination: str,
        date: datetime,
        coordinates: Optional[Tuple[float, float]] = None,
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get smart adjustment suggestions for a specific day
        Fetches weather, traffic, and attractions data in parallel
        """
        adjustments = []
        
        # Get coordinates if not provided
        if not coordinates:
            from .google_maps_service import google_maps_service
            coordinates = await google_maps_service.geocode_address(destination)
            if not coordinates:
                logger.warning(f"Could not geocode destination: {destination}")
                return []
        
        try:
            # Fetch all data in parallel using specialized agents
            weather_data, traffic_data, attractions_data = await asyncio.gather(
                self._fetch_weather_data(coordinates, date),
                self._fetch_traffic_data(coordinates, current_itinerary),
                self._fetch_attractions_data(coordinates, destination),
                return_exceptions=True
            )
            
            # Process weather adjustments
            if isinstance(weather_data, dict) and not isinstance(weather_data, Exception):
                weather_adjustments = self._process_weather_adjustments(
                    weather_data, date, current_itinerary
                )
                adjustments.extend(weather_adjustments)
            
            # Process traffic adjustments
            if isinstance(traffic_data, dict) and not isinstance(traffic_data, Exception):
                traffic_adjustments = self._process_traffic_adjustments(
                    traffic_data, current_itinerary
                )
                adjustments.extend(traffic_adjustments)
            
            # Process attraction adjustments
            if isinstance(attractions_data, list) and not isinstance(attractions_data, Exception):
                attraction_adjustments = self._process_attraction_adjustments(
                    attractions_data, current_itinerary
                )
                adjustments.extend(attraction_adjustments)
            
            # Log any errors
            for data in [weather_data, traffic_data, attractions_data]:
                if isinstance(data, Exception):
                    logger.error(f"Error fetching adjustment data: {data}")
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error getting smart adjustments: {e}")
            return []
    
    async def _fetch_weather_data(
        self, 
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch weather data using OpenWeatherMap API"""
        if not self.weather_api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return {}
        
        try:
            lat, lng = coordinates
            # Use forecast API for future dates, current API for today
            if date.date() == datetime.now().date():
                url = "https://api.openweathermap.org/data/2.5/weather"
            else:
                url = "https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Process weather data
                if date.date() == datetime.now().date():
                    # Current weather
                    return {
                        "condition": data.get("weather", [{}])[0].get("main", "").lower(),
                        "description": data.get("weather", [{}])[0].get("description", ""),
                        "temperature": data.get("main", {}).get("temp", 0),
                        "feels_like": data.get("main", {}).get("feels_like", 0),
                        "humidity": data.get("main", {}).get("humidity", 0),
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "clouds": data.get("clouds", {}).get("all", 0),
                        "rain": data.get("rain", {}).get("1h", 0) if "rain" in data else 0,
                        "date": date.isoformat()
                    }
                else:
                    # Forecast - find closest forecast to target date
                    forecasts = data.get("list", [])
                    if forecasts:
                        # Find forecast closest to target date
                        target_timestamp = date.timestamp()
                        closest_forecast = min(
                            forecasts,
                            key=lambda x: abs(x.get("dt", 0) - target_timestamp)
                        )
                        
                        return {
                            "condition": closest_forecast.get("weather", [{}])[0].get("main", "").lower(),
                            "description": closest_forecast.get("weather", [{}])[0].get("description", ""),
                            "temperature": closest_forecast.get("main", {}).get("temp", 0),
                            "feels_like": closest_forecast.get("main", {}).get("feels_like", 0),
                            "humidity": closest_forecast.get("main", {}).get("humidity", 0),
                            "wind_speed": closest_forecast.get("wind", {}).get("speed", 0),
                            "clouds": closest_forecast.get("clouds", {}).get("all", 0),
                            "rain": closest_forecast.get("rain", {}).get("3h", 0),
                            "date": date.isoformat(),
                            "forecast_time": datetime.fromtimestamp(closest_forecast.get("dt", 0)).isoformat()
                        }
                    
                    return {}
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {}
    
    async def _fetch_traffic_data(
        self,
        coordinates: Tuple[float, float],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch traffic data using Google Maps Directions API"""
        if not self.google_maps_key:
            logger.warning("Google Maps API key not configured")
            return {}
        
        if not current_itinerary:
            return {}
        
        try:
            from .google_maps_service import google_maps_service
            
            # Extract locations from itinerary
            locations = []
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            # Get locations from places or activities
            for item in places + activities:
                location = item.get("location") or item.get("address")
                if location:
                    locations.append(location)
            
            if len(locations) < 2:
                return {}
            
            # Get traffic data for each route segment
            traffic_segments = []
            for i in range(len(locations) - 1):
                origin = locations[i]
                destination = locations[i + 1]
                
                directions = await google_maps_service.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving"
                )
                
                if directions:
                    # Extract traffic info
                    duration = directions.get("duration", "")
                    distance = directions.get("distance", "")
                    
                    # Check if there are traffic delays
                    # Note: Google Maps API includes traffic in duration, but we can check route alternatives
                    traffic_segments.append({
                        "origin": origin,
                        "destination": destination,
                        "duration": duration,
                        "distance": distance,
                        "has_traffic": True  # Assume traffic data is included in duration
                    })
            
            return {
                "segments": traffic_segments,
                "has_delays": len(traffic_segments) > 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            return {}
    
    async def _fetch_attractions_data(
        self,
        coordinates: Tuple[float, float],
        destination: str
    ) -> List[Dict[str, Any]]:
        """Fetch attractions and events data using Google Places API"""
        if not self.google_maps_key:
            logger.warning("Google Maps API key not configured")
            return []
        
        try:
            from .google_maps_service import google_maps_service
            
            # Get nearby attractions
            attractions = await google_maps_service.get_nearby_attractions(
                location=coordinates,
                radius=5000  # 5km radius
            )
            
            # Get nearby events and places that might be relevant
            # Filter for places with good ratings and recent data
            relevant_attractions = []
            for attr in attractions[:10]:  # Limit to top 10
                rating = attr.get("rating", 0)
                if rating >= 4.0:  # Only highly rated places
                    relevant_attractions.append({
                        "name": attr.get("name"),
                        "location": attr.get("formatted_address"),
                        "rating": rating,
                        "types": attr.get("types", []),
                        "coordinates": attr.get("coordinates"),
                        "place_id": attr.get("place_id")
                    })
            
            return relevant_attractions
            
        except Exception as e:
            logger.error(f"Error fetching attractions data: {e}")
            return []
    
    def _process_weather_adjustments(
        self,
        weather_data: Dict[str, Any],
        date: datetime,
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process weather data and create adjustment suggestions"""
        adjustments = []
        condition = weather_data.get("condition", "").lower()
        rain = weather_data.get("rain", 0)
        temperature = weather_data.get("temperature", 0)
        description = weather_data.get("description", "")
        
        # Check if weather affects outdoor activities
        outdoor_conditions = ["clear", "clouds", "sunny"]
        adverse_conditions = ["rain", "thunderstorm", "snow", "drizzle"]
        
        if condition in adverse_conditions or rain > 0:
            # Suggest moving outdoor activities or finding indoor alternatives
            outdoor_activities = []
            if current_itinerary:
                places = current_itinerary.get("places", []) or []
                activities = current_itinerary.get("activities", []) or []
                
                # Identify outdoor activities
                for item in places + activities:
                    activity_name = item.get("activity") or item.get("place") or ""
                    location = item.get("location") or ""
                    
                    # Simple heuristic: check for outdoor keywords
                    outdoor_keywords = ["outdoor", "park", "beach", "hiking", "walking tour", 
                                       "market", "garden", "monument", "temple", "outdoor"]
                    if any(keyword in activity_name.lower() or keyword in location.lower() 
                           for keyword in outdoor_keywords):
                        outdoor_activities.append(activity_name or location)
            
            if outdoor_activities:
                adjustments.append({
                    "id": f"weather_{date.strftime('%Y%m%d')}",
                    "type": "weather",
                    "severity": "medium" if rain < 5 else "high",
                    "title": f"Weather Alert: {description.title()} Expected",
                    "description": f"{description.capitalize()} is forecasted. "
                                 f"We recommend moving outdoor activities indoors or rescheduling. "
                                 f"Affected: {', '.join(outdoor_activities[:3])}",
                    "action": "Adjust Itinerary",
                    "suggestions": [
                        "Move outdoor activities to indoor alternatives",
                        "Reschedule to a day with better weather",
                        "Add indoor attractions as backup plans"
                    ],
                    "weather_data": weather_data,
                    "affected_activities": outdoor_activities
                })
        
        # Temperature warnings
        if temperature < 5:
            adjustments.append({
                "id": f"cold_{date.strftime('%Y%m%d')}",
                "type": "weather",
                "severity": "low",
                "title": "Cold Weather Alert",
                "description": f"Temperature is {temperature:.1f}°C. Dress warmly and consider indoor activities.",
                "action": "View Recommendations",
                "suggestions": ["Wear warm clothing", "Prefer indoor activities"]
            })
        elif temperature > 35:
            adjustments.append({
                "id": f"hot_{date.strftime('%Y%m%d')}",
                "type": "weather",
                "severity": "medium",
                "title": "Hot Weather Alert",
                "description": f"Temperature is {temperature:.1f}°C. Stay hydrated and avoid outdoor activities during peak hours.",
                "action": "View Recommendations",
                "suggestions": ["Stay hydrated", "Schedule outdoor activities in early morning or evening"]
            })
        
        return adjustments
    
    def _process_traffic_adjustments(
        self,
        traffic_data: Dict[str, Any],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process traffic data and create adjustment suggestions"""
        adjustments = []
        segments = traffic_data.get("segments", [])
        
        if not segments:
            return adjustments
        
        # Find segments with significant delays
        for segment in segments:
            duration_str = segment.get("duration", "")
            # Parse duration (e.g., "45 mins" or "1 hour 15 mins")
            # This is a simplified check - in production, parse the duration properly
            if "hour" in duration_str.lower() or int(duration_str.split()[0]) > 30:
                adjustments.append({
                    "id": f"traffic_{segment.get('origin', 'unknown')[:10]}",
                    "type": "traffic",
                    "severity": "medium",
                    "title": "Traffic Alert: Heavy Congestion Detected",
                    "description": f"Significant traffic delays between {segment.get('origin', 'origin')} and "
                                 f"{segment.get('destination', 'destination')}. "
                                 f"Expected travel time: {duration_str}.",
                    "action": "View Alternative Route",
                    "suggestions": [
                        "Leave 20-30 minutes earlier",
                        "Consider public transportation",
                        "Check alternative routes"
                    ],
                    "route_info": segment
                })
                break  # Only show one traffic alert at a time
        
        return adjustments
    
    def _process_attraction_adjustments(
        self,
        attractions_data: List[Dict[str, Any]],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process attractions data and create opportunity suggestions"""
        adjustments = []
        
        if not attractions_data:
            return adjustments
        
        # Find highly-rated attractions not in current itinerary
        if current_itinerary:
            current_places = []
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            for item in places + activities:
                place_name = item.get("activity") or item.get("place") or item.get("name") or ""
                current_places.append(place_name.lower())
            
            # Find new attractions
            new_attractions = [
                attr for attr in attractions_data[:5]
                if not any(attr.get("name", "").lower() in current_place 
                          for current_place in current_places)
            ]
            
            if new_attractions:
                top_attraction = new_attractions[0]
                adjustments.append({
                    "id": f"opportunity_{top_attraction.get('place_id', 'unknown')}",
                    "type": "opportunity",
                    "severity": "low",
                    "title": f"Popular Attraction Nearby: {top_attraction.get('name')}",
                    "description": f"Highly rated attraction ({top_attraction.get('rating', 0)}⭐) near your itinerary. "
                                 f"Consider adding it to your plans!",
                    "action": "Add to Itinerary",
                    "suggestions": [
                        f"Visit {top_attraction.get('name')}",
                        "Check opening hours",
                        "Read reviews"
                    ],
                    "attraction": top_attraction
                })
        
        return adjustments


# Create service instance
smart_adjustments_service = SmartAdjustmentsService()
