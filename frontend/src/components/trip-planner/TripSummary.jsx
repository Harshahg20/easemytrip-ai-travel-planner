import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { MapPin, Calendar, DollarSign, Users, Heart } from "lucide-react";
import { Progress } from "../ui/progress";

export default function TripSummary({ trip, dailyItineraries }) {
  if (!trip) return null;

  const totalEstimatedCost = dailyItineraries.reduce((sum, day) => {
    const dayTotal =
      (day.activities || []).reduce(
        (daySum, activity) => daySum + (activity.cost || 0),
        0
      ) +
      (day.meals || []).reduce((daySum, meal) => daySum + (meal.cost || 0), 0) +
      (day.accommodation?.cost || 0);
    return sum + dayTotal;
  }, 0);

  const budgetUtilization =
    trip.total_budget > 0 ? (totalEstimatedCost / trip.total_budget) * 100 : 0;

  const summaryItems = [
    {
      label: "Days",
      value: dailyItineraries.length,
      icon: Calendar,
      color: "text-blue-600",
    },
    {
      label: "Travelers",
      value: trip.travelers,
      icon: Users,
      color: "text-purple-600",
    },
    {
      label: "Est. Cost",
      value: `₹${totalEstimatedCost.toLocaleString()}`,
      icon: DollarSign,
      color: "text-emerald-600",
    },
    {
      label: "Interests",
      value: trip.themes?.length || 0,
      icon: Heart,
      color: "text-red-600",
    },
  ];

  return (
    <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
      <CardHeader className="bg-slate-50/70 border-b border-slate-200">
        <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-800">
          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <MapPin className="w-5 h-5" />
          </div>
          Trip Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Side: Key Stats & Budget */}
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {summaryItems.map((item, index) => (
                <div
                  key={index}
                  className="flex flex-col items-center justify-center text-center p-3 bg-slate-50 rounded-lg border border-slate-200 h-full"
                >
                  <item.icon
                    className={`w-6 h-6 ${item.color} mx-auto mb-1.5`}
                  />
                  <div className="text-xl font-bold text-slate-800">
                    {item.value}
                  </div>
                  <div className="text-xs text-slate-600">{item.label}</div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="font-medium text-slate-800">
                  Budget Utilization
                </span>
                <span
                  className={`font-semibold ${
                    budgetUtilization > 100
                      ? "text-red-600"
                      : budgetUtilization > 90
                      ? "text-amber-600"
                      : "text-emerald-600"
                  }`}
                >
                  {budgetUtilization.toFixed(0)}%
                </span>
              </div>
              <Progress
                value={Math.min(budgetUtilization, 100)}
                indicatorClassName={
                  budgetUtilization > 100
                    ? "bg-red-500"
                    : budgetUtilization > 90
                    ? "bg-amber-500"
                    : "bg-emerald-500"
                }
              />
            </div>
          </div>

          {/* Right Side: Interests */}
          {trip.themes && trip.themes.length > 0 && (
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <h4 className="font-semibold text-slate-800 mb-3">
                Your Interests
              </h4>
              <div className="flex flex-wrap gap-2">
                {trip.themes.map((interest, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="bg-slate-200 text-slate-700 capitalize text-sm px-3 py-1"
                  >
                    {interest.replace(/_/g, " ")}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
