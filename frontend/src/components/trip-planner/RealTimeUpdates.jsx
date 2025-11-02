import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  CloudSun,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Loader2,
  MapPin,
  Droplets,
} from "lucide-react";
import { motion } from "framer-motion";
import { tripService } from "../../services/api";

const getIconForType = (type) => {
  switch (type) {
    case "weather":
      return CloudSun;
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
  
  // Weather state for entire trip
  const [weatherUpdates, setWeatherUpdates] = useState([]);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [errorWeather, setErrorWeather] = useState(null);

  useEffect(() => {
    if (trip?.id) {
      fetchSmartAdjustments(trip.id, selectedDay);
      fetchWeatherUpdates(trip.id);
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

  const fetchWeatherUpdates = async (tripId) => {
    setLoadingWeather(true);
    setErrorWeather(null);
    try {
      const data = await tripService.getTripWeather(tripId);
      console.log("Weather API response:", data);
      const updates = data.weather_updates || [];
      console.log(`Received ${updates.length} weather updates for trip`);
      if (updates.length === 0) {
        console.warn("No weather updates in response. Response structure:", data);
      }
      setWeatherUpdates(updates);
    } catch (error) {
      console.error("Error fetching weather updates:", error);
      console.error("Error details:", error.response?.data || error.message);
      setErrorWeather("Failed to load weather data");
      setWeatherUpdates([]);
    } finally {
      setLoadingWeather(false);
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

  // Loading state for all data
  const isLoading = loading || loadingWeather;
  
  if (isLoading && !weatherUpdates.length && !adjustments.length) {
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

  // Helper function to format temperature
  const formatTemperature = (temp) => {
    if (typeof temp === "number") {
      return `${Math.round(temp)}°C`;
    }
    return "N/A";
  };

  // Helper function to get weather icon based on condition
  const getWeatherCondition = (condition) => {
    const cond = condition?.toLowerCase() || "";
    if (cond.includes("rain") || cond.includes("drizzle")) return { icon: Droplets, color: "blue", borderClass: "border-blue-300", textClass: "text-blue-600", label: "Rainy" };
    if (cond.includes("cloud")) return { icon: CloudSun, color: "slate", borderClass: "border-slate-300", textClass: "text-slate-600", label: "Cloudy" };
    if (cond.includes("clear") || cond.includes("sun")) return { icon: CloudSun, color: "amber", borderClass: "border-amber-300", textClass: "text-amber-600", label: "Sunny" };
    return { icon: CloudSun, color: "slate", borderClass: "border-slate-300", textClass: "text-slate-600", label: condition || "Clear" };
  };

  // Helper function to get weather color classes for card styling
  const getWeatherColor = (condition) => {
    const cond = condition?.toLowerCase() || "";
    if (cond.includes("rain") || cond.includes("drizzle")) {
      return "text-blue-600 bg-blue-50 border-blue-200";
    }
    if (cond.includes("cloud")) {
      return "text-slate-600 bg-slate-50 border-slate-200";
    }
    if (cond.includes("clear") || cond.includes("sun")) {
      return "text-amber-600 bg-amber-50 border-amber-200";
    }
    return "text-slate-600 bg-slate-50 border-slate-200";
  };

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          Real-Time Updates
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-slate-600 mb-6">
          Real-time weather updates for your destination and smart adjustment suggestions to optimize your journey.
        </p>
        
        {/* Weather Updates Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-blue-500" />
              Weather Updates
            </h3>
            {loadingWeather && (
              <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
            )}
          </div>
          
          {errorWeather ? (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
              {errorWeather}
            </div>
          ) : weatherUpdates.length > 0 ? (
            <div className="space-y-3">
              {weatherUpdates.map((weather, index) => {
                const weatherInfo = weather.weather_data || {};
                const weatherSummary = weather.weather_summary || {};
                const condition = getWeatherCondition(
                  weatherSummary.condition_keyword || weatherInfo.condition
                );
                const ConditionIcon = condition.icon;
                
                // Use formatted summary if available, otherwise fallback to raw data
                const temperatureDisplay = weatherSummary.temperature_range || 
                  formatTemperature(weatherInfo.temperature);
                const conditionDisplay = weatherSummary.condition || 
                  condition.label;
                const recommendations = weatherSummary.recommendations || "";
                
                // Format date for display
                const weatherDate = weather.date ? new Date(weather.date) : null;
                const dateDisplay = weatherDate ? weatherDate.toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  year: weatherDate.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
                }) : '';
                
                return (
                  <motion.div
                    key={weather.day_number || index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <Card className={`border ${getWeatherColor(weatherSummary.condition_keyword || weatherInfo.condition)}`}>
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center border-2">
                            <ConditionIcon className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-semibold text-slate-800">
                                {weather.place_name || "Location"}
                                {weather.day_number && ` - Day ${weather.day_number}`}
                              </h4>
                              {dateDisplay && (
                                <Badge variant="outline" className="text-xs">
                                  {dateDisplay}
                                </Badge>
                              )}
                              {weather.location && weather.location !== weather.place_name && (
                                <span className="text-xs text-slate-500 flex items-center gap-1">
                                  <MapPin className="w-3 h-3" />
                                  {weather.location}
                                </span>
                              )}
                            </div>
                            
                            {/* Weather Summary Card - Similar to Packing List */}
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge variant="outline" className="text-sm font-semibold">
                                  {temperatureDisplay}
                                </Badge>
                              </div>
                              
                              <div className="text-sm text-slate-700 mb-2">
                                <p className="font-medium capitalize">
                                  {conditionDisplay}
                                </p>
                              </div>
                              
                              {recommendations && (
                                <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded-md">
                                  <p className="font-medium text-slate-700 mb-1">Advice:</p>
                                  <p>{recommendations}</p>
                                </div>
                              )}
                              
                              {/* Additional details in smaller text */}
                              <div className="flex flex-wrap gap-3 text-xs text-slate-500 mt-2 pt-2 border-t border-slate-200">
                                {weatherInfo.humidity !== undefined && (
                                  <span>Humidity: {weatherInfo.humidity}%</span>
                                )}
                                {weatherInfo.wind_speed > 0 && (
                                  <span>Wind: {Math.round(weatherInfo.wind_speed)} m/s</span>
                                )}
                                {weatherInfo.rain > 0 && (
                                  <span className="text-blue-700">
                                    <Droplets className="w-3 h-3 inline mr-1" />
                                    Rain: {weatherInfo.rain}mm
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          ) : !loadingWeather ? (
            <div className="text-center py-4 text-sm text-slate-500">
              No weather data available for your destination
            </div>
          ) : null}
        </div>

        {/* Smart Adjustments Section - Only show if adjustments are needed */}
        {adjustments && adjustments.length > 0 ? (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Smart Adjustments
            </h3>
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
          </div>
        ) : !loading ? (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Smart Adjustments
            </h3>
            <Card className="border-emerald-200 bg-emerald-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center border-2 border-emerald-300">
                    <Sparkles className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-emerald-900">
                      No adjustments needed at this time. Your itinerary looks perfect!
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}