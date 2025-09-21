import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

export default function BudgetTracker({ trip, dailyItineraries }) {
  // Get currency symbol based on trip currency
  const getCurrencySymbol = (currency) => {
    switch (currency) {
      case "INR":
        return "₹";
      case "USD":
        return "$";
      case "EUR":
        return "€";
      case "GBP":
        return "£";
      default:
        return "₹"; // Default to INR
    }
  };

  const currencySymbol = getCurrencySymbol(trip.currency || "INR");

  // Calculate total costs
  const totalEstimated = dailyItineraries.reduce((sum, day) => {
    const dayTotal =
      (day.activities || []).reduce(
        (daySum, activity) => daySum + (activity.cost || 0),
        0
      ) +
      (day.meals || []).reduce((daySum, meal) => daySum + (meal.cost || 0), 0) +
      (day.accommodation?.cost || 0);
    return sum + dayTotal;
  }, 0);

  // Calculate category breakdowns
  const categoryBreakdown = dailyItineraries.reduce(
    (breakdown, day) => {
      breakdown.activities += (day.activities || []).reduce(
        (sum, activity) => sum + (activity.cost || 0),
        0
      );
      breakdown.meals += (day.meals || []).reduce(
        (sum, meal) => sum + (meal.cost || 0),
        0
      );
      breakdown.accommodation += day.accommodation?.cost || 0;
      breakdown.transportation += (day.transportation || []).reduce(
        (sum, transport) => sum + (transport.cost || 0),
        0
      );
      return breakdown;
    },
    { activities: 0, meals: 0, accommodation: 0, transportation: 0 }
  );

  const budgetUtilization = (totalEstimated / trip.total_budget) * 100;
  const remaining = trip.total_budget - totalEstimated;

  const categories = [
    {
      name: "Activities",
      amount: categoryBreakdown.activities,
      color: "bg-blue-500",
      lightColor: "bg-blue-100",
    },
    {
      name: "Meals",
      amount: categoryBreakdown.meals,
      color: "bg-emerald-500",
      lightColor: "bg-emerald-100",
    },
    {
      name: "Accommodation",
      amount: categoryBreakdown.accommodation,
      color: "bg-purple-500",
      lightColor: "bg-purple-100",
    },
    {
      name: "Transportation",
      amount: categoryBreakdown.transportation,
      color: "bg-amber-500",
      lightColor: "bg-amber-100",
    },
  ];

  const getBudgetStatus = () => {
    if (budgetUtilization > 100)
      return {
        color: "text-red-600",
        bg: "bg-red-50",
        border: "border-red-200",
        icon: AlertTriangle,
      };
    if (budgetUtilization > 90)
      return {
        color: "text-amber-600",
        bg: "bg-amber-50",
        border: "border-amber-200",
        icon: TrendingUp,
      };
    return {
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      icon: CheckCircle,
    };
  };

  const budgetStatus = getBudgetStatus();

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-lg font-semibold text-slate-900">
          <div className="w-8 h-8 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
            <DollarSign className="w-5 h-5" aria-hidden="true" />
          </div>
          Budget Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Budget Overview */}
        <div className="text-center space-y-3">
          <div className="text-2xl font-bold text-slate-900">
            {currencySymbol}
            {totalEstimated.toLocaleString()}
          </div>
          <div className="text-sm text-slate-600">
            of {currencySymbol}
            {trip.total_budget.toLocaleString()} budget
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  budgetUtilization > 100
                    ? "bg-red-500"
                    : budgetUtilization > 90
                    ? "bg-amber-500"
                    : "bg-emerald-500"
                }`}
                style={{ width: `${Math.min(budgetUtilization, 100)}%` }}
                role="progressbar"
                aria-valuenow={budgetUtilization}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label={`Budget utilization: ${budgetUtilization.toFixed(
                  1
                )}%`}
              />
            </div>
            <div className={`text-sm font-medium ${budgetStatus.color}`}>
              {budgetUtilization.toFixed(1)}% utilized
            </div>
          </div>
        </div>

        {/* Remaining Budget */}
        <div
          className={`p-4 rounded-lg border ${budgetStatus.bg} ${budgetStatus.border}`}
        >
          <div className="flex items-center justify-center gap-3">
            <budgetStatus.icon
              className={`w-5 h-5 ${budgetStatus.color}`}
              aria-hidden="true"
            />
            <span className={`font-semibold ${budgetStatus.color}`}>
              {remaining < 0 ? "Over budget by" : "Remaining:"} {currencySymbol}
              {Math.abs(remaining).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="space-y-4">
          <h4 className="font-semibold text-slate-900">Spending Breakdown</h4>
          {categories.map((category, index) => {
            const percentage =
              totalEstimated > 0 ? (category.amount / totalEstimated) * 100 : 0;

            return (
              <div key={index} className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium text-slate-700">
                    {category.name}
                  </span>
                  <span className="text-slate-900 font-semibold">
                    {currencySymbol}
                    {category.amount.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${category.color}`}
                    style={{ width: `${percentage}%` }}
                    role="progressbar"
                    aria-valuenow={percentage}
                    aria-valuemin="0"
                    aria-valuemax="100"
                    aria-label={`${category.name}: ${percentage.toFixed(
                      1
                    )}% of total spending`}
                  />
                </div>
                <div className="text-xs text-slate-500 text-right">
                  {percentage.toFixed(1)}%
                </div>
              </div>
            );
          })}
        </div>

        {/* Daily Average */}
        <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
          <div className="text-center">
            <div className="text-lg font-bold text-slate-900">
              {currencySymbol}
              {(totalEstimated / dailyItineraries.length || 0).toFixed(0)}
            </div>
            <div className="text-sm text-slate-600">Average per day</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
