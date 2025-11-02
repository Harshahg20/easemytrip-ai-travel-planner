#!/usr/bin/env python3
"""
Simple demo of working Google Weather API integration
Shows real-time weather for multiple cities
"""
import asyncio
import sys
import os
from pathlib import Path

# Setup path and environment
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

os.environ.setdefault("SECRET_KEY", "demo-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "AIzaSyAmLDYoqjcmPDT3-BVV0kA6fjNpCfyoccg")

from app.services.google_maps_service import google_maps_service


async def show_weather_for_city(city_name: str, coordinates: tuple):
    """Display current weather for a city"""
    print(f"\n{'='*60}")
    print(f"📍 {city_name}")
    print(f"{'='*60}")
    
    try:
        weather = await google_maps_service.get_current_weather(coordinates)
        
        # Check if we got real data or fallback
        is_fallback = "error" in weather
        
        temp = weather.get('temperature', {})
        wind = weather.get('wind', {})
        
        if is_fallback:
            print("⚠️  Using fallback data (API unavailable for this location)")
            print()
        
        print(f"🌡️  Temperature:     {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
        print(f"🤔 Feels Like:      {weather.get('feels_like', 'N/A')}°")
        print(f"☁️  Condition:       {weather.get('condition', 'N/A').title()}")
        
        if weather.get('description'):
            print(f"📝 Description:     {weather.get('description', 'N/A')}")
        
        print(f"💧 Humidity:        {weather.get('humidity', 'N/A')}%")
        print(f"💨 Wind Speed:      {wind.get('speed', 'N/A')} {wind.get('unit', 'km/h')}")
        print(f"🧭 Wind Direction:  {wind.get('direction', 'N/A')}°")
        print(f"📊 Pressure:        {weather.get('pressure', 'N/A')} hPa")
        print(f"👁️  Visibility:      {weather.get('visibility', 'N/A')} km")
        print(f"☀️  UV Index:        {weather.get('uv_index', 'N/A')}")
        print(f"☁️  Cloud Cover:     {weather.get('cloud_cover', 'N/A')}%")
        print(f"🌧️  Precipitation:   {weather.get('precipitation', 'N/A')} mm")
        
        # Generate suggestions
        suggestions = generate_suggestions(weather)
        if suggestions:
            print(f"\n💡 Suggestions:")
            for suggestion in suggestions[:3]:  # Show top 3
                print(f"   • {suggestion}")
        
    except Exception as e:
        print(f"❌ Error fetching weather: {e}")


def generate_suggestions(weather_data):
    """Generate weather suggestions"""
    suggestions = []
    temp = weather_data.get('temperature', {}).get('value', 0)
    uv = weather_data.get('uv_index', 0)
    precipitation = weather_data.get('precipitation', 0)
    
    if precipitation > 0:
        suggestions.append("Bring an umbrella ☔")
    if temp < 10:
        suggestions.append("Dress warmly 🧥")
    elif temp > 30:
        suggestions.append("Stay hydrated 💧")
    if uv >= 6:
        suggestions.append("Use sunscreen 🧴")
    
    return suggestions


async def main():
    """Main demo function"""
    print("\n" + "="*60)
    print("🌤️  Google Weather API Demo - Real-time Weather Data")
    print("="*60)
    print("\nFetching current weather for major cities...")
    
    # Test cities
    cities = [
        ("New York, USA", (40.7128, -74.0060)),
        ("London, UK", (51.5074, -0.1278)),
        ("Tokyo, Japan", (35.6762, 139.6503)),
        ("Mumbai, India", (19.0760, 72.8777)),
        ("Paris, France", (48.8566, 2.3522)),
    ]
    
    for city_name, coords in cities:
        await show_weather_for_city(city_name, coords)
        await asyncio.sleep(0.5)  # Small delay between requests
    
    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print("="*60)
    print()
    print("📝 Notes:")
    print("   • Current weather data is live from Google Weather API")
    print("   • Some locations may show fallback data if not supported")
    print("   • Forecast data (daily/hourly) uses fallback until available")
    print()
    print("📚 For more information:")
    print("   • See: WEATHER_API_STATUS.md")
    print("   • Run: python3 check_weather_api.py (quick status check)")
    print("   • Run: python3 test_weather_api.py (full test suite)")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)

