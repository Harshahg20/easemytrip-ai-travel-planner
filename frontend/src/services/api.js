import axios from "axios";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  timeout: 120000, // 120 seconds (2 minutes) timeout for AI operations
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log request in development
    if (process.env.NODE_ENV === "development") {
      console.log("🚀 API Request:", {
        method: config.method?.toUpperCase(),
        url: config.url,
        data: config.data,
      });
    }

    return config;
  },
  (error) => {
    console.error("❌ Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Log response in development
    if (process.env.NODE_ENV === "development") {
      console.log("✅ API Response:", {
        status: response.status,
        url: response.config.url,
        data: response.data,
      });
    }

    return response;
  },
  (error) => {
    console.error("❌ Response Error:", error);

    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          localStorage.removeItem("auth_token");
          window.location.href = "/login";
          break;
        case 403:
          console.error("Access forbidden");
          break;
        case 404:
          console.error("Resource not found");
          break;
        case 500:
          console.error("Internal server error");
          break;
        default:
          console.error(
            `API Error ${status}:`,
            data?.message || "Unknown error"
          );
      }
    } else if (error.request) {
      // Network error
      console.error("Network Error:", error.message);
    } else {
      // Other error
      console.error("Error:", error.message);
    }

    return Promise.reject(error);
  }
);

// API service functions
export const tripService = {
  // Create a new trip
  createTrip: async (tripData) => {
    try {
      const response = await api.post("/trips/", tripData);
      return response.data;
    } catch (error) {
      console.error("Error creating trip:", error);
      throw error;
    }
  },

  // Get destination photos using Google Places Photos API
  getDestinationPhotos: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/photos`);
      return response.data;
    } catch (error) {
      console.error("Error fetching destination photos:", error);
      throw error;
    }
  },

  // Geocode a place (scoped to trip destination)
  geocodePlace: async (tripId, query) => {
    try {
      const response = await api.get(`/trips/${tripId}/geocode`, {
        params: { q: query },
      });
      return response.data; // { lat, lng }
    } catch (error) {
      console.error("Error geocoding place:", error);
      throw error;
    }
  },
  // Get trip by ID
  getTrip: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}`);
      return response.data;
    } catch (error) {
      console.error("Error fetching trip:", error);
      throw error;
    }
  },

  // Update trip
  updateTrip: async (tripId, updateData) => {
    try {
      const response = await api.put(`/trips/${tripId}`, updateData);
      return response.data;
    } catch (error) {
      console.error("Error updating trip:", error);
      throw error;
    }
  },

  // Delete trip
  deleteTrip: async (tripId) => {
    try {
      const response = await api.delete(`/trips/${tripId}`);
      return response.data;
    } catch (error) {
      console.error("Error deleting trip:", error);
      throw error;
    }
  },

  // List all trips
  listTrips: async (params = {}) => {
    try {
      const response = await api.get("/trips/", { params });
      return response.data;
    } catch (error) {
      console.error("Error listing trips:", error);
      throw error;
    }
  },

  // Generate trip options using AI
  generateTripOptions: async (tripId, optionsRequest = {}) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/generate-options`,
        optionsRequest,
        {
          timeout: 180000, // 3 minutes timeout for AI generation
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error generating trip options:", error);
      throw error;
    }
  },

  // Generate optimized trip options using hybrid loading strategy
  generateOptimizedTripOptions: async (tripId, optionsRequest = {}) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/generate-optimized`,
        optionsRequest,
        {
          timeout: 300000, // 5 minutes timeout for optimized generation
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error generating optimized trip options:", error);
      throw error;
    }
  },

  // Generate single day itinerary (lazy loading)
  generateDayItinerary: async (
    tripId,
    dayNumber,
    optionId = null,
    language = "english"
  ) => {
    try {
      // Build URL with language query parameter
      const url = `/trips/${tripId}/generate-day/${dayNumber}${
        language && language !== "english"
          ? `?language=${encodeURIComponent(language)}`
          : ""
      }`;
      const response = await api.post(
        url,
        { option_id: optionId },
        {
          timeout: 120000, // 2 minutes timeout for single day generation
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error generating day itinerary:", error);
      throw error;
    }
  },

  // Get trip options
  getTripOptions: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/options`);
      return response.data;
    } catch (error) {
      console.error("Error fetching trip options:", error);
      throw error;
    }
  },

  // Select a trip option
  selectTripOption: async (tripId, optionId) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/select-option/${optionId}`
      );
      return response.data;
    } catch (error) {
      console.error("Error selecting trip option:", error);
      throw error;
    }
  },

  // Get trip itinerary
  getTripItinerary: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/itinerary`);
      return response.data;
    } catch (error) {
      console.error("Error fetching trip itinerary:", error);
      throw error;
    }
  },

  // Get travel recommendations
  getTravelRecommendations: async (tripId) => {
    try {
      const response = await api.post(`/trips/${tripId}/recommendations`);
      return response.data;
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      throw error;
    }
  },

  // Search places
  searchPlaces: async (tripId, query, placeType = null) => {
    try {
      const response = await api.post(`/trips/${tripId}/places/search`, {
        query,
        place_type: placeType,
      });
      return response.data;
    } catch (error) {
      console.error("Error searching places:", error);
      throw error;
    }
  },

  // Get smart adjustments for a specific day
  getSmartAdjustments: async (tripId, dayNumber) => {
    try {
      const response = await api.get(
        `/trips/${tripId}/smart-adjustments/${dayNumber}`
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching smart adjustments:", error);
      throw error;
    }
  },

  // Adjust itinerary based on weather/traffic conditions
  adjustItinerary: async (
    tripId,
    dayNumber,
    adjustmentType,
    adjustmentData
  ) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/adjust-itinerary/${dayNumber}`,
        {
          adjustment_type: adjustmentType,
          adjustment_data: adjustmentData,
        },
        {
          timeout: 180000, // 3 minutes timeout for AI adjustment
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error adjusting itinerary:", error);
      throw error;
    }
  },

  // Get transport details (local/city transport) based on budget and total days
  getTransportDetails: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/transport-details`, {
        timeout: 120000, // 2 minutes timeout for AI generation
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching transport details:", error);
      throw error;
    }
  },

  // Get travel details (inter-city travel: flights, trains, buses) based on budget and total days
  getTravelDetails: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/travel-details`, {
        timeout: 120000, // 2 minutes timeout for AI generation
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching travel details:", error);
      throw error;
    }
  },

  // Get booking prices for flights and car rentals based on travel/transport data
  getBookingPrices: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/booking-prices`, {
        timeout: 120000, // 2 minutes timeout
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching booking prices:", error);
      throw error;
    }
  },

  // Translate content
  translateContent: async (content, targetLanguage, sourceLanguage = null) => {
    try {
      const response = await api.post("/trips/translate", {
        content,
        target_language: targetLanguage,
        source_language: sourceLanguage,
      });
      return response.data.translated;
    } catch (error) {
      console.error("Error translating content:", error);
      throw error;
    }
  },

  // Translate itinerary
  translateItinerary: async (itinerary, targetLanguage) => {
    try {
      const response = await api.post("/trips/translate/itinerary", {
        itinerary,
        target_language: targetLanguage,
      });
      return response.data.translated;
    } catch (error) {
      console.error("Error translating itinerary:", error);
      throw error;
    }
  },

  // Translate list of texts
  translateTexts: async (texts, targetLanguage, sourceLanguage = null) => {
    try {
      const response = await api.post("/trips/translate/texts", {
        texts,
        target_language: targetLanguage,
        source_language: sourceLanguage,
      });
      return response.data.translated;
    } catch (error) {
      console.error("Error translating texts:", error);
      throw error;
    }
  },

  // Translate cached content in batches by content type
  translateCachedContent: async (tripId, contentTypes, targetLanguage) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/translate-cached`,
        {
          content_types: contentTypes,
          target_language: targetLanguage,
        },
        {
          timeout: 180000, // 3 minutes timeout for batch translation
        }
      );
      return response.data.translated_content;
    } catch (error) {
      console.error("Error translating cached content:", error);
      throw error;
    }
  },

  // Translate all daily itineraries for a trip
  translateDailyItineraries: async (tripId, targetLanguage) => {
    try {
      const response = await api.post(
        `/trips/${tripId}/translate-daily-itineraries`,
        {
          target_language: targetLanguage,
        },
        {
          timeout: 180000, // 3 minutes timeout for batch translation
        }
      );
      return response.data.translated_itineraries;
    } catch (error) {
      console.error("Error translating daily itineraries:", error);
      throw error;
    }
  },

  // Get cache statistics for a trip
  getCacheStats: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/cache-stats`);
      return response.data;
    } catch (error) {
      console.error("Error fetching cache stats:", error);
      throw error;
    }
  },

  // Get or generate trip structure (main places per day)
  getTripStructure: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/trip-structure`);
      return response.data;
    } catch (error) {
      console.error("Error fetching trip structure:", error);
      throw error;
    }
  },
};

export default api;
