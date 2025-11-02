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
        # Google Weather API is available! Use it if Google Maps API key is configured
        # Otherwise fall back to OpenWeatherMap
        # Documentation: https://developers.google.com/maps/documentation/weather/current-conditions
        if settings.google_maps_api_key:
            # Use Google Weather API (same key as Google Maps)
            self.weather_api_key = settings.google_maps_api_key
            self.weather_api_type = "google"
        elif settings.openweather_api_key:
            # Fall back to OpenWeatherMap
            self.weather_api_key = settings.openweather_api_key
            self.weather_api_type = "openweather"
        else:
            self.weather_api_key = None
            self.weather_api_type = None
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
            weather_data_list, traffic_data, routes_data, places_status_data = await asyncio.gather(
                self._fetch_weather_for_places(current_itinerary, date, coordinates),
                self._fetch_traffic_data(coordinates, current_itinerary, date),
                self._fetch_routes_data(current_itinerary, date),
                self._fetch_places_status(current_itinerary),
                return_exceptions=True
            )
            
            # Process weather adjustments for each location
            if isinstance(weather_data_list, list) and not isinstance(weather_data_list, Exception):
                for weather_item in weather_data_list:
                    if weather_item.get("weather_data"):
                        weather_adjustments = self._process_weather_adjustments(
                            weather_item["weather_data"], 
                            date, 
                            current_itinerary,
                            weather_item.get("place_name"),
                            weather_item.get("coordinates")
                        )
                        adjustments.extend(weather_adjustments)
            
            # Process traffic adjustments
            if isinstance(traffic_data, dict) and not isinstance(traffic_data, Exception):
                traffic_adjustments = self._process_traffic_adjustments(
                    traffic_data, current_itinerary
                )
                adjustments.extend(traffic_adjustments)
            
            # Process route updates
            if isinstance(routes_data, dict) and not isinstance(routes_data, Exception):
                route_adjustments = self._process_route_adjustments(
                    routes_data, current_itinerary
                )
                adjustments.extend(route_adjustments)
            
            # Process place status (closed, restrictions)
            if isinstance(places_status_data, list) and not isinstance(places_status_data, Exception):
                place_adjustments = self._process_place_status_adjustments(
                    places_status_data, current_itinerary
                )
                adjustments.extend(place_adjustments)
            
            # Log any errors
            for data in [weather_data_list, traffic_data, routes_data, places_status_data]:
                if isinstance(data, Exception):
                    logger.error(f"Error fetching adjustment data: {data}")
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error getting smart adjustments: {e}")
            return []
    
    async def _fetch_weather_for_places(
        self,
        current_itinerary: Optional[Dict[str, Any]] = None,
        date: datetime = None,
        fallback_coordinates: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch weather data for each place/activity location in the itinerary"""
        if not self.weather_api_key:
            logger.warning("OpenWeatherMap API key not configured - weather data will not be available")
            # Still try fallback if no API key
            if fallback_coordinates:
                logger.info("Attempting to use fallback coordinates despite missing API key")
            return []
        
        if not current_itinerary:
            # Fallback to destination coordinates if no itinerary
            if fallback_coordinates:
                weather_data = await self._fetch_weather_data(fallback_coordinates, date)
                if weather_data:
                    return [{
                        "coordinates": fallback_coordinates,
                        "place_name": "Destination",
                        "weather_data": weather_data
                    }]
            return []
        
        try:
            from .google_maps_service import google_maps_service
            
            # Collect unique places/activities with their locations
            locations_to_check = {}
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            # Process places and activities
            logger.debug(f"Processing {len(places)} places and {len(activities)} activities for weather")
            for item in places + activities:
                place_name = item.get("name") or item.get("activity") or item.get("place") or "Location"
                location_str = item.get("location") or item.get("address") or item.get("name")
                
                # Get coordinates
                coords = None
                if item.get("coordinates"):
                    coords_data = item.get("coordinates")
                    if isinstance(coords_data, dict):
                        coords = (coords_data.get("lat"), coords_data.get("lng"))
                    elif isinstance(coords_data, (list, tuple)) and len(coords_data) >= 2:
                        coords = (coords_data[0], coords_data[1])
                
                # If no coordinates, try to geocode
                if not coords and location_str:
                    try:
                        logger.debug(f"Geocoding location: {location_str} for place: {place_name}")
                        coords = await google_maps_service.geocode_address(location_str)
                        if coords:
                            logger.debug(f"Successfully geocoded {location_str} to {coords}")
                    except Exception as e:
                        logger.warning(f"Could not geocode {location_str}: {e}")
                
                # Use coordinates if available
                if coords and coords[0] and coords[1]:
                    # Use coordinates as key to avoid duplicates
                    coord_key = f"{coords[0]:.4f},{coords[1]:.4f}"
                    if coord_key not in locations_to_check:
                        locations_to_check[coord_key] = {
                            "coordinates": coords,
                            "place_name": place_name,
                            "location": location_str
                        }
                        logger.debug(f"Added location to check: {place_name} at {coords}")
            
            logger.info(f"Found {len(locations_to_check)} unique locations to fetch weather for")
            
            # If no locations found, use fallback
            if not locations_to_check and fallback_coordinates:
                logger.info(f"No locations found in itinerary, using fallback coordinates: {fallback_coordinates}")
                weather_data = await self._fetch_weather_data(fallback_coordinates, date)
                if weather_data:
                    logger.info("Successfully fetched fallback weather data")
                    return [{
                        "coordinates": fallback_coordinates,
                        "place_name": "Destination",
                        "weather_data": weather_data
                    }]
                else:
                    logger.warning("Failed to fetch fallback weather data")
                return []
            
            # Fetch weather for each unique location in parallel
            async def fetch_weather_for_location(loc_info):
                coords = loc_info["coordinates"]
                weather_data = await self._fetch_weather_data(coords, date)
                if weather_data:
                    return {
                        "coordinates": coords,
                        "place_name": loc_info["place_name"],
                        "location": loc_info.get("location"),
                        "weather_data": weather_data
                    }
                return None
            
            weather_tasks = [fetch_weather_for_location(loc_info) for loc_info in locations_to_check.values()]
            weather_results = await asyncio.gather(*weather_tasks, return_exceptions=True)
            
            # Filter out None and exceptions
            valid_results = []
            for result in weather_results:
                if result and not isinstance(result, Exception):
                    valid_results.append(result)
                    logger.debug(f"Successfully fetched weather for {result.get('place_name', 'unknown')}")
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching weather for location: {result}")
            
            logger.info(f"Successfully fetched weather for {len(valid_results)} out of {len(weather_tasks)} locations")
            
            # If no valid results but we have fallback, use it
            if not valid_results and fallback_coordinates:
                logger.info(f"No valid weather results, trying fallback coordinates: {fallback_coordinates}")
                fallback_weather = await self._fetch_weather_data(fallback_coordinates, date)
                if fallback_weather:
                    return [{
                        "coordinates": fallback_coordinates,
                        "place_name": "Destination",
                        "weather_data": fallback_weather
                    }]
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Error fetching weather for places: {e}")
            # Fallback to destination coordinates
            if fallback_coordinates:
                weather_data = await self._fetch_weather_data(fallback_coordinates, date)
                if weather_data:
                    return [{
                        "coordinates": fallback_coordinates,
                        "place_name": "Destination",
                        "weather_data": weather_data
                    }]
            return []
    
    async def _fetch_weather_data(
        self, 
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch weather data for a specific location using Google Weather API or OpenWeatherMap"""
        if not self.weather_api_key:
            return {}
        
        try:
            lat, lng = coordinates
            
            if self.weather_api_type == "google":
                result = await self._fetch_google_weather_data(coordinates, date)
                # If Google Weather fails (returns empty), fall back to OpenWeather
                if not result and settings.openweather_api_key:
                    logger.warning("Google Weather API failed, falling back to OpenWeather")
                    return await self._fetch_openweather_data(coordinates, date)
                return result
            else:
                return await self._fetch_openweather_data(coordinates, date)
                
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {}
    
    async def _fetch_google_weather_data(
        self,
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch weather data using Google Weather API
        Documentation: https://developers.google.com/maps/documentation/weather/current-conditions
        """
        lat, lng = coordinates
        
        try:
            # Google Weather API uses GET requests with URL parameters
            # For current conditions (today)
            if date.date() == datetime.now().date():
                url = "https://weather.googleapis.com/v1/currentConditions:lookup"
                params = {
                    "key": self.weather_api_key,
                    "location.latitude": lat,
                    "location.longitude": lng
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Process Google Weather API response structure
                    # Reference: https://developers.google.com/maps/documentation/weather/current-conditions
                    weather_condition = data.get("weatherCondition", {})
                    condition_type = weather_condition.get("type", "CLEAR").lower()
                    condition_desc = weather_condition.get("description", {}).get("text", "Clear")
                    
                    temp_obj = data.get("temperature", {})
                    temp_value = temp_obj.get("degrees", 0)
                    
                    feels_like_obj = data.get("feelsLikeTemperature", {})
                    feels_like_value = feels_like_obj.get("degrees", temp_value)
                    
                    wind_obj = data.get("wind", {})
                    wind_speed_obj = wind_obj.get("speed", {})
                    wind_speed_value = wind_speed_obj.get("value", 0)
                    # Google API returns in KILOMETERS_PER_HOUR, no conversion needed
                    
                    precipitation_obj = data.get("precipitation", {})
                    qpf_obj = precipitation_obj.get("qpf", {})
                    rain_value = qpf_obj.get("quantity", 0)
                    
                    return {
                        "condition": condition_type,
                        "description": condition_desc,
                        "temperature": temp_value,
                        "feels_like": feels_like_value,
                        "humidity": data.get("relativeHumidity", 0),
                        "wind_speed": wind_speed_value,  # Already in km/h
                        "clouds": data.get("cloudCover", 0),
                        "rain": rain_value,
                        "date": date.isoformat(),
                        "location_coords": {"lat": lat, "lng": lng}
                    }
            else:
                # For future dates, we'll fetch forecast (handled separately in _fetch_google_weather_forecast_for_period)
                # For individual date lookup, we can use daily forecast endpoint
                return await self._fetch_google_forecast_for_date(coordinates, date)
                    
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text[:200] if e.response.text else str(e)
            
            logger.error(f"Google Weather API HTTP error: {e.response.status_code} - {error_detail}")
            return self._generate_fallback_weather(coordinates, date)
        except Exception as e:
            logger.error(f"Error fetching Google weather data: {e}", exc_info=True)
            return self._generate_fallback_weather(coordinates, date)
    
    async def _fetch_google_forecast_for_date(
        self,
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch forecast for a specific date using Google Weather API daily forecast"""
        lat, lng = coordinates
        
        try:
            # Use daily forecast endpoint
            # Documentation: https://developers.google.com/maps/documentation/weather/daily-forecast
            # Note: Endpoint format may need to be verified with actual API
            url = "https://weather.googleapis.com/v1/forecastDaily"
            params = {
                "key": self.weather_api_key,
                "location.latitude": lat,
                "location.longitude": lng,
                "days": 10  # Request up to 10 days
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Find forecast for the target date
                daily_forecast = data.get("dailyForecast", {})
                days = daily_forecast.get("days", [])
                
                target_date_str = date.strftime("%Y-%m-%d")
                
                for day_forecast in days:
                    forecast_date_str = day_forecast.get("date", "").split("T")[0]
                    if forecast_date_str == target_date_str:
                        # Process the forecast day
                        weather_condition = day_forecast.get("weatherCondition", {})
                        condition_type = weather_condition.get("type", "CLEAR").lower()
                        condition_desc = weather_condition.get("description", {}).get("text", "Clear")
                        
                        # Get temperature (use high or average)
                        high_temp_obj = day_forecast.get("highTemperature", {})
                        low_temp_obj = day_forecast.get("lowTemperature", {})
                        high_temp = high_temp_obj.get("degrees", 0)
                        low_temp = low_temp_obj.get("degrees", 0)
                        avg_temp = (high_temp + low_temp) / 2 if (high_temp and low_temp) else high_temp or low_temp
                        
                        wind_obj = day_forecast.get("wind", {})
                        wind_speed_obj = wind_obj.get("speed", {}) if wind_obj else {}
                        wind_speed_value = wind_speed_obj.get("value", 0) if wind_speed_obj else 0
                        
                        precipitation_obj = day_forecast.get("precipitation", {})
                        qpf_obj = precipitation_obj.get("qpf", {}) if precipitation_obj else {}
                        rain_value = qpf_obj.get("quantity", 0) if qpf_obj else 0
                        
                        return {
                            "condition": condition_type,
                            "description": condition_desc,
                            "temperature": avg_temp,
                            "feels_like": avg_temp,  # Forecast may not have feels_like
                            "humidity": day_forecast.get("relativeHumidity", 0),
                            "wind_speed": wind_speed_value,
                            "clouds": day_forecast.get("cloudCover", 0),
                            "rain": rain_value,
                            "date": date.isoformat(),
                            "location_coords": {"lat": lat, "lng": lng}
                        }
                
                logger.warning(f"No forecast found for date {target_date_str}")
                return self._generate_fallback_weather(coordinates, date)
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text[:200] if e.response.text else str(e)
            
            logger.error(f"Google Weather Forecast API HTTP error: {e.response.status_code} - {error_detail}")
            return self._generate_fallback_weather(coordinates, date)
        except Exception as e:
            logger.error(f"Error fetching Google forecast for date: {e}", exc_info=True)
            return self._generate_fallback_weather(coordinates, date)
    
    async def _fetch_openweather_data(
        self,
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Fetch weather data using OpenWeatherMap API (fallback)"""
        lat, lng = coordinates
        
        try:
            # Use forecast API for future dates, current API for today
            if date.date() == datetime.now().date():
                url = "https://api.openweathermap.org/data/2.5/weather"
            else:
                url = "https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                "lat": lat,
                "lon": lng,
                "appid": settings.openweather_api_key,
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
                        "date": date.isoformat(),
                        "location_coords": {"lat": lat, "lng": lng}
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
                            "forecast_time": datetime.fromtimestamp(closest_forecast.get("dt", 0)).isoformat(),
                            "location_coords": {"lat": lat, "lng": lng}
                        }
                    
                    return {}
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching OpenWeather data: {e}")
            # Generate fallback weather data
            return self._generate_fallback_weather(coordinates, date)
        except Exception as e:
            logger.error(f"Error fetching OpenWeather data: {e}")
            # Generate fallback weather data
            return self._generate_fallback_weather(coordinates, date)
    
    def _generate_fallback_weather(
        self,
        coordinates: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Generate reasonable fallback weather data based on location and date when APIs fail"""
        import random
        
        lat, lng = coordinates
        
        # Determine season based on latitude and month
        month = date.month
        is_northern = lat > 0
        
        # Determine season
        if is_northern:
            is_summer = month in [6, 7, 8]
            is_winter = month in [12, 1, 2]
        else:
            is_summer = month in [12, 1, 2]
            is_winter = month in [6, 7, 8]
        
        # Base temperature on latitude and season
        abs_lat = abs(lat)
        if abs_lat < 23.5:  # Tropical
            base_temp = 28 if is_summer else 25
        elif abs_lat < 45:  # Temperate
            base_temp = 25 if is_summer else 10
        else:  # Cold
            base_temp = 15 if is_summer else -5
        
        # Add some variation
        temp = base_temp + random.randint(-3, 3)
        feels_like = temp + random.randint(-2, 2)
        
        # Determine weather condition
        conditions = ["clear", "partly cloudy", "cloudy", "rain"]
        weights = [0.4, 0.3, 0.2, 0.1] if not is_winter else [0.3, 0.3, 0.3, 0.1]
        condition = random.choices(conditions, weights=weights)[0]
        
        # Set weather parameters based on condition
        if condition == "clear":
            humidity = random.randint(40, 60)
            clouds = random.randint(0, 20)
            rain = 0
            description = "Clear sky"
        elif condition == "partly cloudy":
            humidity = random.randint(50, 70)
            clouds = random.randint(20, 60)
            rain = 0
            description = "Partly cloudy"
        elif condition == "cloudy":
            humidity = random.randint(60, 80)
            clouds = random.randint(60, 90)
            rain = 0
            description = "Overcast clouds"
        else:  # rain
            humidity = random.randint(70, 90)
            clouds = random.randint(80, 100)
            rain = random.uniform(0.5, 3.0)
            description = "Light rain"
        
        wind_speed = random.uniform(5, 15)
        
        logger.info(f"Generated fallback weather for ({lat}, {lng}) on {date.date()}: {temp}°C, {condition}")
        
        return {
            "condition": condition,
            "description": description,
            "temperature": round(temp, 1),
            "feels_like": round(feels_like, 1),
            "humidity": humidity,
            "wind_speed": round(wind_speed, 1),
            "clouds": clouds,
            "rain": round(rain, 2),
            "date": date.isoformat(),
            "location_coords": {"lat": lat, "lng": lng},
            "is_fallback": True
        }
    
    async def _fetch_weather_forecast_for_period(
        self,
        coordinates: Tuple[float, float],
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Fetch weather forecast for a date range and organize by date"""
        if not self.weather_api_key:
            api_name = "Google Maps" if self.weather_api_type == "google" else "OpenWeatherMap"
            logger.warning(f"{api_name} API key not configured")
            return None
        
        if self.weather_api_type == "google":
            result = await self._fetch_google_weather_forecast_for_period(coordinates, start_date, end_date)
            # If Google Weather fails, fall back to OpenWeather
            if not result and settings.openweather_api_key:
                logger.warning("Google Weather API forecast failed, falling back to OpenWeather")
                return await self._fetch_openweather_forecast_for_period(coordinates, start_date, end_date)
            return result
        else:
            return await self._fetch_openweather_forecast_for_period(coordinates, start_date, end_date)
    
    async def _fetch_google_weather_forecast_for_period(
        self,
        coordinates: Tuple[float, float],
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Fetch Google Weather API forecast for a date range
        Documentation: https://developers.google.com/maps/documentation/weather/daily-forecast
        """
        try:
            lat, lng = coordinates
            # Google Weather API uses GET requests with URL parameters
            url = "https://weather.googleapis.com/v1/forecastDaily:lookup"
            
            # Calculate number of days needed (up to 10 days max per API)
            total_days = (end_date.date() - start_date.date()).days + 1
            days_param = min(total_days, 10)  # Google API supports up to 10 days
            
            params = {
                "key": self.weather_api_key,
                "location.latitude": lat,
                "location.longitude": lng,
                "days": days_param
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Organize forecasts by date
                forecast_by_date = {}
                
                # Get daily forecast
                daily_forecast = data.get("dailyForecast", {})
                days = daily_forecast.get("days", [])
                
                if not days:
                    logger.warning("No forecast data in Google Weather API response")
                    return None
                
                # Process each day's forecast
                for day_forecast in days:
                    date_str = day_forecast.get("date", "")
                    if date_str:
                        # Parse date string (format: "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SSZ")
                        try:
                            forecast_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
                            # Only include dates within trip period
                            if start_date.date() <= forecast_date <= end_date.date():
                                date_key = forecast_date.isoformat()
                                
                                # Process Google Weather API response structure
                                weather_condition = day_forecast.get("weatherCondition", {})
                                condition_type = weather_condition.get("type", "CLEAR").lower()
                                condition_desc = weather_condition.get("description", {}).get("text", "Clear")
                                
                                # Get temperature (average of high and low)
                                high_temp_obj = day_forecast.get("highTemperature", {})
                                low_temp_obj = day_forecast.get("lowTemperature", {})
                                high_temp = high_temp_obj.get("degrees", 0)
                                low_temp = low_temp_obj.get("degrees", 0)
                                avg_temp = (high_temp + low_temp) / 2 if (high_temp and low_temp) else high_temp or low_temp
                                
                                wind_obj = day_forecast.get("wind", {})
                                wind_speed_obj = wind_obj.get("speed", {}) if wind_obj else {}
                                wind_speed_value = wind_speed_obj.get("value", 0) if wind_speed_obj else 0
                                
                                precipitation_obj = day_forecast.get("precipitation", {})
                                qpf_obj = precipitation_obj.get("qpf", {}) if precipitation_obj else {}
                                rain_value = qpf_obj.get("quantity", 0) if qpf_obj else 0
                                
                                forecast_by_date[date_key] = {
                                    "condition": condition_type,
                                    "description": condition_desc,
                                    "temperature": avg_temp,
                                    "feels_like": avg_temp,  # Forecast may not have separate feels_like
                                    "humidity": day_forecast.get("relativeHumidity", 0),
                                    "wind_speed": wind_speed_value,  # Already in km/h
                                    "clouds": day_forecast.get("cloudCover", 0),
                                    "rain": rain_value,
                                    "date": date_str,
                                    "location_coords": {"lat": lat, "lng": lng}
                                }
                        except Exception as e:
                            logger.warning(f"Error parsing forecast date {date_str}: {e}")
                            continue
                
                # For today, also get current conditions (more accurate than forecast)
                if start_date.date() == datetime.now().date():
                    current_weather = await self._fetch_google_weather_data(coordinates, datetime.now())
                    if current_weather:
                        today_key = datetime.now().date().isoformat()
                        forecast_by_date[today_key] = current_weather
                
                logger.info(f"Fetched Google weather forecast for {len(forecast_by_date)} dates")
                
                if not forecast_by_date:
                    logger.warning("No forecast data within trip period")
                    return None
                
                return {
                    "destination_coordinates": coordinates,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "forecast_by_date": forecast_by_date,
                    "cached_at": datetime.now().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text[:200] if e.response.text else str(e)
            
            logger.error(f"HTTP status error fetching Google weather forecast: {e.response.status_code} - {error_detail}")
            if e.response.status_code == 401:
                logger.error("Invalid Google Maps API key. Please check your GOOGLE_MAPS_API_KEY environment variable.")
            elif e.response.status_code == 403:
                logger.error("Google Weather API not enabled or API key lacks permissions. Please enable Weather API in Google Cloud Console.")
            elif e.response.status_code == 429:
                logger.error("Google Weather API rate limit exceeded. Please try again later.")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Google weather forecast: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Google weather forecast: {e}", exc_info=True)
            return None
    
    async def _fetch_openweather_forecast_for_period(
        self,
        coordinates: Tuple[float, float],
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Fetch OpenWeatherMap forecast for a date range (fallback)"""
        
        try:
            lat, lng = coordinates
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
                
                forecasts = data.get("list", [])
                if not forecasts:
                    logger.warning("No forecast data in API response")
                    return None
                
                # Organize forecasts by date
                forecast_by_date = {}
                
                # Current date for today's weather if needed
                if start_date.date() == datetime.now().date():
                    # Get current weather for today
                    current_url = "https://api.openweathermap.org/data/2.5/weather"
                    try:
                        current_response = await client.get(current_url, params=params)
                        if current_response.status_code == 200:
                            current_data = current_response.json()
                            today_key = datetime.now().date().isoformat()
                            forecast_by_date[today_key] = {
                                "condition": current_data.get("weather", [{}])[0].get("main", "").lower(),
                                "description": current_data.get("weather", [{}])[0].get("description", ""),
                                "temperature": current_data.get("main", {}).get("temp", 0),
                                "feels_like": current_data.get("main", {}).get("feels_like", 0),
                                "humidity": current_data.get("main", {}).get("humidity", 0),
                                "wind_speed": current_data.get("wind", {}).get("speed", 0),
                                "clouds": current_data.get("clouds", {}).get("all", 0),
                                "rain": current_data.get("rain", {}).get("1h", 0) if "rain" in current_data else 0,
                                "date": datetime.now().isoformat(),
                                "location_coords": {"lat": lat, "lng": lng}
                            }
                    except Exception as e:
                        logger.warning(f"Could not fetch current weather: {e}")
                
                # Process forecast list (3-hour intervals for up to 5 days)
                for forecast in forecasts:
                    forecast_time = datetime.fromtimestamp(forecast.get("dt", 0))
                    forecast_date = forecast_time.date()
                    date_key = forecast_date.isoformat()
                    
                    # Only include forecasts within trip period
                    if start_date.date() <= forecast_date <= end_date.date():
                        # If we already have a forecast for this date, use the one closest to noon
                        if date_key not in forecast_by_date:
                            forecast_by_date[date_key] = {
                                "condition": forecast.get("weather", [{}])[0].get("main", "").lower(),
                                "description": forecast.get("weather", [{}])[0].get("description", ""),
                                "temperature": forecast.get("main", {}).get("temp", 0),
                                "feels_like": forecast.get("main", {}).get("feels_like", 0),
                                "humidity": forecast.get("main", {}).get("humidity", 0),
                                "wind_speed": forecast.get("wind", {}).get("speed", 0),
                                "clouds": forecast.get("clouds", {}).get("all", 0),
                                "rain": forecast.get("rain", {}).get("3h", 0),
                                "date": forecast_time.isoformat(),
                                "forecast_time": forecast_time.isoformat(),
                                "location_coords": {"lat": lat, "lng": lng},
                                "hour": forecast_time.hour
                            }
                        else:
                            # Use forecast closest to noon (12:00) for better representation
                            existing_hour = forecast_by_date[date_key].get("hour", 12)
                            current_hour = forecast_time.hour
                            
                            # If this forecast is closer to noon, use it
                            if abs(current_hour - 12) < abs(existing_hour - 12):
                                forecast_by_date[date_key] = {
                                    "condition": forecast.get("weather", [{}])[0].get("main", "").lower(),
                                    "description": forecast.get("weather", [{}])[0].get("description", ""),
                                    "temperature": forecast.get("main", {}).get("temp", 0),
                                    "feels_like": forecast.get("main", {}).get("feels_like", 0),
                                    "humidity": forecast.get("main", {}).get("humidity", 0),
                                    "wind_speed": forecast.get("wind", {}).get("speed", 0),
                                    "clouds": forecast.get("clouds", {}).get("all", 0),
                                    "rain": forecast.get("rain", {}).get("3h", 0),
                                    "date": forecast_time.isoformat(),
                                    "forecast_time": forecast_time.isoformat(),
                                    "location_coords": {"lat": lat, "lng": lng},
                                    "hour": forecast_time.hour
                                }
                
                logger.info(f"Fetched weather forecast for {len(forecast_by_date)} dates")
                
                return {
                    "destination_coordinates": coordinates,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "forecast_by_date": forecast_by_date,
                    "cached_at": datetime.now().isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error fetching weather forecast: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                logger.error("Invalid OpenWeatherMap API key. Please check your OPENWEATHER_API_KEY environment variable.")
            elif e.response.status_code == 429:
                logger.error("OpenWeatherMap API rate limit exceeded. Please try again later.")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather forecast: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}", exc_info=True)
            return None
    
    async def _fetch_traffic_data(
        self,
        coordinates: Tuple[float, float],
        current_itinerary: Optional[Dict[str, Any]] = None,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Fetch traffic data with real-time congestion using Google Maps Directions API"""
        if not self.google_maps_key:
            logger.warning("Google Maps API key not configured")
            return {}
        
        if not current_itinerary:
            return {}
        
        try:
            from .google_maps_service import google_maps_service
            import time
            
            # Extract locations from itinerary
            locations = []
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            # Get locations from places or activities
            for item in places + activities:
                location = item.get("location") or item.get("address") or item.get("name")
                if location:
                    locations.append(location)
            
            if len(locations) < 2:
                return {}
            
            # Calculate departure time for traffic-aware routing
            departure_time = None
            if date:
                # If date is today or future, use it for traffic prediction
                now = datetime.now()
                if date >= now:
                    departure_time = int(date.timestamp())
                else:
                    departure_time = int(time.time())  # Current time
            
            # Get traffic data for each route segment with real-time traffic
            traffic_segments = []
            for i in range(len(locations) - 1):
                origin = locations[i]
                destination = locations[i + 1]
                
                directions = await google_maps_service.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving",
                    departure_time=departure_time
                )
                
                if directions:
                    # Extract traffic info with real-time data
                    duration = directions.get("duration", "")
                    duration_value = directions.get("duration_value", 0)
                    duration_in_traffic = directions.get("duration_in_traffic", "")
                    duration_in_traffic_value = directions.get("duration_in_traffic_value")
                    traffic_delay_seconds = directions.get("traffic_delay_seconds", 0)
                    has_traffic = directions.get("has_traffic", False)
                    distance = directions.get("distance", "")
                    
                    traffic_segments.append({
                        "origin": origin,
                        "destination": destination,
                        "duration": duration,
                        "duration_value": duration_value,
                        "duration_in_traffic": duration_in_traffic,
                        "duration_in_traffic_value": duration_in_traffic_value,
                        "traffic_delay_seconds": traffic_delay_seconds,
                        "has_traffic": has_traffic,
                        "distance": distance,
                        "route_summary": directions.get("summary", "")
                    })
            
            # Determine if there are significant delays
            significant_delays = [s for s in traffic_segments if s.get("traffic_delay_seconds", 0) > 300]  # > 5 minutes
            
            return {
                "segments": traffic_segments,
                "has_delays": len(significant_delays) > 0,
                "total_delay_minutes": sum(s.get("traffic_delay_seconds", 0) for s in traffic_segments) / 60,
                "affected_segments": significant_delays
            }
            
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            return {}
    
    async def _fetch_routes_data(
        self,
        current_itinerary: Optional[Dict[str, Any]] = None,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Fetch alternative routes and route updates using Google Maps Directions API"""
        if not self.google_maps_key:
            logger.warning("Google Maps API key not configured")
            return {}
        
        if not current_itinerary:
            return {}
        
        try:
            from .google_maps_service import google_maps_service
            import time
            
            # Extract locations from itinerary
            locations = []
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            for item in places + activities:
                location = item.get("location") or item.get("address") or item.get("name")
                if location:
                    locations.append(location)
            
            if len(locations) < 2:
                return {}
            
            # Get departure time
            departure_time = None
            if date:
                now = datetime.now()
                if date >= now:
                    departure_time = int(date.timestamp())
                else:
                    departure_time = int(time.time())
            
            # Get routes with alternatives for first significant segment
            if len(locations) >= 2:
                origin = locations[0]
                destination = locations[1]
                
                # Get alternative routes
                routes_data = await google_maps_service.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving",
                    departure_time=departure_time,
                    alternatives=True
                )
                
                if routes_data and routes_data.get("routes"):
                    primary_route = routes_data.get("primary_route", routes_data)
                    alternative_routes = routes_data.get("routes", [])
                    
                    # Filter out the primary route from alternatives
                    if len(alternative_routes) > 1:
                        alternative_routes = [r for r in alternative_routes[1:] if r != primary_route]
                    
                    return {
                        "origin": origin,
                        "destination": destination,
                        "primary_route": primary_route,
                        "alternative_routes": alternative_routes[:3],  # Limit to 3 alternatives
                        "has_alternatives": len(alternative_routes) > 0
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching routes data: {e}")
            return {}
    
    async def _fetch_places_status(
        self,
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch place status (closed, restrictions) using Google Places API"""
        if not self.google_maps_key:
            logger.warning("Google Maps API key not configured")
            return []
        
        if not current_itinerary:
            return []
        
        try:
            from .google_maps_service import google_maps_service
            
            # Extract places from itinerary
            places_status = []
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            # Collect place IDs or names to check
            places_to_check = []
            for item in places + activities:
                place_id = item.get("place_id")
                place_name = item.get("name") or item.get("activity") or item.get("place")
                
                if place_id:
                    places_to_check.append({"place_id": place_id, "name": place_name})
                elif place_name:
                    # Try to find place by name
                    places_to_check.append({"name": place_name, "place_id": None})
            
            # Check status for each place (limit to first 10 to avoid too many API calls)
            for place_info in places_to_check[:10]:
                place_id = place_info.get("place_id")
                place_name = place_info.get("name")
                
                if place_id:
                    # Fetch place details with business status
                    place_details = await google_maps_service.get_place_details(place_id)
                    
                    if place_details:
                        business_status = place_details.get("business_status", "OPERATIONAL")
                        is_open_now = place_details.get("is_open_now")
                        opening_hours = place_details.get("opening_hours", {})
                        weekday_text = place_details.get("weekday_text", [])
                        
                        # Check if place has issues
                        has_issue = False
                        issue_type = None
                        issue_description = ""
                        
                        if business_status == "CLOSED_PERMANENTLY":
                            has_issue = True
                            issue_type = "closed_permanently"
                            issue_description = "This place is permanently closed"
                        elif business_status == "CLOSED_TEMPORARILY":
                            has_issue = True
                            issue_type = "closed_temporarily"
                            issue_description = "This place is temporarily closed"
                        elif is_open_now is False:
                            has_issue = True
                            issue_type = "closed_now"
                            issue_description = "This place is currently closed"
                        
                        if has_issue:
                            places_status.append({
                                "place_id": place_id,
                                "name": place_details.get("name", place_name),
                                "address": place_details.get("formatted_address", ""),
                                "business_status": business_status,
                                "is_open_now": is_open_now,
                                "issue_type": issue_type,
                                "issue_description": issue_description,
                                "opening_hours": weekday_text,
                                "coordinates": place_details.get("coordinates")
                            })
            
            return places_status
            
        except Exception as e:
            logger.error(f"Error fetching places status: {e}")
            return []
    
    def _process_weather_adjustments(
        self,
        weather_data: Dict[str, Any],
        date: datetime,
        current_itinerary: Optional[Dict[str, Any]] = None,
        place_name: Optional[str] = None,
        coordinates: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """Process weather data and create adjustment suggestions for a specific location"""
        adjustments = []
        condition = weather_data.get("condition", "").lower()
        rain = weather_data.get("rain", 0)
        temperature = weather_data.get("temperature", 0)
        description = weather_data.get("description", "")
        
        # Build location context for the alert
        location_context = ""
        if place_name and place_name != "Destination":
            location_context = f" at {place_name}"
        
        # Check if weather affects outdoor activities for this specific location
        outdoor_conditions = ["clear", "clouds", "sunny"]
        adverse_conditions = ["rain", "thunderstorm", "snow", "drizzle"]
        
        # Find activities at this location
        outdoor_activities_at_location = []
        if current_itinerary and place_name and place_name != "Destination":
            places = current_itinerary.get("places", []) or []
            activities = current_itinerary.get("activities", []) or []
            
            # Match activities to this location by name or coordinates
            for item in places + activities:
                item_name = item.get("name") or item.get("activity") or item.get("place") or ""
                item_coords = item.get("coordinates")
                
                # Check if this item matches the location
                matches = False
                if item_name.lower() == place_name.lower():
                    matches = True
                elif coordinates and item_coords:
                    # Check if coordinates are close (within ~1km)
                    if isinstance(item_coords, dict):
                        item_lat = item_coords.get("lat")
                        item_lng = item_coords.get("lng")
                    elif isinstance(item_coords, (list, tuple)) and len(item_coords) >= 2:
                        item_lat, item_lng = item_coords[0], item_coords[1]
                    else:
                        item_lat = item_lng = None
                    
                    if item_lat and item_lng:
                        # Rough distance check (simplified - assumes ~111km per degree)
                        lat_diff = abs(item_lat - coordinates[0])
                        lng_diff = abs(item_lng - coordinates[1])
                        if lat_diff < 0.01 and lng_diff < 0.01:  # Roughly within 1km
                            matches = True
                
                if matches:
                    location_str = item.get("location") or ""
                    # Check if outdoor activity
                    outdoor_keywords = ["outdoor", "park", "beach", "hiking", "walking tour", 
                                       "market", "garden", "monument", "temple", "outdoor"]
                    if any(keyword in item_name.lower() or keyword in location_str.lower() 
                           for keyword in outdoor_keywords):
                        outdoor_activities_at_location.append(item_name or location_str)
        
        # Weather alerts for adverse conditions
        if condition in adverse_conditions or rain > 0:
            severity = "medium" if rain < 5 else "high"
            title = f"Weather Alert{location_context}: {description.title()} Expected"
            
            if outdoor_activities_at_location:
                description_text = f"{description.capitalize()} is forecasted{location_context}. "
                description_text += f"Outdoor activities may be affected: {', '.join(outdoor_activities_at_location[:3])}."
            else:
                description_text = f"{description.capitalize()} is forecasted{location_context}. "
                description_text += "Consider adjusting outdoor activities."
            
            adjustments.append({
                "id": f"weather_{hash(place_name or 'default') % 10000}_{date.strftime('%Y%m%d')}",
                "type": "weather",
                "severity": severity,
                "title": title,
                "description": description_text,
                "action": "Adjust Itinerary",
                "suggestions": [
                    "Move outdoor activities to indoor alternatives",
                    "Reschedule to a day with better weather",
                    "Add indoor attractions as backup plans"
                ],
                "weather_data": weather_data,
                "affected_activities": outdoor_activities_at_location,
                "place_name": place_name
            })
        
        # Temperature warnings - location-specific
        if temperature < 5:
            adjustments.append({
                "id": f"cold_{hash(place_name or 'default') % 10000}_{date.strftime('%Y%m%d')}",
                "type": "weather",
                "severity": "low",
                "title": f"Cold Weather Alert{location_context}",
                "description": f"Temperature is {temperature:.1f}°C{location_context}. Dress warmly and consider indoor activities.",
                "action": "View Recommendations",
                "suggestions": ["Wear warm clothing", "Prefer indoor activities"],
                "weather_data": weather_data,
                "place_name": place_name
            })
        elif temperature > 35:
            adjustments.append({
                "id": f"hot_{hash(place_name or 'default') % 10000}_{date.strftime('%Y%m%d')}",
                "type": "weather",
                "severity": "medium",
                "title": f"Hot Weather Alert{location_context}",
                "description": f"Temperature is {temperature:.1f}°C{location_context}. Stay hydrated and avoid outdoor activities during peak hours.",
                "action": "View Recommendations",
                "suggestions": ["Stay hydrated", "Schedule outdoor activities in early morning or evening"],
                "weather_data": weather_data,
                "place_name": place_name
            })
        
        return adjustments
    
    def _process_traffic_adjustments(
        self,
        traffic_data: Dict[str, Any],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process traffic data and create adjustment suggestions with real-time congestion"""
        adjustments = []
        affected_segments = traffic_data.get("affected_segments", [])
        total_delay_minutes = traffic_data.get("total_delay_minutes", 0)
        
        if not affected_segments:
            return adjustments
        
        # Process each segment with significant traffic
        for segment in affected_segments:
            origin = segment.get("origin", "origin")
            destination = segment.get("destination", "destination")
            duration = segment.get("duration", "")
            duration_in_traffic = segment.get("duration_in_traffic", "")
            traffic_delay_seconds = segment.get("traffic_delay_seconds", 0)
            traffic_delay_minutes = traffic_delay_seconds / 60
            
            # Determine severity
            if traffic_delay_minutes > 20:
                severity = "high"
            elif traffic_delay_minutes > 10:
                severity = "medium"
            else:
                severity = "low"
            
            adjustments.append({
                "id": f"traffic_{hash(origin + destination) % 10000}",
                "type": "traffic",
                "severity": severity,
                "title": f"Traffic Congestion: {int(traffic_delay_minutes)} min delay",
                "description": f"Heavy traffic detected on route from {origin} to {destination}. "
                             f"Expected travel time: {duration_in_traffic or duration} "
                             f"(additional {int(traffic_delay_minutes)} minutes due to traffic).",
                "action": "Adjust Itinerary",
                "suggestions": [
                    f"Leave {int(traffic_delay_minutes + 10)} minutes earlier to account for delays",
                    "Consider using alternative routes",
                    "Check real-time traffic updates before departure",
                    "Consider public transportation if available"
                ],
                "route_info": segment
            })
        
        return adjustments
    
    def _process_route_adjustments(
        self,
        routes_data: Dict[str, Any],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process route data and suggest alternative routes"""
        adjustments = []
        
        if not routes_data.get("has_alternatives"):
            return adjustments
        
        primary_route = routes_data.get("primary_route", {})
        alternative_routes = routes_data.get("alternative_routes", [])
        origin = routes_data.get("origin", "")
        destination = routes_data.get("destination", "")
        
        # Find faster alternatives
        primary_duration = primary_route.get("duration_value", 0)
        
        faster_routes = []
        for alt_route in alternative_routes:
            alt_duration = alt_route.get("duration_value", 0)
            if alt_duration > 0 and alt_duration < primary_duration * 0.9:  # At least 10% faster
                time_saved = (primary_duration - alt_duration) / 60  # minutes
                faster_routes.append({
                    "route": alt_route,
                    "time_saved_minutes": time_saved
                })
        
        if faster_routes:
            best_alternative = max(faster_routes, key=lambda x: x["time_saved_minutes"])
            route = best_alternative["route"]
            time_saved = int(best_alternative["time_saved_minutes"])
            
            adjustments.append({
                "id": f"route_{hash(origin + destination) % 10000}",
                "type": "route",
                "severity": "low",
                "title": f"Faster Route Available: Save {time_saved} minutes",
                "description": f"An alternative route from {origin} to {destination} can save {time_saved} minutes. "
                             f"New route: {route.get('summary', 'Alternative route')}. "
                             f"Travel time: {route.get('duration', 'N/A')} vs {primary_route.get('duration', 'N/A')}.",
                "action": "Adjust Itinerary",
                "suggestions": [
                    "Update itinerary to use the faster route",
                    "Adjust timing to match new route duration",
                    "Review route details before departure"
                ],
                "route_info": {
                    "origin": origin,
                    "destination": destination,
                    "current_route": primary_route,
                    "recommended_route": route,
                    "time_saved_minutes": time_saved
                }
            })
        
        return adjustments
    
    def _process_place_status_adjustments(
        self,
        places_status: List[Dict[str, Any]],
        current_itinerary: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process place status and create alerts for closed/restricted places"""
        adjustments = []
        
        for place in places_status:
            issue_type = place.get("issue_type", "")
            business_status = place.get("business_status", "")
            place_name = place.get("name", "Place")
            issue_description = place.get("issue_description", "")
            opening_hours = place.get("opening_hours", [])
            
            # Determine severity and title based on issue type
            if issue_type == "closed_permanently":
                severity = "high"
                title = f"Place Closed: {place_name} is Permanently Closed"
                action = "Adjust Itinerary"
                suggestions = [
                    "Remove this place from your itinerary",
                    "Find alternative places to visit",
                    "Update your schedule accordingly"
                ]
            elif issue_type == "closed_temporarily":
                severity = "high"
                title = f"Place Temporarily Closed: {place_name}"
                action = "Adjust Itinerary"
                suggestions = [
                    "Check reopening date if available",
                    "Find alternative places to visit",
                    "Reschedule visit for later date"
                ]
            elif issue_type == "closed_now":
                severity = "medium"
                title = f"Place Currently Closed: {place_name}"
                action = "Adjust Itinerary"
                suggestions = [
                    f"Check opening hours: {', '.join(opening_hours[:3]) if opening_hours else 'Check online'}",
                    "Adjust visit time to match opening hours",
                    "Consider visiting at a different time"
                ]
            else:
                continue  # Skip unknown issue types
            
            adjustments.append({
                "id": f"place_{place.get('place_id', hash(place_name) % 10000)}",
                "type": "alert",
                "severity": severity,
                "title": title,
                "description": f"{issue_description}. {place.get('address', '')}",
                "action": action,
                "suggestions": suggestions,
                "place_info": place
            })
        
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
