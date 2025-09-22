import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createPageUrl } from "../utils";
import { tripService } from "../services/api";
import { Button } from "../components/ui/button";
import {
  Sparkles,
  ArrowLeft,
  MapPin,
  Calendar,
  Users,
  RefreshCw,
  Briefcase,
  Compass,
  Heart,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useLanguage } from "../components/language/LanguageProvider";
import TripOptionCard from "../components/trip-options/TripOptionCard";
import CustomizationPanel from "../components/trip-options/CustomizationPanel";
// import { generateMultipleTripOptions } from "../pages/TripForm";

export default function TripOptions() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [optionToCustomize, setOptionToCustomize] = useState(null);
  const [regenerating, setRegenerating] = useState(false);

  const fetchTripData = async () => {
    setLoading(true);
    setError("");
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const tripId = urlParams.get("trip_id");
      if (!tripId) {
        setError("No trip ID provided.");
        setLoading(false);
        return;
      }

      // Fetch trip data from API
      const fetchedTrip = await tripService.getTrip(tripId);
      if (!fetchedTrip) {
        setError("Trip not found.");
        setLoading(false);
        return;
      }

      // Fetch trip options from API
      const tripOptions = await tripService.getTripOptions(tripId);

      // Set trip data with options
      setTrip({
        ...fetchedTrip,
        trip_options: tripOptions,
      });
    } catch (err) {
      console.error("Error fetching trip:", err);
      setError("Failed to load trip data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTripData();
  }, []);

  const handleRegenerateOptions = async () => {
    setRegenerating(true);
    try {
      // Regenerate trip options using API
      const newOptions = await tripService.generateTripOptions(trip.id, {});

      // Update local state with new options
      setTrip({
        ...trip,
        trip_options: newOptions,
      });
    } catch (err) {
      console.error("Error regenerating options:", err);
      setError("Failed to regenerate options.");
    } finally {
      setRegenerating(false);
    }
  };

  const handleSelectOption = async (option) => {
    try {
      // Select the trip option using API
      await tripService.selectTripOption(trip.id, option.id);

      // Navigate to trip planner
      navigate(`/trip-planner?trip_id=${trip.id}&option_id=${option.id}`);
    } catch (err) {
      console.error("Error selecting option:", err);
      setError("Could not select this plan. Please try again.");
    }
  };

  const handleCustomizeOption = (option) => {
    setOptionToCustomize(option);
    setIsCustomizing(true);
  };

  const handleSaveCustomization = async (customizedOption) => {
    try {
      // Update the trip option using API
      await tripService.updateTrip(trip.id, {
        trip_options: trip.trip_options.map((opt) =>
          opt.id === customizedOption.id ? customizedOption : opt
        ),
      });

      // Update local state
      setTrip({
        ...trip,
        trip_options: trip.trip_options.map((opt) =>
          opt.id === customizedOption.id ? customizedOption : opt
        ),
      });

      setIsCustomizing(false);
      setOptionToCustomize(null);
    } catch (err) {
      console.error("Error saving customization:", err);
      setError("Failed to save customization.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-blue-500" />
          </div>
          <p className="text-slate-600">{t("loadingOptions")}</p>
        </div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center max-w-md mx-4">
          <h2 className="text-xl font-bold text-slate-800 mb-2">
            {t("somethingWentWrong")}
          </h2>
          <p className="text-slate-600 mb-4">{error || t("optionsError")}</p>
          <Button onClick={() => navigate(createPageUrl("TripForm"))}>
            {t("backToForm")}
          </Button>
        </div>
      </div>
    );
  }

  const getOptionIcon = (optionId) => {
    switch (optionId) {
      case "balanced":
        return Compass;
      case "adventure":
        return Briefcase;
      case "cultural":
        return Heart;
      default:
        return Sparkles;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigate(createPageUrl("TripForm"))}
                className="rounded-full border-slate-200 hover:bg-slate-100"
              >
                <ArrowLeft className="w-4 h-4 text-slate-600" />
              </Button>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">
                  {t("choosePerfectTrip")}
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500 mt-1">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4" />
                    <span>{trip.destination}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {new Date(trip.start_date).toLocaleDateString()} -{" "}
                      {new Date(trip.end_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4" />
                    <span>
                      {trip.travelers} {t("travelers")}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleRegenerateOptions}
              disabled={regenerating}
              className="border-slate-200 hover:bg-slate-100"
            >
              <RefreshCw
                className={`w-4 h-4 mr-2 ${regenerating ? "animate-spin" : ""}`}
              />
              {t("regenerateOptions")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 text-center">
          <h2 className="text-xl font-semibold text-slate-800 mb-2">
            {t("uniqueTripPlans")}
          </h2>
          <p className="text-slate-600">{t("tailoredTravelStyles")}</p>
        </div>

        <AnimatePresence>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {trip.trip_options?.map((option, index) => {
              const OptionIcon = getOptionIcon(option.id);
              return (
                <motion.div
                  key={option.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <TripOptionCard
                    option={option}
                    trip={trip}
                    icon={OptionIcon}
                    onSelect={() => handleSelectOption(option)}
                    onCustomize={() => handleCustomizeOption(option)}
                  />
                </motion.div>
              );
            })}
          </div>
        </AnimatePresence>

        <CustomizationPanel
          isOpen={isCustomizing}
          onClose={() => setIsCustomizing(false)}
          option={optionToCustomize}
          trip={trip}
          onSave={handleSaveCustomization}
        />
      </main>
    </div>
  );
}
