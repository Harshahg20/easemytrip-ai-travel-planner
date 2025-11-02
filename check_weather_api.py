#!/usr/bin/env python3
"""
Quick check script for Google Weather API status
"""
import httpx
import sys

API_KEY = "AIzaSyAmLDYoqjcmPDT3-BVV0kA6fjNpCfyoccg"
TEST_LOCATION = (40.7128, -74.0060)  # New York City

def check_api_status():
    """Check if Weather API is enabled and working"""
    
    print("=" * 60)
    print("Google Weather API Status Check")
    print("=" * 60)
    print()
    
    # Test current conditions endpoint
    url = "https://weather.googleapis.com/v1/currentConditions:lookup"
    params = {
        "key": API_KEY,
        "location.latitude": TEST_LOCATION[0],
        "location.longitude": TEST_LOCATION[1]
    }
    
    print(f"Testing: {url}")
    print(f"Location: New York City {TEST_LOCATION}")
    print()
    
    try:
        response = httpx.get(url, params=params, timeout=10.0)
        
        if response.status_code == 200:
            print("✅ SUCCESS! Weather API is working!")
            print()
            data = response.json()
            
            # Show some weather data
            if "currentConditions" in data:
                conditions = data["currentConditions"]
                temp = conditions.get("temperature", {})
                print(f"Current Weather:")
                print(f"  Temperature: {temp.get('value', 'N/A')}°{temp.get('unit', 'C').upper()}")
                print(f"  Condition: {conditions.get('weatherCondition', 'N/A')}")
                print()
            
            return True
            
        elif response.status_code == 404:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            
            print("❌ WEATHER API NOT ENABLED")
            print()
            print(f"Error: {error_message}")
            print()
            print("To enable the Weather API:")
            print()
            print("1. Visit: https://console.cloud.google.com/apis/library/weather.googleapis.com")
            print("2. Select project: gen-ai-hackathon-476317")
            print("3. Click 'ENABLE'")
            print("4. Wait 1-2 minutes for changes to propagate")
            print()
            return False
            
        elif response.status_code == 403:
            print("❌ API KEY ERROR")
            print()
            print("Your API key doesn't have permission to access Weather API.")
            print()
            print("To fix:")
            print("1. Visit: https://console.cloud.google.com/apis/credentials")
            print("2. Find your API key")
            print("3. Edit API restrictions")
            print("4. Add 'Weather API' to allowed APIs")
            print()
            return False
            
        else:
            print(f"❌ UNEXPECTED ERROR: HTTP {response.status_code}")
            print()
            print(f"Response: {response.text[:500]}")
            print()
            return False
            
    except httpx.RequestError as e:
        print(f"❌ NETWORK ERROR: {e}")
        print()
        print("Check your internet connection and try again.")
        print()
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        return False

if __name__ == "__main__":
    success = check_api_status()
    
    print("=" * 60)
    
    if success:
        print()
        print("🎉 Your Weather API is ready to use!")
        print()
        print("Next steps:")
        print("  - Run: python3 test_weather_api.py (for full testing)")
        print("  - Start using weather features in your application")
        print()
    else:
        print()
        print("⚠️  Weather API needs to be enabled.")
        print()
        print("Quick start:")
        print("  1. Run: ./enable_weather_api.sh")
        print("  2. Or follow instructions in: WEATHER_API_SETUP.md")
        print()
    
    print("=" * 60)
    
    sys.exit(0 if success else 1)

