"""
Weather Agent - Specialized agent for fetching and analyzing weather data using Google Weather API
Part of the multi-agent smart adjustments system
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from ....core.config import settings

logger = logging.getLogger(__name__)


class WeatherAgent:
    """Agent specialized in weather data fetching and analysis using Google Weather API"""
    
    def __init__(self):
        self.api_key = settings.google_maps_api_key
    
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
        """Fetch weather data from Google Weather API"""
        from ....services.google_maps_service import google_maps_service
        
        if not self.api_key:
            logger.warning("Google Maps API key not configured for weather")
            return {}
        
        try:
            # Calculate days difference from today
            today = datetime.now().date()
            target_date = date.date()
            days_diff = (target_date - today).days
            
            # Use current weather API for today
            if days_diff == 0:
                weather_data = await google_maps_service.get_current_weather(coordinates)
                
                # Convert Google Weather API format to agent format
                if weather_data:
                    return {
                        "condition": weather_data.get("condition", "Unknown").lower(),
                        "description": weather_data.get("description", ""),
                        "temperature": weather_data.get("temperature", {}).get("value", 0),
                        "feels_like": weather_data.get("feels_like", 0),
                        "humidity": weather_data.get("humidity", 0),
                        "wind_speed": weather_data.get("wind", {}).get("speed", 0),
                        "wind_direction": weather_data.get("wind", {}).get("direction", 0),
                        "clouds": weather_data.get("cloud_cover", 0),
                        "precipitation": weather_data.get("precipitation", 0),
                        "pressure": weather_data.get("pressure", 0),
                        "visibility": weather_data.get("visibility", 0),
                        "uv_index": weather_data.get("uv_index", 0),
                        "date": date.isoformat(),
                        "is_current": True,
                        "timestamp": weather_data.get("timestamp", "")
                    }
            
            # Use daily forecast for future dates (up to 10 days)
            elif 0 < days_diff <= 10:
                forecast_data = await google_maps_service.get_weather_forecast(coordinates, days=days_diff + 1)
                
                if forecast_data and "forecasts" in forecast_data:
                    forecasts = forecast_data["forecasts"]
                    
                    # Find forecast for target date
                    for forecast in forecasts:
                        forecast_date = forecast.get("date", "")
                        if forecast_date.startswith(target_date.isoformat()):
                            temp = forecast.get("temperature", {})
                            avg_temp = (temp.get("high", 0) + temp.get("low", 0)) / 2
                            
                            return {
                                "condition": forecast.get("condition", "Unknown").lower(),
                                "description": forecast.get("description", ""),
                                "temperature": avg_temp,
                                "temperature_high": temp.get("high", 0),
                                "temperature_low": temp.get("low", 0),
                                "feels_like": avg_temp,
                                "humidity": forecast.get("humidity", 0),
                                "wind_speed": forecast.get("wind_speed", 0),
                                "clouds": 0,  # Not available in daily forecast
                                "precipitation": forecast.get("precipitation_amount", 0),
                                "precipitation_probability": forecast.get("precipitation_probability", 0),
                                "uv_index": forecast.get("uv_index", 0),
                                "sunrise": forecast.get("sunrise", ""),
                                "sunset": forecast.get("sunset", ""),
                                "date": date.isoformat(),
                                "forecast_date": forecast.get("date", ""),
                                "is_current": False
                            }
            
            # For past dates or dates beyond 10 days, return empty
            logger.warning(f"Cannot fetch weather for date {days_diff} days from today")
            return {}
                    
        except Exception as e:
            logger.error(f"Error fetching weather data from Google Weather API: {e}")
            return {}
    
    def _format_weather_message(self, weather_data: Dict[str, Any]) -> str:
        """Format weather data into a user-friendly message"""
        if not weather_data:
            return "Weather data unavailable"
        
        condition = weather_data.get("description", weather_data.get("condition", "Unknown")).title()
        temp = weather_data.get("temperature", 0)
        
        # Check if it's current or forecast
        if weather_data.get("is_current", False):
            message = f"Current Weather: {condition}, Temperature: {temp:.1f}°C"
            
            # Add feels like if different
            feels_like = weather_data.get("feels_like", temp)
            if abs(feels_like - temp) > 2:
                message += f" (feels like {feels_like:.1f}°C)"
            
            # Add precipitation if present
            precipitation = weather_data.get("precipitation", 0)
            if precipitation > 0:
                message += f", Precipitation: {precipitation:.1f}mm"
            
            # Add humidity
            humidity = weather_data.get("humidity", 0)
            if humidity > 0:
                message += f", Humidity: {humidity}%"
            
            # Add UV index if high
            uv_index = weather_data.get("uv_index", 0)
            if uv_index >= 6:
                message += f", UV Index: {uv_index} (High)"
        else:
            # Forecast message
            temp_high = weather_data.get("temperature_high", temp)
            temp_low = weather_data.get("temperature_low", temp)
            message = f"Forecast: {condition}, High: {temp_high:.1f}°C, Low: {temp_low:.1f}°C"
            
            # Add precipitation probability
            precip_prob = weather_data.get("precipitation_probability", 0)
            if precip_prob > 30:
                message += f", Rain chance: {precip_prob}%"
        
        return message
    
    def _generate_weather_suggestions(self, weather_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on weather conditions"""
        suggestions = []
        condition = weather_data.get("condition", "").lower()
        precipitation = weather_data.get("precipitation", 0)
        precip_prob = weather_data.get("precipitation_probability", 0)
        temp = weather_data.get("temperature", 0)
        uv_index = weather_data.get("uv_index", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        
        # Rain/Storm suggestions
        if condition in ["rain", "thunderstorm", "drizzle", "storm"] or precipitation > 0:
            suggestions.append("🌧️ Bring an umbrella or raincoat")
            suggestions.append("🏠 Consider indoor activities")
            if "thunderstorm" in condition or "storm" in condition:
                suggestions.append("⚠️ Avoid outdoor activities due to storm conditions")
        elif precip_prob > 50:
            suggestions.append("☔ High chance of rain - bring an umbrella")
        
        # Temperature suggestions
        if temp < 5:
            suggestions.append("🧥 Dress warmly - very cold conditions")
            suggestions.append("❄️ Watch for icy conditions")
        elif temp < 15:
            suggestions.append("🧥 Bring a jacket or sweater")
        elif temp > 35:
            suggestions.append("💧 Stay well hydrated")
            suggestions.append("🌞 Avoid peak sun hours (11am-3pm)")
            suggestions.append("🧴 Use sunscreen")
        elif temp > 28:
            suggestions.append("💧 Stay hydrated")
            suggestions.append("😎 Wear light, breathable clothing")
        
        # UV Index suggestions
        if uv_index >= 8:
            suggestions.append("⚠️ Very high UV index - minimize sun exposure")
            suggestions.append("🧴 Apply SPF 30+ sunscreen regularly")
        elif uv_index >= 6:
            suggestions.append("☀️ High UV index - use sun protection")
        
        # Wind suggestions
        if wind_speed > 40:
            suggestions.append("💨 Very windy conditions - secure loose items")
        elif wind_speed > 25:
            suggestions.append("🌬️ Windy conditions - dress appropriately")
        
        # Snow suggestions
        if "snow" in condition:
            suggestions.append("❄️ Snowy conditions - drive carefully")
            suggestions.append("🧤 Wear warm, waterproof clothing")
        
        # Fog/visibility suggestions
        if "fog" in condition or weather_data.get("visibility", 10000) < 1000:
            suggestions.append("🌫️ Poor visibility - drive carefully")
        
        # General suggestions based on overall conditions
        if condition in ["clear", "sunny"]:
            suggestions.append("☀️ Great weather for outdoor activities!")
        
        return suggestions
