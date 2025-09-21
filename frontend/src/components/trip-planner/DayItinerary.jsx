import React from "react";
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

export default function DayItinerary({ dayData }) {
  if (!dayData) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-8 text-center">
          <div className="text-slate-500">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Select a day to view the itinerary</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const allItems = [
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
  ].sort((a, b) => {
    const timeA = a.time || "00:00";
    const timeB = b.time || "00:00";
    return timeA.localeCompare(timeB);
  });

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
            {dayData.daily_budget?.toFixed(0) || 0}
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
                  <div className="text-center min-w-[60px] pt-1">
                    <div className="text-base font-bold text-slate-700">
                      {item.time || "--:--"}
                    </div>
                    {item.duration && (
                      <div className="text-xs text-slate-500 mt-1">
                        {item.duration}
                      </div>
                    )}
                  </div>

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
                        ₹{dayData.accommodation.cost?.toFixed(0) || 0}
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
    </Card>
  );
}
