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
import InteractiveMap from "../components/trip-planner/InteractiveMap";
import BookingPanel from "../components/trip-planner/BookingPanel";
import CustomizationPanel from "../components/trip-options/CustomizationPanel";
import TransportDetails from "../components/trip-planner/TransportDetails";
import RealTimeUpdates from "../components/trip-planner/RealTimeUpdates";

export default function TripPlanner() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState(1);
  const [dailyItineraries, setDailyItineraries] = useState([]);
  const [showCustomization, setShowCustomization] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

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
            // Get detailed itinerary for the selected option
            const itinerary = await tripService.getTripItinerary(tripId);
            setDailyItineraries(itinerary || []);
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

  const handleDaySelect = (dayNumber) => {
    setSelectedDay(dayNumber);
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
        itinerary: dailyItineraries.map((day) => ({
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
    (day) => day.day_number === selectedDay
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

  const tripDuration = dailyItineraries.length;

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
        <div className="space-y-8">
          {/* Trip Overview Section */}
          <TripSummary trip={trip} dailyItineraries={dailyItineraries} />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Day Selector */}
              <DaySelector
                dailyItineraries={dailyItineraries}
                selectedDay={selectedDay}
                onSelectDay={handleDaySelect}
              />

              {/* Tabbed Content */}
              <Tabs defaultValue="itinerary" className="w-full">
                <TabsList className="grid w-full grid-cols-5 mb-6">
                  <TabsTrigger
                    value="itinerary"
                    className="flex items-center gap-2"
                  >
                    <Calendar className="w-4 h-4" />
                    {t("dailyItinerary")}
                  </TabsTrigger>
                  <TabsTrigger
                    value="transport"
                    className="flex items-center gap-2"
                  >
                    <Bus className="w-4 h-4" />
                    Travel
                  </TabsTrigger>
                  <TabsTrigger value="map" className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    {t("map")}
                  </TabsTrigger>
                  <TabsTrigger
                    value="bookings"
                    className="flex items-center gap-2"
                  >
                    <DollarSign className="w-4 h-4" />
                    {t("bookings")}
                  </TabsTrigger>
                  <TabsTrigger
                    value="updates"
                    className="flex items-center gap-2"
                  >
                    <Bot className="w-4 h-4" />
                    Updates
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="itinerary" className="space-y-6">
                  <DayItinerary dayData={selectedDayData} />
                </TabsContent>

                <TabsContent value="transport" className="space-y-6">
                  <Card className="border-slate-200 shadow-sm bg-white">
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
                </TabsContent>

                <TabsContent value="map" className="space-y-6">
                  <Card className="border-slate-200 shadow-sm bg-white">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MapPin className="w-5 h-5" />
                        {t("interactiveMap")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <InteractiveMap dayData={selectedDayData} />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="bookings" className="space-y-6">
                  <BookingPanel trip={trip} onBookingComplete={loadTripData} />
                </TabsContent>

                <TabsContent value="updates" className="space-y-6">
                  <RealTimeUpdates trip={trip} />
                </TabsContent>
              </Tabs>
            </div>

            {/* Right Sidebar - Budget Tracker */}
            <div className="lg:col-span-1 space-y-6">
              <BudgetTracker trip={trip} dailyItineraries={dailyItineraries} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
