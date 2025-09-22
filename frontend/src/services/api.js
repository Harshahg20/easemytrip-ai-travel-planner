import axios from "axios";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000, // 30 seconds timeout
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
        optionsRequest
      );
      return response.data;
    } catch (error) {
      console.error("Error generating trip options:", error);
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
};

export default api;
