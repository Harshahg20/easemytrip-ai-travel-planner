import React from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Calendar, DollarSign, Loader2, Clock } from "lucide-react";
import { DaySelectorSkeleton } from "../ui/loading-skeletons";

export default function DaySelector({
  dailyItineraries,
  selectedDay,
  onSelectDay,
  loadingDays = new Set(),
  loadedDays = new Set(),
  trip = null,
}) {
  // Calculate total trip duration from trip data
  const tripDuration = trip
    ? (() => {
        const startDate = new Date(trip.start_date);
        const endDate = new Date(trip.end_date);
        return Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
      })()
    : dailyItineraries.length;

  if (tripDuration === 0) {
    return null;
  }

  // Show skeleton if no data is loaded yet
  if (loadedDays.size === 0 && loadingDays.size === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4 border border-slate-200">
        <div className="flex items-center gap-2 mb-4 px-2">
          <Calendar className="w-5 h-5 text-slate-500" />
          <h3 className="text-lg font-semibold text-slate-800">
            Daily Itinerary
          </h3>
        </div>
        <DaySelectorSkeleton count={Math.min(tripDuration, 5)} />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 border border-slate-200">
      <div className="flex items-center gap-2 mb-4 px-2">
        <Calendar className="w-5 h-5 text-slate-500" />
        <h3 className="text-lg font-semibold text-slate-800">
          Daily Itinerary
        </h3>
      </div>

      <div className="overflow-x-auto">
        <div className="flex gap-3 pb-2">
          {Array.from({ length: tripDuration }, (_, index) => {
            const dayNumber = index + 1;
            const day = dailyItineraries[index];
            // Use the daily_budget from API instead of calculating
            const computeFallbackBudget = (day) => {
              if (!day) return 0;
              const activitiesTotal = (day.activities || []).reduce(
                (sum, a) => sum + (a?.cost || 0),
                0
              );
              const mealsTotal = (day.meals || []).reduce(
                (sum, m) => sum + (m?.cost || 0),
                0
              );
              const accommodationTotal = day.accommodation?.cost || 0;
              const transportTotal = Array.isArray(day.transportation)
                ? (day.transportation || []).reduce(
                    (sum, t) => sum + (t?.cost || 0),
                    0
                  )
                : day.transportation_cost || 0;
              return activitiesTotal + mealsTotal + accommodationTotal + transportTotal;
            };
            const dayBudgetRaw = typeof day?.daily_budget === "number" ? day.daily_budget : 0;
            const dayBudget = dayBudgetRaw > 0 ? dayBudgetRaw : computeFallbackBudget(day);
            const isLoading = loadingDays.has(dayNumber);
            const isLoaded = loadedDays.has(dayNumber);
            const hasData = day && day.activities && day.activities.length > 0;

            return (
              <Button
                key={dayNumber}
                variant={selectedDay === dayNumber ? "default" : "outline"}
                onClick={() => onSelectDay(dayNumber)}
                disabled={isLoading}
                className={`min-w-[140px] h-auto p-4 flex flex-col items-start gap-2 rounded-lg transition-all duration-300 ${
                  selectedDay === dayNumber
                    ? "bg-slate-800 text-white border-slate-800"
                    : "border-slate-200 hover:bg-slate-100 hover:border-slate-300"
                } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="font-semibold text-base flex items-center justify-between w-full">
                  <span>Day {dayNumber}</span>
                  {isLoading && (
                    <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
                  )}
                </div>
                <div
                  className={`text-xs ${
                    selectedDay === dayNumber ? "opacity-80" : "text-slate-500"
                  }`}
                >
                  {day?.date
                    ? new Date(day.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    : trip?.start_date
                    ? new Date(
                        new Date(trip.start_date).getTime() +
                          (dayNumber - 1) * 24 * 60 * 60 * 1000
                      ).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    : "TBD"}
                </div>
                {hasData && (
                  <Badge
                    variant="secondary"
                    className={`text-xs font-medium ${
                      selectedDay === dayNumber
                        ? "bg-white/20 text-white"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    <DollarSign className="w-3 h-3 mr-1" />₹
                    {Number(dayBudget || 0).toFixed(0)}
                  </Badge>
                )}
                {!hasData && !isLoading && (
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    <span>Click to load</span>
                  </div>
                )}
                {isLoading && (
                  <div className="flex items-center gap-1 text-xs text-blue-500">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Loading...</span>
                  </div>
                )}
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
