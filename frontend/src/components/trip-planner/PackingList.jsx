import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Luggage,
  CloudSun,
  Shirt,
  Footprints,
  Watch,
  Sparkles,
  AlertCircle,
  Loader2,
  Sun,
  CloudRain,
  Snowflake,
} from "lucide-react";
import { motion } from "framer-motion";
import { tripService } from "../../services/api";

const getWeatherIcon = (condition) => {
  const cond = condition?.toLowerCase() || "";
  if (cond.includes("rain") || cond.includes("drizzle")) return CloudRain;
  if (cond.includes("snow")) return Snowflake;
  if (cond.includes("cloud")) return CloudSun;
  if (cond.includes("clear") || cond.includes("sun")) return Sun;
  return CloudSun;
};

const getWeatherColor = (condition) => {
  const cond = condition?.toLowerCase() || "";
  if (cond.includes("rain") || cond.includes("drizzle")) return "text-blue-600 bg-blue-50 border-blue-200";
  if (cond.includes("snow")) return "text-slate-600 bg-slate-50 border-slate-200";
  if (cond.includes("cloud")) return "text-slate-600 bg-slate-50 border-slate-200";
  if (cond.includes("clear") || cond.includes("sun")) return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-slate-600 bg-slate-50 border-slate-200";
};

export default function PackingList({ trip, selectedDay = 1 }) {
  const [packingData, setPackingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (trip?.id) {
      fetchPackingData(trip.id, selectedDay);
    }
  }, [trip?.id, selectedDay]);

  const fetchPackingData = async (tripId, dayNumber) => {
    setLoading(true);
    setError(null);
    try {
      const data = await tripService.getDayPacking(tripId, dayNumber);
      setPackingData(data.packing_suggestions || null);
    } catch (error) {
      console.error("Error fetching packing suggestions:", error);
      setError("Failed to load packing suggestions");
      setPackingData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Luggage className="w-5 h-5 text-amber-500" />
            Packing List
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
            <span className="ml-2 text-sm text-slate-600">
              Generating packing suggestions...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Luggage className="w-5 h-5 text-amber-500" />
            Packing List
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8 text-sm text-red-600 bg-red-50 p-4 rounded-md">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!packingData) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Luggage className="w-5 h-5 text-amber-500" />
            Packing List
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8 text-sm text-slate-500">
            No packing data available for this day
          </div>
        </CardContent>
      </Card>
    );
  }

  const weatherSummary = packingData.weather_summary || {};
  const dressCode = packingData.dress_code || {};
  const clothing = packingData.clothing || {};
  const WeatherIcon = getWeatherIcon(weatherSummary.condition);

  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Luggage className="w-5 h-5 text-amber-500" />
          Packing List - Day {selectedDay}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-slate-600">
          Smart packing suggestions based on weather conditions, planned activities, and dress code requirements.
        </p>

        {/* Weather Summary */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <CloudSun className="w-5 h-5 text-blue-500" />
            Weather Summary
          </h3>
          <Card className={`border ${getWeatherColor(weatherSummary.condition)}`}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center border-2">
                  <WeatherIcon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-sm font-semibold">
                      {weatherSummary.temperature_range || "N/A"}
                    </Badge>
                    <span className="text-sm font-medium text-slate-700 capitalize">
                      {weatherSummary.condition || "Moderate"}
                    </span>
                  </div>
                  {weatherSummary.recommendations && (
                    <p className="text-xs text-slate-600 mt-1">
                      {weatherSummary.recommendations}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Dress Code Section (if temples are included) */}
        {dressCode.has_temple_visit && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600" />
              Temple Dress Code
            </h3>
            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="p-4">
                <div className="space-y-2">
                  {dressCode.requirements && dressCode.requirements.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-amber-900 mb-1">Requirements:</p>
                      <ul className="text-xs text-amber-800 list-disc list-inside space-y-1">
                        {dressCode.requirements.map((req, idx) => (
                          <li key={idx}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {dressCode.suggestions && dressCode.suggestions.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-amber-900 mb-1">Suggestions:</p>
                      <ul className="text-xs text-amber-800 list-disc list-inside space-y-1">
                        {dressCode.suggestions.map((sug, idx) => (
                          <li key={idx}>{sug}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Clothing Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Shirt className="w-5 h-5 text-purple-500" />
            Clothing
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {clothing.essential && clothing.essential.length > 0 && (
              <Card className="border-purple-200 bg-purple-50">
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-purple-900 mb-2">Essential</p>
                  <ul className="text-xs text-purple-800 space-y-1">
                    {clothing.essential.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-purple-600 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {clothing.weather_specific && clothing.weather_specific.length > 0 && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-blue-900 mb-2">Weather Specific</p>
                  <ul className="text-xs text-blue-800 space-y-1">
                    {clothing.weather_specific.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-blue-600 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {clothing.activity_specific && clothing.activity_specific.length > 0 && (
              <Card className="border-green-200 bg-green-50">
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-green-900 mb-2">Activity Specific</p>
                  <ul className="text-xs text-green-800 space-y-1">
                    {clothing.activity_specific.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-green-600 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {clothing.temple_appropriate && clothing.temple_appropriate.length > 0 && (
              <Card className="border-amber-200 bg-amber-50">
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-amber-900 mb-2">Temple Appropriate</p>
                  <ul className="text-xs text-amber-800 space-y-1">
                    {clothing.temple_appropriate.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-amber-600 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Footwear */}
        {packingData.footwear && packingData.footwear.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Footprints className="w-5 h-5 text-indigo-500" />
              Footwear
            </h3>
            <Card className="border-indigo-200 bg-indigo-50">
              <CardContent className="p-4">
                <ul className="text-sm text-indigo-800 space-y-1">
                  {packingData.footwear.filter(item => item).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-indigo-600 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Accessories */}
        {packingData.accessories && packingData.accessories.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Watch className="w-5 h-5 text-pink-500" />
              Accessories
            </h3>
            <Card className="border-pink-200 bg-pink-50">
              <CardContent className="p-4">
                <ul className="text-sm text-pink-800 space-y-1">
                  {packingData.accessories.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-pink-600 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Personal Care */}
        {packingData.personal_care && packingData.personal_care.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-500" />
              Personal Care
            </h3>
            <Card className="border-emerald-200 bg-emerald-50">
              <CardContent className="p-4">
                <ul className="text-sm text-emerald-800 space-y-1">
                  {packingData.personal_care.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-600 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Activity Specific Items */}
        {packingData.activity_specific_items && packingData.activity_specific_items.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <Luggage className="w-5 h-5 text-cyan-500" />
              Activity Specific Items
            </h3>
            <Card className="border-cyan-200 bg-cyan-50">
              <CardContent className="p-4">
                <ul className="text-sm text-cyan-800 space-y-1">
                  {packingData.activity_specific_items.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-cyan-600 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Important Notes */}
        {packingData.important_notes && packingData.important_notes.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-orange-500" />
              Important Notes
            </h3>
            <Card className="border-orange-200 bg-orange-50">
              <CardContent className="p-4">
                <ul className="text-sm text-orange-800 space-y-2">
                  {packingData.important_notes.map((note, idx) => (
                    <motion.li
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: idx * 0.1 }}
                      className="flex items-start gap-2"
                    >
                      <AlertCircle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span>{note}</span>
                    </motion.li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

