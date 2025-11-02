import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import {
  CloudSun,
  Clock,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { motion } from "framer-motion";
import { tripService } from "../../services/api";

const getIconForType = (type) => {
  switch (type) {
    case "weather":
      return CloudSun;
    case "traffic":
      return Clock;
    case "route":
      return ArrowRight;
    case "opportunity":
      return Sparkles;
    case "alert":
      return AlertCircle;
    default:
      return Sparkles;
  }
};

const getColorForType = (type, severity) => {
  const severityMap = {
    high: "red",
    medium: "amber",
    low: "blue",
  };

  const typeMap = {
    weather: severityMap[severity] || "blue",
    traffic: severityMap[severity] || "amber",
    route: "blue",
    opportunity: "emerald",
    alert: "red",
  };

  return typeMap[type] || "blue";
};

const getIconColor = (color) => {
  switch (color) {
    case "blue":
      return "text-blue-600";
    case "amber":
      return "text-amber-600";
    case "emerald":
      return "text-emerald-600";
    case "red":
      return "text-red-600";
    default:
      return "text-slate-600";
  }
};

const getBgColor = (color) => {
  switch (color) {
    case "blue":
      return "bg-blue-50 border-blue-200";
    case "amber":
      return "bg-amber-50 border-amber-200";
    case "emerald":
      return "bg-emerald-50 border-emerald-200";
    case "red":
      return "bg-red-50 border-red-200";
    default:
      return "bg-slate-50 border-slate-200";
  }
};

export default function RealTimeUpdates({ trip, selectedDay = 1 }) {
  const [adjustments, setAdjustments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adjusting, setAdjusting] = useState({});

  useEffect(() => {
    if (trip?.id) {
      fetchSmartAdjustments(trip.id, selectedDay);
    }
  }, [trip?.id, selectedDay]);

  const fetchSmartAdjustments = async (tripId, dayNumber) => {
    setLoading(true);
    try {
      const data = await tripService.getSmartAdjustments(tripId, dayNumber);
      setAdjustments(data.adjustments || []);
    } catch (error) {
      console.error("Error fetching smart adjustments:", error);
      // Keep empty array on error - component will show empty state
      setAdjustments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdjustItinerary = async (adjustment) => {
    const adjustmentId = adjustment.id;
    setAdjusting({ ...adjusting, [adjustmentId]: true });

    try {
      // Prepare adjustment data based on type
      const adjustmentData = {
        weather_data: adjustment.weather_data,
        affected_activities: adjustment.affected_activities,
        route_info: adjustment.route_info,
        place_info: adjustment.place_info,
        attraction: adjustment.attraction,
      };

      const result = await tripService.adjustItinerary(
        trip.id,
        selectedDay,
        adjustment.type,
        adjustmentData
      );

      alert(result.message || "Your itinerary has been updated based on the conditions.");

      // Refresh adjustments after successful adjustment
      await fetchSmartAdjustments(trip.id, selectedDay);

      // If onTripUpdate callback exists, notify parent component
      if (trip.onTripUpdate) {
        trip.onTripUpdate();
      }
      
      // Force page reload to show updated itinerary
      window.location.reload();
    } catch (error) {
      console.error("Error adjusting itinerary:", error);
      alert(error.response?.data?.detail || "Could not adjust itinerary. Please try again.");
    } finally {
      setAdjusting({ ...adjusting, [adjustmentId]: false });
    }
  };

  if (loading) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          Real-Time Updates
        </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
            <span className="ml-2 text-sm text-slate-600">
              Analyzing conditions...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!adjustments || adjustments.length === 0) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          Real-Time Updates
        </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-600 mb-6">
            Your trip is alive! We monitor conditions in real-time to suggest
            smart adjustments, ensuring you have the best possible experience.
          </p>
          <div className="text-center py-8 text-sm text-slate-500">
            No adjustments needed at this time. Your itinerary looks perfect!
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          Real-Time Updates
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600 mb-6">
          Real-time updates: We monitor weather conditions, traffic congestion, route changes, 
          and place availability to keep your itinerary optimized throughout your journey.
        </p>
        <div className="space-y-4">
          {adjustments.map((adjustment, index) => {
            const Icon = getIconForType(adjustment.type);
            const color = getColorForType(
              adjustment.type,
              adjustment.severity || "medium"
            );

            return (
              <motion.div
                key={adjustment.id || index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className={`${getBgColor(color)}`}>
                  <CardContent className="p-4 flex items-start gap-4">
                    <div
                      className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getIconColor(
                        color
                      )} bg-white`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-800 mb-1">
                        {adjustment.title}
                      </h4>
                      <p className="text-sm text-slate-600 mb-3">
                        {adjustment.description}
                      </p>
                      {adjustment.suggestions && adjustment.suggestions.length > 0 && (
                        <ul className="text-xs text-slate-500 mb-3 list-disc list-inside">
                          {adjustment.suggestions.slice(0, 2).map((suggestion, idx) => (
                            <li key={idx}>{suggestion}</li>
                          ))}
                        </ul>
                      )}
                      <Button
                        variant="link"
                        className="p-0 h-auto text-blue-600 font-semibold"
                        onClick={() => handleAdjustItinerary(adjustment)}
                        disabled={adjusting[adjustment.id]}
                      >
                        {adjusting[adjustment.id] ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            Adjusting...
                          </>
                        ) : (
                          <>
                            {adjustment.action || "Adjust Itinerary"}
                            <ArrowRight className="w-4 h-4 ml-1" />
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}