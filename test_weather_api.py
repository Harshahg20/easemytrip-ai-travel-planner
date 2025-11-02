"""
Test script for Google Weather API integration
Tests both current weather and forecast functionality
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend/app to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set environment variables before importing config
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-weather-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "AIzaSyAmLDYoqjcmPDT3-BVV0kA6fjNpCfyoccg")

from app.services.google_maps_service import google_maps_service
from datetime import datetime, timedelta


async def test_google_weather_api():
    """Test Google Weather API integration"""
    
    print("=" * 60)
    print("Google Weather API Test")
    print("=" * 60)
    
    # Test coordinates (New York City)
    test_location = (40.7128, -74.0060)
    location_name = "New York City"
    
    print(f"\n📍 Testing weather for: {location_name}")
    print(f"   Coordinates: {test_location}")
    
    # Test 1: Current Weather
    print("\n" + "-" * 60)
    print("TEST 1: Current Weather")
    print("-" * 60)
    try:
        current_weather = await google_maps_service.get_current_weather(test_location)
        
        if "error" in current_weather:
            print(f"⚠️  Weather API returned fallback data: {current_weather.get('error')}")
        
        print("\n✅ Current Weather Data:")
        print(f"   Timestamp: {current_weather.get('timestamp', 'N/A')}")
        print(f"   Condition: {current_weather.get('condition', 'N/A')}")
        print(f"   Description: {current_weather.get('description', 'N/A')}")
        
        temp = current_weather.get('temperature', {})
        print(f"   Temperature: {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
        print(f"   Feels Like: {current_weather.get('feels_like', 'N/A')}°")
        print(f"   Humidity: {current_weather.get('humidity', 'N/A')}%")
        
        wind = current_weather.get('wind', {})
        print(f"   Wind Speed: {wind.get('speed', 'N/A')} {wind.get('unit', 'km/h')}")
        print(f"   Wind Direction: {wind.get('direction', 'N/A')}°")
        
        print(f"   Pressure: {current_weather.get('pressure', 'N/A')} hPa")
        print(f"   Visibility: {current_weather.get('visibility', 'N/A')} km")
        print(f"   UV Index: {current_weather.get('uv_index', 'N/A')}")
        print(f"   Cloud Cover: {current_weather.get('cloud_cover', 'N/A')}%")
        print(f"   Precipitation: {current_weather.get('precipitation', 'N/A')} mm")
        
    except Exception as e:
        print(f"❌ Error fetching current weather: {e}")
    
    # Test 2: Weather Forecast (5 days)
    print("\n" + "-" * 60)
    print("TEST 2: 5-Day Weather Forecast")
    print("-" * 60)
    try:
        forecast = await google_maps_service.get_weather_forecast(test_location, days=5)
        
        if "error" in forecast:
            print(f"⚠️  Forecast API returned fallback data: {forecast.get('error')}")
        
        forecasts = forecast.get('forecasts', [])
        print(f"\n✅ Retrieved {len(forecasts)} day(s) of forecast:")
        
        for idx, day in enumerate(forecasts, 1):
            print(f"\n   Day {idx} - {day.get('date', 'N/A')}:")
            print(f"      Condition: {day.get('condition', 'N/A')}")
            print(f"      Description: {day.get('description', 'N/A')}")
            
            temp = day.get('temperature', {})
            print(f"      High: {temp.get('high', 'N/A')}° / Low: {temp.get('low', 'N/A')}°")
            print(f"      Precipitation: {day.get('precipitation_probability', 'N/A')}% chance")
            print(f"      Humidity: {day.get('humidity', 'N/A')}%")
            print(f"      Wind Speed: {day.get('wind_speed', 'N/A')} km/h")
            print(f"      UV Index: {day.get('uv_index', 'N/A')}")
            print(f"      Sunrise: {day.get('sunrise', 'N/A')} / Sunset: {day.get('sunset', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error fetching forecast: {e}")
    
    # Test 3: Hourly Forecast (24 hours)
    print("\n" + "-" * 60)
    print("TEST 3: 24-Hour Forecast")
    print("-" * 60)
    try:
        hourly = await google_maps_service.get_hourly_weather(test_location, hours=24)
        
        if "error" in hourly:
            print(f"⚠️  Hourly API returned fallback data: {hourly.get('error')}")
        
        hourly_forecasts = hourly.get('forecasts', [])
        print(f"\n✅ Retrieved {len(hourly_forecasts)} hour(s) of forecast")
        
        # Show first 6 hours only for brevity
        print("\n   First 6 hours:")
        for idx, hour in enumerate(hourly_forecasts[:6], 1):
            temp = hour.get('temperature', {})
            print(f"   {hour.get('time', 'N/A')}: {hour.get('condition', 'N/A')}, "
                  f"{temp.get('value', 'N/A')}°, "
                  f"Rain: {hour.get('precipitation_probability', 'N/A')}%")
        
    except Exception as e:
        print(f"❌ Error fetching hourly forecast: {e}")
    
    # Test 4: Additional location tests
    print("\n" + "-" * 60)
    print("TEST 4: Other Locations")
    print("-" * 60)
    
    # Test Tokyo
    tokyo_location = (35.6762, 139.6503)
    print("\n📍 Testing Tokyo, Japan:")
    try:
        tokyo_weather = await google_maps_service.get_current_weather(tokyo_location)
        temp = tokyo_weather.get('temperature', {})
        print(f"   {tokyo_weather.get('condition', 'N/A')}, {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test London
    london_location = (51.5074, -0.1278)
    print("\n📍 Testing London, UK:")
    try:
        london_weather = await google_maps_service.get_current_weather(london_location)
        temp = london_weather.get('temperature', {})
        print(f"   {london_weather.get('condition', 'N/A')}, {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Mumbai
    mumbai_location = (19.0760, 72.8777)
    print("\n📍 Testing Mumbai, India:")
    try:
        mumbai_weather = await google_maps_service.get_current_weather(mumbai_location)
        temp = mumbai_weather.get('temperature', {})
        print(f"   {mumbai_weather.get('condition', 'N/A')}, {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


async def main():
    """Main test function"""
    await test_google_weather_api()


if __name__ == "__main__":
    asyncio.run(main())

