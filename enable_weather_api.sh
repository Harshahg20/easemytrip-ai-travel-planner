#!/bin/bash

# Script to help enable Google Weather API
# Run this script for step-by-step instructions

echo "=================================================="
echo "Google Weather API Setup Assistant"
echo "=================================================="
echo ""
echo "This script will guide you through enabling the Google Weather API."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}STEP 1: Enable the Weather API${NC}"
echo ""
echo "1. Open this link in your browser:"
echo -e "${GREEN}https://console.cloud.google.com/apis/library/weather.googleapis.com${NC}"
echo ""
echo "2. Make sure your project 'gen-ai-hackathon-476317' is selected"
echo ""
echo "3. Click the blue 'ENABLE' button"
echo ""
read -p "Press Enter when you have enabled the API..."

echo ""
echo -e "${YELLOW}STEP 2: Verify API Key Permissions${NC}"
echo ""
echo "1. Open this link:"
echo -e "${GREEN}https://console.cloud.google.com/apis/credentials${NC}"
echo ""
echo "2. Find your API key (ends with: ...yoccg)"
echo ""
echo "3. Click on it to edit"
echo ""
echo "4. Under 'API restrictions':"
echo "   - Select 'Restrict key'"
echo "   - Ensure 'Weather API' is in the allowed list"
echo ""
read -p "Press Enter when you have verified the API key..."

echo ""
echo -e "${YELLOW}STEP 3: Wait for Propagation${NC}"
echo ""
echo "Changes may take 1-2 minutes to propagate..."
for i in {30..1}; do
    echo -ne "Waiting $i seconds...\r"
    sleep 1
done
echo ""

echo ""
echo -e "${YELLOW}STEP 4: Test the Weather API${NC}"
echo ""
echo "Running test script..."
echo ""

cd /Users/harshahg/google_ai_ease_my_trip_ai
python3 test_weather_api.py

echo ""
echo "=================================================="
echo ""

# Check if test was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Setup Complete!${NC}"
    echo ""
    echo "If you still see fallback data or 404 errors:"
    echo "  1. Wait a few more minutes for API to fully enable"
    echo "  2. Check that billing is enabled in Google Cloud"
    echo "  3. Verify API key restrictions"
    echo ""
    echo "Otherwise, your Weather API is working!"
else
    echo -e "${RED}❌ Test failed. Please check the error messages above.${NC}"
fi

echo ""
echo "For more information, see: WEATHER_API_SETUP.md"
echo "=================================================="

