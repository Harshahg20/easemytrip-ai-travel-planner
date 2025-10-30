import React, { useState } from "react";
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

  const openDirections = async (item) => {
    try {
      let center = null;
      const coords = item.coordinates || item.location_coordinates;
      if (
        coords &&
        typeof coords.lat === "number" &&
        typeof coords.lng === "number"
      ) {
        center = { lat: coords.lat, lng: coords.lng };
      } else if (item.location) {
        const params = new URLSearchParams(window.location.search);
        const tripId = params.get("trip_id");
        if (tripId) {
          const res = await tripService.geocodePlace(tripId, item.location);
          if (res && typeof res.lat === "number") center = res;
        }
      }
      if (center) {
        setMapPoint({
          center,
          title: item.activity || item.place || item.restaurant || "Location",
        });
        setMapOpen(true);
      }
    } catch (e) {
      console.error("Directions error", e);
    }
  };
  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            <span>Loading Day {selectedDay || ""} Itinerary...</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <DayItinerarySkeleton />
        </CardContent>
      </Card>
    );
  }

  if (!dayData) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-8 text-center">
          <div className="text-slate-500">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>
              {selectedDay
                ? `Day ${selectedDay} is loading...`
                : "Select a day to view the itinerary"}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const allItems = [
    // Map place-based items to activity-like items for UI reuse
    ...(dayData.places || []).map((p) => ({
      time: undefined,
      activity: p.place || p.name || "Place",
      location: p.location,
      duration: undefined,
      cost: p.estimated_cost || p.cost || 0,
      description: p.description,
      category: "place",
      type: "activity",
    })),
    ...(dayData.activities || []).map((item) => ({
      ...item,
      type: "activity",
    })),
    ...(dayData.meals || []).map((item) => ({
      ...item,
      type: "meal",
      activity: item.restaurant,
      location: item.location,
    })),
  ];

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader className="border-b border-slate-200">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-slate-500" />
            <span className="text-lg font-semibold text-slate-800">
              Day {dayData.day_number} -{" "}
              {new Date(dayData.date).toLocaleDateString("en-US", {
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
                typeof dayData.daily_budget === "number"
                  ? dayData.daily_budget
                  : 0;
              if (budget > 0) return budget.toFixed(0);
              const activitiesTotal = (dayData.activities || []).reduce(
                (sum, a) => sum + (a?.cost || 0),
                0
              );
              const mealsTotal = (dayData.meals || []).reduce(
                (sum, m) => sum + (m?.cost || 0),
                0
              );
              const accommodationTotal = dayData.accommodation?.cost || 0;
              const transportTotal = Array.isArray(dayData.transportation)
                ? (dayData.transportation || []).reduce(
                    (sum, t) => sum + (t?.cost || 0),
                    0
                  )
                : dayData.transportation_cost || 0;
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
                            Directions
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

          {dayData.accommodation && (
            <div className="p-6 bg-blue-50/50 border-t border-slate-200">
              <div className="flex items-start gap-4">
                <div className="text-center min-w-[60px] pt-1">
                  <div className="text-base font-bold text-blue-700">Night</div>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center border border-blue-200 mt-1">
                  <Home className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-800 mb-1">
                    {dayData.accommodation.name}
                  </h4>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                    <div className="flex items-center gap-1.5 text-slate-500">
                      <MapPin className="w-4 h-4" />
                      <span>{dayData.accommodation.location}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-emerald-600 font-medium">
                      <DollarSign className="w-4 h-4" />
                      <span>
                        {dayData.accommodation.cost &&
                        dayData.accommodation.cost > 0
                          ? `₹${dayData.accommodation.cost.toFixed(0)}`
                          : "Price on request"}
                      </span>
                    </div>
                  </div>
                  <Badge
                    variant="secondary"
                    className="mt-3 bg-blue-100 text-blue-700"
                  >
                    {dayData.accommodation.type}
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
