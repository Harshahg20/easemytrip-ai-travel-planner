"""
Weather Agent - Specialized agent for fetching and analyzing weather data
Part of the multi-agent smart adjustments system
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import httpx
from ....core.config import settings

logger = logging.getLogger(__name__)


class WeatherAgent:
    """Agent specialized in weather data fetching and analysis"""
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
    
    async def process_request(
        self, 
        user_input: str, 
        user_id: str, 
        context: Dict[str, Any], 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process weather-related requests"""
        try:
            # Extract location and date from context
            destination = context.get("destination") or context.get("location")
            date_str = context.get("date") or context.get("target_date")
            coordinates = context.get("coordinates")
            
            if not destination and not coordinates:
                return {
                    "type": "weather",
                    "message": "Please provide a location to fetch weather data",
                    "status": "error"
                }
            
            # Parse date
            if date_str:
                if isinstance(date_str, str):
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date = date_str
            else:
                date = datetime.now()
            
            # Get coordinates if needed
            if not coordinates and destination:
                from ....services.google_maps_service import google_maps_service
                coordinates = await google_maps_service.geocode_address(destination)
            
            if not coordinates:
                return {
                    "type": "weather",
                    "message": f"Could not find coordinates for {destination}",
                    "status": "error"
                }
            
            # Fetch weather data
            weather_data = await self.fetch_weather_data(coordinates, date)
            
            return {
                "type": "weather",
                "message": self._format_weather_message(weather_data),
                "weather_data": weather_data,
                "status": "success",
                "suggestions": self._generate_weather_suggestions(weather_data)
            }
            
        except Exception as e:
            logger.error(f"Error in weather agent: {e}")
            return {
                "type": "weather",
                "message": "Unable to fetch weather data at this time",
                "status": "error"
            }
    
    async def fetch_weather_data(
        self, 
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap API"""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return {}
        
        try:
            lat, lng = coordinates
            
            # Use current weather API for today, forecast for future dates
            if date.date() == datetime.now().date():
                url = "https://api.openweathermap.org/data/2.5/weather"
            else:
                url = "https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
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
                        "date": date.isoformat(),
                        "is_current": True
                    }
                else:
                    # Forecast - find closest forecast to target date
                    forecasts = data.get("list", [])
                    if forecasts:
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
                            "forecast_time": datetime.fromtimestamp(closest_forecast.get("dt", 0)).isoformat(),
                            "is_current": False
                        }
                    
                    return {}
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {}
    
    def _format_weather_message(self, weather_data: Dict[str, Any]) -> str:
        """Format weather data into a user-friendly message"""
        if not weather_data:
            return "Weather data unavailable"
        
        condition = weather_data.get("description", "Unknown").title()
        temp = weather_data.get("temperature", 0)
        rain = weather_data.get("rain", 0)
        
        message = f"Current Weather: {condition}, Temperature: {temp:.1f}°C"
        if rain > 0:
            message += f", Rain: {rain}mm"
        
        return message
    
    def _generate_weather_suggestions(self, weather_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on weather conditions"""
        suggestions = []
        condition = weather_data.get("condition", "").lower()
        rain = weather_data.get("rain", 0)
        temp = weather_data.get("temperature", 0)
        
        if condition in ["rain", "thunderstorm", "drizzle"] or rain > 0:
            suggestions.append("Consider indoor activities")
            suggestions.append("Reschedule outdoor plans")
        
        if temp < 5:
            suggestions.append("Dress warmly")
        
        if temp > 35:
            suggestions.append("Stay hydrated")
            suggestions.append("Avoid peak sun hours")
        
        return suggestions
