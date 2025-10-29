import React, { useEffect, useRef, useState } from "react";
import { Wrapper, Status } from "@googlemaps/react-wrapper";
import { useLanguage } from "../language/LanguageProvider";

// Google Maps API key - should be in environment variables
const GOOGLE_MAPS_API_KEY =
  process.env.REACT_APP_GOOGLE_MAPS_API_KEY ||
  "AIzaSyAmLDYoqjcmPDT3-BVV0kA6fjNpCfyoccg";

const render = (status) => {
  switch (status) {
    case Status.LOADING:
      return (
        <div className="flex items-center justify-center h-full">
          Loading map...
        </div>
      );
    case Status.FAILURE:
      return (
        <div className="flex items-center justify-center h-full text-red-500">
          Error loading map
        </div>
      );
    default:
      return null;
  }
};

function MapComponent({ dayData, markers }) {
  const ref = useRef(null);
  const [map, setMap] = useState(null);

  useEffect(() => {
    if (ref.current && !map) {
      const mapInstance = new window.google.maps.Map(ref.current, {
        center:
          markers.length > 0
            ? {
                lat: markers[0].coordinates.lat,
                lng: markers[0].coordinates.lng,
              }
            : { lat: 15.4909, lng: 73.8278 }, // Default to Goa
        zoom: 12,
        mapTypeId: window.google.maps.MapTypeId.ROADMAP,
        styles: [
          {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "on" }],
          },
        ],
      });
      setMap(mapInstance);
    }
  }, [ref, map, markers]);

  useEffect(() => {
    if (map && markers.length > 0) {
      // Clear existing markers
      const existingMarkers = map.markers || [];
      existingMarkers.forEach((marker) => marker.setMap(null));

      // Create new markers
      const newMarkers = markers.map((marker, index) => {
        const googleMarker = new window.google.maps.Marker({
          position: {
            lat: marker.coordinates.lat,
            lng: marker.coordinates.lng,
          },
          map: map,
          title: marker.name || marker.activity || marker.restaurant,
          icon: getMarkerIcon(marker.type),
          animation: window.google.maps.Animation.DROP,
        });

        // Create info window
        const infoWindow = new window.google.maps.InfoWindow({
          content: createInfoWindowContent(marker),
        });

        // Add click listener
        googleMarker.addListener("click", () => {
          infoWindow.open(map, googleMarker);
        });

        return googleMarker;
      });

      // Store markers on map instance
      map.markers = newMarkers;

      // Fit bounds to show all markers
      if (markers.length > 1) {
        const bounds = new window.google.maps.LatLngBounds();
        markers.forEach((marker) => {
          bounds.extend({
            lat: marker.coordinates.lat,
            lng: marker.coordinates.lng,
          });
        });
        map.fitBounds(bounds);
      }
    }
  }, [map, markers]);

  return <div ref={ref} className="h-full w-full rounded-lg" />;
}

function getMarkerIcon(type) {
  const iconColors = {
    activities: "#4285F4", // Blue
    meals: "#EA4335", // Red
    accommodation: "#34A853", // Green
  };

  return {
    path: window.google.maps.SymbolPath.CIRCLE,
    scale: 8,
    fillColor: iconColors[type] || "#4285F4",
    fillOpacity: 1,
    strokeColor: "#FFFFFF",
    strokeWeight: 2,
  };
}

function createInfoWindowContent(marker) {
  return `
    <div class="p-2">
      <h3 class="font-bold text-sm">${
        marker.name || marker.activity || marker.restaurant
      }</h3>
      <p class="text-xs text-gray-600">${marker.location || ""}</p>
      <p class="text-xs text-blue-600 font-semibold">${marker.type}</p>
      ${
        marker.description
          ? `<p class="text-xs mt-1">${marker.description}</p>`
          : ""
      }
      ${
        marker.cost
          ? `<p class="text-xs text-green-600 font-semibold">₹${marker.cost}</p>`
          : ""
      }
    </div>
  `;
}

export default function InteractiveMap({ dayData }) {
  const { t } = useLanguage();
  const [markers, setMarkers] = useState([]);

  // Helper function to get fallback coordinates for common locations
  const getFallbackCoordinates = (location) => {
    const locationMap = {
      "Downtown Area, Goa": { lat: 15.4909, lng: 73.8278 },
      "Panaji, Goa": { lat: 15.4909, lng: 73.8278 },
      "Historic Quarter, Goa": { lat: 15.4909, lng: 73.8278 },
      "City Center, Goa": { lat: 15.4909, lng: 73.8278 },
      "Old Town, Goa": { lat: 15.4909, lng: 73.8278 },
      "Cultural District, Goa": { lat: 15.4909, lng: 73.8278 },
      "Heritage Zone, Goa": { lat: 15.4909, lng: 73.8278 },
      "Beachfront, Goa": { lat: 15.4909, lng: 73.8278 },
      "Coastal Area, Goa": { lat: 15.4909, lng: 73.8278 },
      "Marina District, Goa": { lat: 15.4909, lng: 73.8278 },
      "Mountain Region, Goa": { lat: 15.4909, lng: 73.8278 },
      "Hill Station, Goa": { lat: 15.4909, lng: 73.8278 },
      "Nature Reserve, Goa": { lat: 15.4909, lng: 73.8278 },
      Goa: { lat: 15.4909, lng: 73.8278 },
      Mumbai: { lat: 19.076, lng: 72.8777 },
      Delhi: { lat: 28.6139, lng: 77.209 },
      Bangalore: { lat: 12.9716, lng: 77.5946 },
      Chennai: { lat: 13.0827, lng: 80.2707 },
      Kolkata: { lat: 22.5726, lng: 88.3639 },
      Hyderabad: { lat: 17.385, lng: 78.4867 },
      Pune: { lat: 18.5204, lng: 73.8567 },
      Jaipur: { lat: 26.9124, lng: 75.7873 },
      Kochi: { lat: 9.9312, lng: 76.2673 },
      Ahmedabad: { lat: 23.0225, lng: 72.5714 },
      Surat: { lat: 21.1702, lng: 72.8311 },
      Vadodara: { lat: 22.3072, lng: 73.1812 },
    };

    // Try exact match first
    if (locationMap[location]) {
      return locationMap[location];
    }

    // Try partial match
    for (const [key, coords] of Object.entries(locationMap)) {
      if (
        location.toLowerCase().includes(key.toLowerCase()) ||
        key.toLowerCase().includes(location.toLowerCase())
      ) {
        return coords;
      }
    }

    // Default to Goa coordinates
    return { lat: 15.4909, lng: 73.8278 };
  };

  useEffect(() => {
    if (!dayData) {
      setMarkers([]);
      return;
    }

    const allMarkers = [];

    // Process activities
    if (dayData.activities) {
      dayData.activities.forEach((item) => {
        let coordinates = item.coordinates;
        if (!coordinates && item.location) {
          coordinates = getFallbackCoordinates(item.location);
        }
        if (coordinates) {
          allMarkers.push({
            ...item,
            coordinates,
            type: "activities",
            name: item.activity,
            description: item.description,
            cost: item.cost,
          });
        }
      });
    }

    // Process meals
    if (dayData.meals) {
      dayData.meals.forEach((item) => {
        let coordinates = item.coordinates;
        if (!coordinates && item.location) {
          coordinates = getFallbackCoordinates(item.location);
        }
        if (coordinates) {
          allMarkers.push({
            ...item,
            coordinates,
            type: "meals",
            name: item.restaurant,
            description: item.cuisine,
            cost: item.cost,
          });
        }
      });
    }

    // Process accommodation
    if (dayData.accommodation) {
      let coordinates = dayData.accommodation.coordinates;
      if (!coordinates && dayData.accommodation.location) {
        coordinates = getFallbackCoordinates(dayData.accommodation.location);
      }
      if (coordinates) {
        allMarkers.push({
          ...dayData.accommodation,
          coordinates,
          type: "accommodation",
          name: dayData.accommodation.name,
          description: dayData.accommodation.type,
          cost: dayData.accommodation.cost,
        });
      }
    }

    setMarkers(allMarkers);
  }, [dayData]);

  if (!dayData || markers.length === 0) {
    return (
      <div className="aspect-video bg-slate-100 rounded-lg flex items-center justify-center">
        <div className="text-center text-slate-500">
          <p>{t("selectDayPrompt")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="aspect-video h-[500px] w-full rounded-lg overflow-hidden">
      <Wrapper apiKey={GOOGLE_MAPS_API_KEY} render={render}>
        <MapComponent dayData={dayData} markers={markers} />
      </Wrapper>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg">
        <div className="text-xs font-semibold mb-2">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-xs">Activities</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-xs">Meals</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-xs">Accommodation</span>
          </div>
        </div>
      </div>
    </div>
  );
}
