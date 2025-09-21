import React from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Calendar, DollarSign } from "lucide-react";

export default function DaySelector({
  dailyItineraries,
  selectedDay,
  onSelectDay,
}) {
  if (!dailyItineraries || dailyItineraries.length === 0) {
    return null;
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
          {dailyItineraries.map((day) => {
            const dayBudget =
              (day.activities || []).reduce(
                (sum, activity) => sum + (activity.cost || 0),
                0
              ) +
              (day.meals || []).reduce(
                (sum, meal) => sum + (meal.cost || 0),
                0
              ) +
              (day.accommodation?.cost || 0);

            return (
              <Button
                key={day.day_number}
                variant={selectedDay === day.day_number ? "default" : "outline"}
                onClick={() => onSelectDay(day.day_number)}
                className={`min-w-[140px] h-auto p-4 flex flex-col items-start gap-2 rounded-lg transition-all duration-300 ${
                  selectedDay === day.day_number
                    ? "bg-slate-800 text-white border-slate-800"
                    : "border-slate-200 hover:bg-slate-100 hover:border-slate-300"
                }`}
              >
                <div className="font-semibold text-base">
                  Day {day.day_number}
                </div>
                <div
                  className={`text-xs ${
                    selectedDay === day.day_number
                      ? "opacity-80"
                      : "text-slate-500"
                  }`}
                >
                  {new Date(day.date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })}
                </div>
                <Badge
                  variant="secondary"
                  className={`text-xs font-medium ${
                    selectedDay === day.day_number
                      ? "bg-white/20 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  <DollarSign className="w-3 h-3 mr-1" />₹{dayBudget.toFixed(0)}
                </Badge>
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
