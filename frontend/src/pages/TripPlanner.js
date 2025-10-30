import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { createPageUrl } from "../utils";
import { tripService } from "../services/api";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Users,
  DollarSign,
  Share2,
  Download,
  Settings,
  Sparkles,
  Bus,
  Bot,
} from "lucide-react";
import { useLanguage } from "../components/language/LanguageProvider";

import TripSummary from "../components/trip-planner/TripSummary";
import DayItinerary from "../components/trip-planner/DayItinerary";
import DaySelector from "../components/trip-planner/DaySelector";
import BudgetTracker from "../components/trip-planner/BudgetTracker";
import BookingPanel from "../components/trip-planner/BookingPanel";
import CustomizationPanel from "../components/trip-options/CustomizationPanel";
import TransportDetails from "../components/trip-planner/TransportDetails";
import RealTimeUpdates from "../components/trip-planner/RealTimeUpdates";
import DestinationCarousel from "../components/trip-planner/DestinationCarousel";

export default function TripPlanner() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState(1);
  const [dailyItineraries, setDailyItineraries] = useState([]);
  const [activeTab, setActiveTab] = useState("itinerary");
  const [showCustomization, setShowCustomization] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [loadingDays, setLoadingDays] = useState(new Set()); // Track which days are being loaded
  const [loadedDays, setLoadedDays] = useState(new Set([1])); // Track which days are already loaded

  const loadTripData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const tripId = urlParams.get("trip_id");
      const optionId = urlParams.get("option_id");

      if (!tripId) {
        setError("No trip ID provided");
        setLoading(false);
        return;
      }

      // Fetch trip data from API
      const fetchedTrip = await tripService.getTrip(tripId);
      if (!fetchedTrip) {
        setError("Trip not found");
        setLoading(false);
        return;
      }

      setTrip(fetchedTrip);

      // If option_id is provided, get the selected option and its itineraries
      if (optionId) {
        try {
          // Get the selected trip option
          const tripOptions = await tripService.getTripOptions(tripId);
          const selectedOption = tripOptions.find((opt) => opt.id === optionId);

          if (selectedOption) {
            // Initialize with first day only (lazy loading)
            if (
              selectedOption.daily_itineraries &&
              selectedOption.daily_itineraries.length > 0
            ) {
              setDailyItineraries(selectedOption.daily_itineraries);
              setLoadedDays(new Set([1])); // Only first day is loaded initially
            } else {
              setError("No itinerary data found for selected option");
            }
          } else {
            setError("Selected trip option not found");
          }
        } catch (err) {
          console.error("Error loading trip option:", err);
          setError("Failed to load trip option details");
        }
      } else {
        // No option selected, redirect to options page
        navigate(`/trip-options?trip_id=${tripId}`);
        return;
      }
    } catch (err) {
      console.error("Error loading trip:", err);
      setError("Failed to load trip data");
    } finally {
      setLoading(false);
    }
  }, [t, navigate]);

  useEffect(() => {
    loadTripData();
  }, [loadTripData]);

  const handleDaySelect = async (dayNumber) => {
    setSelectedDay(dayNumber);

    // If this day hasn't been loaded yet, load it
    if (!loadedDays.has(dayNumber)) {
      await loadDayItinerary(dayNumber);
    }
  };

  const loadDayItinerary = async (dayNumber) => {
    if (loadingDays.has(dayNumber) || loadedDays.has(dayNumber)) {
      return; // Already loading or loaded
    }

    setLoadingDays((prev) => new Set(prev).add(dayNumber));

    try {
      const urlParams = new URLSearchParams(window.location.search);
      const tripId = urlParams.get("trip_id");
      const optionId = urlParams.get("option_id");

      if (!tripId) {
        throw new Error("No trip ID provided");
      }

      // Generate the specific day itinerary
      const dayData = await tripService.generateDayItinerary(
        tripId,
        dayNumber,
        optionId
      );

      if (dayData && dayData.itinerary) {
        // Update the daily itineraries with the new day
        setDailyItineraries((prev) => {
          const updated = [...prev];
          // Ensure we have enough days in the array
          while (updated.length < dayNumber) {
            updated.push(null);
          }
          updated[dayNumber - 1] = dayData.itinerary;
          return updated;
        });

        // Mark this day as loaded
        setLoadedDays((prev) => new Set(prev).add(dayNumber));
      }
    } catch (error) {
      console.error(`Error loading day ${dayNumber}:`, error);
      setError(`Failed to load day ${dayNumber} itinerary`);
    } finally {
      setLoadingDays((prev) => {
        const newSet = new Set(prev);
        newSet.delete(dayNumber);
        return newSet;
      });
    }
  };

  const handleShare = async () => {
    if (!trip) return;

    const shareData = {
      title: `${trip.destination} Trip Plan`,
      text: `Check out my ${dailyItineraries.length}-day trip to ${trip.destination}!`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        // Fallback to clipboard
        fallbackShare();
      }
    } else {
      fallbackShare();
    }
  };

  const fallbackShare = () => {
    const url = window.location.href;
    navigator.clipboard
      .writeText(url)
      .then(() => {
        // You could add a toast notification here
        alert("Trip link copied to clipboard!");
      })
      .catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
        alert("Trip link copied to clipboard!");
      });
  };

  const handleDownload = async () => {
    if (!trip) return;

    setIsDownloading(true);
    try {
      // Create a comprehensive trip summary
      const tripSummary = {
        destination: trip.destination,
        dates: `${new Date(trip.start_date).toLocaleDateString()} - ${new Date(
          trip.end_date
        ).toLocaleDateString()}`,
        travelers: trip.travelers,
        budget: trip.total_budget
          ? `₹${trip.total_budget.toLocaleString()}`
          : "Not specified",
        themes: trip.themes?.join(", ") || "None selected",
        itinerary: dailyItineraries
          .filter((day) => day)
          .map((day) => ({
            day: day.day_number,
            date: new Date(day.date).toLocaleDateString(),
            activities:
              day.activities
                ?.map(
                  (a) =>
                    `${a.time ? a.time + " - " : ""}${a.activity}${
                      a.location ? " at " + a.location : ""
                    }`
                )
                .join("\n") || "No activities",
            meals:
              day.meals
                ?.map(
                  (m) =>
                    `${m.meal_type}${m.restaurant ? " at " + m.restaurant : ""}`
                )
                .join(", ") || "No meals planned",
            accommodation: day.accommodation?.name || "No accommodation",
          })),
      };

      // Convert to downloadable format (simple text for now)
      const content = `
${trip.destination} Trip Itinerary
=================================

Trip Details:
- Destination: ${tripSummary.destination}
- Dates: ${tripSummary.dates}
- Travelers: ${tripSummary.travelers}
- Budget: ${tripSummary.budget}
- Interests: ${tripSummary.themes}

Daily Itinerary:
================

${tripSummary.itinerary
  .map(
    (day) => `
Day ${day.day} (${day.date})
${"-".repeat(20)}
Activities:
${day.activities}

Meals: ${day.meals}
Accommodation: ${day.accommodation}

`
  )
  .join("")}

Generated by Tripora - AI Travel Planner
      `.trim();

      // Create and trigger download
      const blob = new Blob([content], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${trip.destination.replace(/\s+/g, "_")}_itinerary.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Download failed. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleCustomize = () => {
    setShowCustomization(true);
  };

  const handleSaveCustomization = async (customizedOption) => {
    try {
      // Update the trip with customized option
      await tripService.updateTrip(trip.id, {
        selected_option: customizedOption,
      });

      // Update local state
      setTrip({ ...trip, selected_option: customizedOption });
      setDailyItineraries(customizedOption.daily_itineraries || []);
      setShowCustomization(false);
      // Could add a success notification here, e.g., toast.success('Trip customized successfully!');
    } catch (error) {
      console.error("Failed to save customization:", error);
      alert("Failed to save changes. Please try again.");
    }
  };

  const selectedDayData = dailyItineraries.find(
    (day) => day && day.day_number === selectedDay
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-slate-400 to-slate-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <p className="text-slate-600">{t("loadingTrip")}</p>
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
          <p className="text-slate-600 mb-4">
            {error === t("selectPlanFirst") ? t("choosePlanMessage") : error}
            {error === t("noItineraryFound") && t("noItineraryFoundMessage")}
          </p>
          <div className="flex gap-3 justify-center">
            <Button
              variant="outline"
              onClick={() => navigate(createPageUrl("MyTrips"))}
            >
              {t("backToTrips")}
            </Button>
            {(error === t("selectPlanFirst") ||
              error === t("noItineraryFound")) &&
              trip && (
                <Button
                  onClick={() =>
                    navigate(createPageUrl(`TripOptions?trip_id=${trip.id}`))
                  }
                  className="bg-slate-800 hover:bg-slate-900"
                >
                  {t("goToOptions")}
                </Button>
              )}
          </div>
        </div>
      </div>
    );
  }

  if (showCustomization && trip.selected_option) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <CustomizationPanel
            option={trip.selected_option}
            trip={trip}
            onSave={handleSaveCustomization}
            onCancel={() => setShowCustomization(false)}
          />
        </div>
      </div>
    );
  }

  // Use actual trip dates for duration to avoid lazy-loading artifacts
  const tripDuration =
    trip && trip.start_date && trip.end_date
      ? Math.max(
          1,
          Math.ceil(
            (new Date(trip.end_date) - new Date(trip.start_date)) /
              (1000 * 60 * 60 * 24)
          ) + 1
        )
      : dailyItineraries.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-sm border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigate(createPageUrl("MyTrips"))}
                className="rounded-full border-slate-200 hover:bg-slate-100"
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">
                  {trip.destination}
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500 mt-1">
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
                  {tripDuration > 0 && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4" />
                      <span>
                        {tripDuration} {t("days")}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share2 className="w-4 h-4 mr-2" />
                {t("share")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                disabled={isDownloading}
              >
                {isDownloading ? (
                  <>
                    <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                    Downloading...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    {t("download")}
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" onClick={handleCustomize}>
                <Settings className="w-4 h-4 mr-2" />
                {t("customize")}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Two column viewport-like layout: left scrolls, right sticky */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_380px] gap-8">
          {/* Left column: hero image + sticky tabs + sections (scrollable) */}
          <div>
            {/* Destination hero banner - carousel via Google Places Photos */}
            <DestinationCarousel
              tripId={trip?.id}
              destination={trip?.destination}
            />
            {/* Sticky tabs header */}
            <div className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-slate-200">
              <Tabs
                value={activeTab}
                onValueChange={setActiveTab}
                className="w-full"
              >
                <TabsList className="px-2 gap-2">
                  <TabsTrigger value="itinerary" className="px-3">
                    {t("dailyItinerary")}
                  </TabsTrigger>
                  <TabsTrigger value="updates" className="px-3">
                    Updates
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            {/* Day selector */}
            <div className="py-4">
              <DaySelector
                dailyItineraries={dailyItineraries}
                selectedDay={selectedDay}
                onSelectDay={handleDaySelect}
                loadingDays={loadingDays}
                loadedDays={loadedDays}
                trip={trip}
              />
            </div>
            {/* Tab contents */}
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsContent value="itinerary" className="space-y-6">
                <DayItinerary
                  dayData={selectedDayData}
                  isLoading={
                    loadingDays.has(selectedDay) ||
                    (!selectedDayData && !loadedDays.has(selectedDay))
                  }
                  selectedDay={selectedDay}
                />
              </TabsContent>
              <TabsContent value="updates" className="space-y-6">
                <RealTimeUpdates trip={trip} />
              </TabsContent>
            </Tabs>
            {/* Full-width travel details at the end of left column */}
            <Card className="border-slate-200 shadow-sm bg-white mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bus className="w-5 h-5" />
                  Travel & Transport Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TransportDetails
                  trip={trip}
                  dailyItineraries={dailyItineraries}
                />
              </CardContent>
            </Card>
          </div>

          {/* Right column: sticky Book Now card */}
          <div className="hidden lg:block sticky top-24 self-start h-min">
            <Card className="border-slate-200 shadow-sm bg-white w-[380px]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  {t("bookings")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <BookingPanel trip={trip} onBookingComplete={loadTripData} />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
