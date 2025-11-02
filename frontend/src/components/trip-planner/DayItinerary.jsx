import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Clock,
  MapPin,
  DollarSign,
  Utensils,
  Camera,
  Home,
  Bus,
  BedDouble,
} from "lucide-react";
import { DayItinerarySkeleton } from "../ui/loading-skeletons";
import MapModal from "./MapModal";
import { tripService } from "../../services/api";
import { useItineraryTranslation } from "../../hooks/useTranslation";
import { useLanguage } from "../language/LanguageProvider";

const getCategoryIcon = (category) => {
  switch (category?.toLowerCase()) {
    case "food":
    case "dining":
      return Utensils;
    case "accommodation":
      return BedDouble;
    case "sightseeing":
    case "attraction":
      return Camera;
    case "transport":
      return Bus;
    default:
      return MapPin;
  }
};

export default function DayItinerary({
  dayData,
  isLoading = false,
  selectedDay = null,
}) {
  const [mapOpen, setMapOpen] = useState(false);
  const [mapPoint, setMapPoint] = useState(null);
  const { translateItinerary, isTranslating } = useItineraryTranslation();
  const { t, currentLanguage } = useLanguage();
  const [translatedDayData, setTranslatedDayData] = useState(dayData);

  // Translate dayData when it changes or language changes (fallback if server translation fails)
  useEffect(() => {
    if (dayData) {
      // If language is not English, try client-side translation as fallback
      if (currentLanguage !== "english") {
        translateItinerary(dayData).then((translated) => {
          setTranslatedDayData(translated);
        });
      } else {
        setTranslatedDayData(dayData);
      }
    } else {
      setTranslatedDayData(null);
    }
  }, [dayData, translateItinerary, currentLanguage]);

  const openDirections = async (item) => {
    try {
      let center = null;
      
      // First, try to get coordinates directly from the item
      const coords = item.coordinates || item.location_coordinates;
      if (
        coords &&
        typeof coords.lat === "number" &&
        typeof coords.lng === "number"
      ) {
        center = { lat: coords.lat, lng: coords.lng };
      } 
      // If coordinates are in array format [lng, lat] or [lat, lng]
      else if (Array.isArray(coords) && coords.length === 2) {
        // Google Maps format is typically [lat, lng]
        center = { lat: coords[0], lng: coords[1] };
      }
      // If no coordinates, try to geocode using location
      else if (item.location || item.activity || item.place || item.restaurant) {
        const params = new URLSearchParams(window.location.search);
        const tripId = params.get("trip_id");
        if (tripId) {
          // First try with full place name + location for better accuracy
          const placeName = item.activity || item.place || item.restaurant || item.name || "";
          const locationName = item.location || "";
          
          // Prioritize: "Place Name, Location" for better geocoding accuracy
          let geocodeQuery = "";
          if (placeName && locationName) {
            geocodeQuery = `${placeName}, ${locationName}`;
          } else if (placeName) {
            geocodeQuery = placeName;
          } else if (locationName) {
            geocodeQuery = locationName;
          }

          if (geocodeQuery) {
            try {
              console.log("Geocoding query:", geocodeQuery);
              const res = await tripService.geocodePlace(tripId, geocodeQuery);
              if (res && typeof res.lat === "number" && typeof res.lng === "number") {
                center = { lat: res.lat, lng: res.lng };
                console.log("Geocoded to:", center, "for:", geocodeQuery);
              }
            } catch (geocodeError) {
              console.error("Geocoding error:", geocodeError);
              // Fallback: try geocoding with just location
              if (locationName && locationName !== geocodeQuery) {
                try {
                  const res = await tripService.geocodePlace(tripId, locationName);
                  if (res && typeof res.lat === "number" && typeof res.lng === "number") {
                    center = { lat: res.lat, lng: res.lng };
                    console.log("Fallback geocoded to:", center, "for:", locationName);
                  }
                } catch (fallbackError) {
                  console.error("Fallback geocoding error:", fallbackError);
                }
              }
            }
          }
        }
      }
      
      if (center && typeof center.lat === "number" && typeof center.lng === "number") {
        const newTitle = item.activity || item.place || item.restaurant || item.name || "Location";
        const newCenter = { lat: center.lat, lng: center.lng };
        
        console.log("Setting map point:", {
          title: newTitle,
          center: newCenter,
          previousMapPoint: mapPoint
        });
        
        // Always create a new object to ensure React detects the change
        setMapPoint({
          center: newCenter,
          title: newTitle,
        });
        // Ensure modal is open
        if (!mapOpen) {
          setMapOpen(true);
        }
      } else {
        console.warn("Could not determine location for:", item);
        // Show user-friendly error message
        alert(`Unable to find location for "${item.activity || item.place || item.restaurant}". Please check the location name.`);
      }
    } catch (e) {
      console.error("Directions error", e);
      alert("Error opening map. Please try again.");
    }
  };
  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            <span>
              {t("loadingTrip")} {selectedDay ? `${t("days")} ${selectedDay}` : ""}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <DayItinerarySkeleton />
        </CardContent>
      </Card>
    );
  }

  // Use translated data or fallback to original
  const displayData = translatedDayData || dayData;

  if (!dayData || isTranslating) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-8 text-center">
          <div className="text-slate-500">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>
              {isTranslating
                ? t("loadingTrip")
                : selectedDay
                ? `${t("days")} ${selectedDay} ${t("loadingTrip")}`
                : t("selectDayPrompt")}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const allItems = [
    // Map place-based items to activity-like items for UI reuse
    ...(displayData.places || []).map((p) => ({
      time: undefined,
      activity: p.place || p.name || "Place",
      location: p.location,
      duration: undefined,
      cost: p.estimated_cost || p.cost || 0,
      description: p.description,
      category: "place",
      type: "activity",
      // Preserve coordinates for map functionality
      coordinates: p.coordinates || p.location_coordinates,
      location_coordinates: p.coordinates || p.location_coordinates,
    })),
    ...(displayData.activities || []).map((item) => ({
      ...item,
      type: "activity",
      // Ensure coordinates are preserved
      coordinates: item.coordinates || item.location_coordinates,
      location_coordinates: item.coordinates || item.location_coordinates,
    })),
    ...(displayData.meals || []).map((item) => ({
      ...item,
      type: "meal",
      activity: item.restaurant,
      location: item.location,
      // Ensure coordinates are preserved for meals
      coordinates: item.coordinates || item.location_coordinates,
      location_coordinates: item.coordinates || item.location_coordinates,
    })),
  ];

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader className="border-b border-slate-200">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-slate-500" />
            <span className="text-lg font-semibold text-slate-800">
              {t("days")} {displayData.day_number} -{" "}
              {new Date(displayData.date).toLocaleDateString(currentLanguage === "english" ? "en-US" : currentLanguage, {
                weekday: "long",
              })}
            </span>
          </div>
          <Badge
            variant="secondary"
            className="bg-slate-100 text-slate-700 font-semibold"
          >
            <DollarSign className="w-3 h-3 mr-1" />₹
            {(() => {
              const budget =
                typeof displayData.daily_budget === "number"
                  ? displayData.daily_budget
                  : 0;
              if (budget > 0) return budget.toFixed(0);
              const activitiesTotal = (displayData.activities || []).reduce(
                (sum, a) => sum + (a?.cost || 0),
                0
              );
              const mealsTotal = (displayData.meals || []).reduce(
                (sum, m) => sum + (m?.cost || 0),
                0
              );
              const accommodationTotal = displayData.accommodation?.cost || 0;
              const transportTotal = Array.isArray(displayData.transportation)
                ? (displayData.transportation || []).reduce(
                    (sum, t) => sum + (t?.cost || 0),
                    0
                  )
                : displayData.transportation_cost || 0;
              const total =
                activitiesTotal +
                mealsTotal +
                accommodationTotal +
                transportTotal;
              return total.toFixed(0);
            })()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-100">
          {allItems.map((item, index) => {
            const IconComponent =
              item.type === "meal" ? Utensils : getCategoryIcon(item.category);

            return (
              <div
                key={index}
                className="p-6 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center border border-slate-200 mt-1">
                    <IconComponent className="w-5 h-5 text-slate-600" />
                  </div>

                  <div className="flex-1">
                    <h4 className="font-semibold text-slate-800 mb-1">
                      {item.activity || item.restaurant}
                    </h4>

                    {item.description && (
                      <p className="text-slate-600 mb-2 text-sm leading-relaxed">
                        {item.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <MapPin className="w-4 h-4" />
                        <span>{item.location}</span>
                        {item.location && (
                          <button
                            type="button"
                            className="ml-2 text-blue-600 hover:underline"
                            onClick={() => openDirections(item)}
                          >
                            {t("viewOnMap")}
                          </button>
                        )}
                      </div>

                      {item.cost > 0 && (
                        <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                          <DollarSign className="w-4 h-4" />
                          <span>₹{item.cost.toFixed(0)}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 mt-3">
                      {item.category && item.type === "activity" && (
                        <Badge
                          variant="secondary"
                          className="bg-blue-50 text-blue-700"
                        >
                          {item.category}
                        </Badge>
                      )}
                      {item.type === "meal" && (
                        <Badge
                          variant="secondary"
                          className="bg-amber-50 text-amber-700"
                        >
                          {item.meal_type}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {displayData.accommodation && (
            <div className="p-6 bg-blue-50/50 border-t border-slate-200">
              <div className="flex items-start gap-4">
                <div className="text-center min-w-[60px] pt-1">
                  <div className="text-base font-bold text-blue-700">{t("night")}</div>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center border border-blue-200 mt-1">
                  <Home className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-800 mb-1">
                    {displayData.accommodation.name}
                  </h4>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                    <div className="flex items-center gap-1.5 text-slate-500">
                      <MapPin className="w-4 h-4" />
                      <span>{displayData.accommodation.location}</span>
                      {displayData.accommodation.location && (
                        <button
                          type="button"
                          className="ml-2 text-blue-600 hover:underline"
                          onClick={() => openDirections({
                            activity: displayData.accommodation.name,
                            location: displayData.accommodation.location,
                            coordinates: displayData.accommodation.coordinates || displayData.accommodation.location_coordinates,
                            location_coordinates: displayData.accommodation.coordinates || displayData.accommodation.location_coordinates,
                          })}
                        >
                          {t("viewOnMap")}
                        </button>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                      <DollarSign className="w-4 h-4" />
                      <span>
                        {displayData.accommodation.cost &&
                        displayData.accommodation.cost > 0
                          ? `₹${displayData.accommodation.cost.toFixed(0)}`
                          : t("estimatedCost")}
                      </span>
                    </div>
                  </div>
                  <Badge
                    variant="secondary"
                    className="mt-3 bg-blue-100 text-blue-700"
                  >
                    {displayData.accommodation.type}
                  </Badge>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
      {mapOpen && mapPoint && (
        <MapModal
          open={mapOpen}
          onOpenChange={setMapOpen}
          center={mapPoint.center}
          title={mapPoint.title}
        />
      )}
    </Card>
  );
}
