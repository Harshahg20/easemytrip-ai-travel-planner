import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
// import { Progress } from "../components/ui/progress";
import { Button } from "../components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Card, CardContent } from "../components/ui/card";
import { createPageUrl } from "../utils";
import { tripService } from "../services/api";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import DestinationStep from "../components/trip-form/DestinationStep";
import DateStep from "../components/trip-form/DateStep";
import BudgetStep from "../components/trip-form/BudgetStep";
import TravelersStep from "../components/trip-form/TravelersStep";
import InterestsStep from "../components/trip-form/InterestsStep";
import PreferenceStep from "../components/trip-form/PreferenceStep";
import { useLanguage } from "../components/language/LanguageProvider";

export const generateMultipleTripOptions = (trip) => {
  const baseCost = trip.total_budget * 0.8; // 80% of total budget for daily expenses
  // Ensure start_date and end_date are valid Date objects for calculation
  const startDate = new Date(trip.start_date);
  const endDate = new Date(trip.end_date);

  // Calculate duration, ensuring it's at least 1 day.
  // Add 1 to include both start and end date.
  const duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
  const baseCoords = { lat: 28.6139, lng: 77.209 }; // Delhi as a default example, could be dynamic based on trip.destination later

  // Expanded data pools for dynamic content
  const activityPools = {
    adventure: [
      { name: "Trekking to scenic mountain peaks", category: "Adventure" },
      { name: "White water rafting expedition", category: "Adventure" },
      { name: "Paragliding over valleys", category: "Adventure" },
      { name: "Rock climbing adventure", category: "Adventure" },
      { name: "Cave exploration tour", category: "Exploration" },
      { name: "Wildlife safari experience", category: "Nature" },
      { name: "Bungee jumping thrilling experience", category: "Adventure" },
      { name: "Scuba diving in clear waters", category: "Adventure" },
      { name: "Desert dune bashing", category: "Adventure" },
      { name: "Zip-lining through the forest", category: "Adventure" },
    ],
    cultural: [
      { name: "Heritage palace tour", category: "Heritage" },
      { name: "Traditional folk performance", category: "Culture" },
      { name: "Ancient temple complex visit", category: "Heritage" },
      { name: "Local handicraft workshop", category: "Culture" },
      { name: "Historical museum exploration", category: "History" },
      { name: "Architectural monuments tour", category: "Heritage" },
      { name: "Art gallery visit and workshop", category: "Art" },
      { name: "Culinary class for local cuisine", category: "Culture" },
      { name: "Attend a religious ceremony", category: "Culture" },
      { name: "Traditional market shopping experience", category: "Shopping" },
    ],
    balanced: [
      { name: "City highlights walking tour", category: "Sightseeing" },
      { name: "Scenic lake boat cruise", category: "Leisure" },
      { name: "Local market exploration", category: "Shopping" },
      { name: "Panoramic viewpoint visit", category: "Sightseeing" },
      { name: "Botanical garden stroll", category: "Nature" },
      { name: "Cultural district exploration", category: "Culture" },
      { name: "Relaxing spa and wellness session", category: "Wellness" },
      { name: "Evening rooftop dinner with city views", category: "Dining" },
      {
        name: "Photography tour of picturesque spots",
        category: "Photography",
      },
      { name: "Sunset beach walk", category: "Leisure" },
    ],
  };

  const restaurantPools = {
    restaurants: [
      "The Spice Garden",
      "Royal Dining Hall",
      "Curry Junction",
      "Mountain View Restaurant",
      "Heritage Kitchen",
      "The Local Table",
      "Flavors of India",
      "Golden Palace Restaurant",
      "Riverside Cafe",
      "The Traditional Dhaba",
      "Masala House",
      "The Grand Kitchen",
      "Authentic Flavors",
      "The Cultural Kitchen",
      "Taste Paradise",
      "Local Delights",
      "The Food Court",
      "Regional Specialties",
      "The Hungry Traveler",
      "Spice Route Cafe",
      "Urban Bistro",
      "Gourmet Grill",
      "Oceanic Tastes",
      "Forest Glade Eatery",
      "Skyline Lounge",
      "Garden Pavilion",
      "The Chef's Table",
      "Harmony Bistro",
      "Grand Saffron",
      "Pearl Restaurant",
      "Sunset Point Diner",
      "The Oasis Cafe",
      "Mystic Spice",
      "Echoes of Tradition",
      "Culinary Haven",
      "Dreamland Cafe",
      "Vivid Plate",
      "Azure Restaurant",
      "Golden Spoon",
      "The Hearthstone",
      "Evergreen Eatery",
      "Canyon Grill",
      "Emerald Restaurant",
      "Silver Platter",
      "Crimson Kitchen",
      "The Lighthouse Bistro",
      "Starry Night Cafe",
      "Whispering Pines Restaurant",
    ],
    cuisines: [
      "North Indian",
      "South Indian",
      "Local Specialty",
      "Continental",
      "Chinese",
      "Mughlai",
      "Rajasthani",
      "Bengali",
      "Punjabi",
      "Gujarati",
      "Italian",
      "Thai",
      "Mexican",
      "Mediterranean",
      "Japanese",
      "American",
    ],
  };

  // Track used restaurants to avoid repetition within a single option's generation
  const usedRestaurants = new Set();

  const getRandomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];

  const getUniqueRestaurant = () => {
    let restaurant;
    let attempts = 0;
    const maxAttempts = restaurantPools.restaurants.length * 2; // Prevent infinite loops if all are used
    do {
      restaurant = getRandomItem(restaurantPools.restaurants);
      attempts++;
      // If we've tried many times or used all unique restaurants, clear and reuse.
      if (
        attempts > maxAttempts ||
        usedRestaurants.size >= restaurantPools.restaurants.length
      ) {
        console.warn(
          "Ran out of unique restaurants for the current option, resetting pool."
        );
        usedRestaurants.clear();
        restaurant = getRandomItem(restaurantPools.restaurants); // Pick one after clearing
        break;
      }
    } while (usedRestaurants.has(restaurant));

    usedRestaurants.add(restaurant);
    return restaurant;
  };

  const generateDailyItinerary = (dayNumber, focus) => {
    let activityCost, mealCost;
    // Distribute costs based on focus and total budget per day
    const dailyBaseCost = baseCost / duration;

    switch (focus) {
      case "adventure":
        activityCost = dailyBaseCost * 0.5; // More for activities
        mealCost = dailyBaseCost * 0.2; // Less for food
        break;
      case "cultural":
        activityCost = dailyBaseCost * 0.3; // Moderate for activities
        mealCost = dailyBaseCost * 0.4; // More for food/experiences
        break;
      case "balanced":
      default:
        activityCost = dailyBaseCost * 0.4; // Balanced activities
        mealCost = dailyBaseCost * 0.3; // Balanced food
        break;
    }
    const accommodationCost = dailyBaseCost * 0.3; // Consistent for accommodation

    // Calculate the specific date for the current day
    const currentDayDate = new Date(trip.start_date); // Start with the trip's start date
    currentDayDate.setDate(currentDayDate.getDate() + dayNumber - 1); // Add days

    // Helper to generate slightly randomized coordinates
    const randomCoord = (base) => ({
      lat: base.lat + (Math.random() - 0.5) * 0.1,
      lng: base.lng + (Math.random() - 0.5) * 0.1,
    });

    // Dynamic activity and meal selection
    const activityPool = activityPools[focus] || activityPools.balanced;
    const activity1 = getRandomItem(activityPool);
    let activity2 = getRandomItem(activityPool);
    // Ensure two different activities unless the pool is too small
    while (activity1 === activity2 && activityPool.length > 1) {
      activity2 = getRandomItem(activityPool);
    }

    // Get unique restaurants for this day from the dynamic pool
    const lunchRestaurant = getUniqueRestaurant();
    const dinnerRestaurant = getUniqueRestaurant();

    return {
      day_number: dayNumber,
      date: currentDayDate.toISOString().split("T")[0], // Format YYYY-MM-DD
      activities: [
        {
          time: "10:00",
          activity: activity1.name,
          category: activity1.category,
          location: trip.destination,
          duration: "3 hours",
          cost: activityCost / 2, // Distribute activity cost over multiple activities
          description: `Experience the best of ${activity1.category.toLowerCase()} in ${
            trip.destination
          }.`,
          coordinates: randomCoord(baseCoords),
        },
        {
          time: "14:00",
          activity: activity2.name,
          category: activity2.category,
          location: trip.destination,
          duration: "2 hours",
          cost: activityCost / 2,
          description: `Discover ${activity2.category.toLowerCase()} attractions in ${
            trip.destination
          }.`,
          coordinates: randomCoord(baseCoords),
        },
      ],
      meals: [
        {
          meal_type: "lunch",
          restaurant: lunchRestaurant,
          cuisine: getRandomItem(restaurantPools.cuisines),
          cost: mealCost / 2, // Distribute meal cost over multiple meals
          location: trip.destination,
          coordinates: randomCoord(baseCoords),
        },
        {
          meal_type: "dinner",
          restaurant: dinnerRestaurant,
          cuisine: getRandomItem(restaurantPools.cuisines),
          cost: mealCost / 2, // Distribute meal cost over multiple meals
          location: trip.destination,
          coordinates: randomCoord(baseCoords),
        },
      ],
      accommodation: {
        name: `${
          trip.accommodation_preference.charAt(0).toUpperCase() +
          trip.accommodation_preference.slice(1)
        } Resort ${trip.destination}`,
        type: trip.accommodation_preference,
        cost: accommodationCost,
        location: trip.destination,
        coordinates: randomCoord(baseCoords),
      },
    };
  };

  const calculateTotalCost = (itineraries) => {
    return itineraries.reduce((sum, day) => {
      const dayTotal =
        (day.activities?.reduce((s, a) => s + (a.cost || 0), 0) || 0) +
        (day.meals?.reduce((s, m) => s + (m.cost || 0), 0) || 0) +
        (day.accommodation?.cost || 0);
      return sum + dayTotal;
    }, 0);
  };

  const getDescription = (focus) => {
    switch (focus) {
      case "adventure":
        return "An exhilarating journey filled with thrilling activities and nature exploration.";
      case "cultural":
        return "Immerse yourself in local traditions, history, and culinary delights.";
      case "balanced":
        return "A perfect blend of sightseeing, relaxation, and local experiences.";
      default:
        return "A unique travel experience tailored to your preferences.";
    }
  };

  const getTags = (focus) => {
    switch (focus) {
      case "adventure":
        return ["Adventure", "Nature", "Thrill", "Exploration"];
      case "cultural":
        return ["Culture", "History", "Food", "Heritage"];
      case "balanced":
        return ["Relaxation", "Sightseeing", "Shopping", "Local Life"];
      default:
        return ["Travel", "Discovery"];
    }
  };

  const options = ["balanced", "adventure", "cultural"].map((type) => {
    // Clear used restaurants for each option generation
    usedRestaurants.clear();

    const daily_itineraries = Array.from({ length: duration }, (_, i) =>
      generateDailyItinerary(i + 1, type)
    );
    return {
      id: type, // Unique ID for the option
      name: `${type.charAt(0).toUpperCase() + type.slice(1)} Explorer`,
      focus: `${type.charAt(0).toUpperCase() + type.slice(1)} Focus`,
      description: getDescription(type),
      total_estimated_cost: Math.round(calculateTotalCost(daily_itineraries)),
      daily_itineraries: daily_itineraries,
      tags: getTags(type),
    };
  });

  return options;
};

const steps = [
  "Destination",
  "Dates",
  "Budget",
  "Travelers",
  "Interests",
  "Preferences",
];

const getStepComponent = (step, formData, updateFormData) => {
  switch (step) {
    case 1:
      return (
        <DestinationStep formData={formData} updateFormData={updateFormData} />
      );
    case 2:
      return <DateStep formData={formData} updateFormData={updateFormData} />;
    case 3:
      return <BudgetStep formData={formData} updateFormData={updateFormData} />;
    case 4:
      return (
        <TravelersStep formData={formData} updateFormData={updateFormData} />
      );
    case 5:
      return (
        <InterestsStep formData={formData} updateFormData={updateFormData} />
      );
    case 6:
      return (
        <PreferenceStep formData={formData} updateFormData={updateFormData} />
      );
    default:
      return null;
  }
};

export default function TripForm() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    destination: "",
    start_date: "",
    end_date: "",
    total_budget: "", // Changed to empty to not count as complete initially
    currency: "INR",
    travelers: 1, // Set to 1 as a sensible default
    themes: [],
    accommodation_preference: "", // Changed to empty
    transportation_preference: "", // Changed to empty
    special_requirements: "",
  });
  const [error, setError] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Check for destination in URL parameters on component mount
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const destinationFromUrl = urlParams.get("destination");
    if (destinationFromUrl) {
      setFormData((prev) => ({
        ...prev,
        destination: decodeURIComponent(destinationFromUrl),
      }));
    }
  }, []);

  const updateFormData = (data) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        return formData.destination.trim() !== "";
      case 2:
        return formData.start_date && formData.end_date;
      case 3:
        const budget = parseFloat(formData.total_budget);
        return !isNaN(budget) && budget > 0;
      case 4:
        const travelers = parseInt(formData.travelers, 10);
        return !isNaN(travelers) && travelers > 0;
      case 5:
        return (
          formData.themes &&
          formData.themes.length >= 3 &&
          formData.themes.length <= 5
        );
      case 6:
        return (
          formData.accommodation_preference &&
          formData.transportation_preference
        );
      default:
        return false;
    }
  };

  const isStepValid = validateStep(currentStep);

  const generateAndNavigate = async () => {
    if (!isStepValid) return;
    setIsGenerating(true);
    setError("");

    try {
      // Create the trip first
      const tripData = {
        destination: formData.destination,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        total_budget: parseFloat(formData.total_budget),
        currency: formData.currency,
        travelers: parseInt(formData.travelers, 10),
        themes: formData.themes,
        accommodation_preference: formData.accommodation_preference,
        transportation_preference: formData.transportation_preference,
        food_preference: "mixed", // Default value
        special_requirements: formData.special_requirements,
      };

      console.log("Creating trip with data:", tripData);
      const createdTrip = await tripService.createTrip(tripData);
      console.log("Trip created successfully:", createdTrip);

      // Generate trip options using AI
      console.log("Generating trip options...");
      const tripOptions = await tripService.generateTripOptions(
        createdTrip.id,
        {}
      );
      console.log("Trip options generated:", tripOptions);

      // Navigate to trip options page
      navigate(`/trip-options?trip_id=${createdTrip.id}`);
    } catch (err) {
      console.error("Error creating trip:", err);
      setError(
        t("generateItineraryError") + (err.message ? `: ${err.message}` : "")
      );
      setIsGenerating(false);
    }
  };

  const handleContinue = () => {
    if (isStepValid) {
      if (currentStep === steps.length) {
        generateAndNavigate();
      } else {
        nextStep();
      }
    }
  };

  if (isGenerating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <Card className="w-full max-w-md mx-4 border-0 shadow-lg bg-white">
          <CardContent className="p-8 text-center">
            <div className="w-20 h-20 bg-gradient-to-r from-slate-400 to-slate-500 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-3">
              {t("creatingYourPerfectTrip")}
            </h3>
            <p className="text-slate-600 mb-8 leading-relaxed">
              {t("aiCraftingItinerary")}
            </p>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-center gap-3 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
                <span>{t("analyzingPreferences")}</span>
              </div>
              <div className="flex items-center justify-center gap-3 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
                <span>{t("findingBestAttractions")}</span>
              </div>
              <div className="flex items-center justify-center gap-3 text-emerald-600">
                <CheckCircle className="w-4 h-4" />
                <span>{t("optimizingBudget")}</span>
              </div>
              <div className="flex items-center justify-center gap-3 text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t("finalizingItinerary")}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl lg:text-4xl font-bold text-slate-800">
            {t("planYourPerfectTrip")}
          </h1>
          <p className="text-slate-600 mt-1">{t("letsCreateItinerary")}</p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            {getStepComponent(currentStep, formData, updateFormData)}
          </motion.div>
        </AnimatePresence>

        <div className="mt-12 flex justify-between items-center">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={currentStep === 1}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>

          <Button
            onClick={handleContinue}
            disabled={!isStepValid}
            className="gap-2 bg-slate-800 hover:bg-slate-900"
          >
            {currentStep === steps.length ? t("createMyTrip") : t("continue")}
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
