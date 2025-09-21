// Trip entity and related utilities

export const TripSchema = {
  name: "Trip",
  type: "object",
  properties: {
    destination: {
      type: "string",
      description: "Travel destination city/state in India",
    },
    start_date: {
      type: "string",
      format: "date",
      description: "Trip start date",
    },
    end_date: {
      type: "string",
      format: "date",
      description: "Trip end date",
    },
    total_budget: {
      type: "number",
      description: "Total budget for the trip in INR",
    },
    travelers: {
      type: "number",
      description: "Number of travelers",
    },
    interests: {
      type: "array",
      items: {
        type: "string",
      },
      description: "Travel interests and activities",
    },
    preferences: {
      type: "object",
      properties: {
        accommodation_type: {
          type: "string",
          enum: ["budget", "mid-range", "luxury"],
        },
        transport_preference: {
          type: "string",
          enum: ["public", "private", "mixed"],
        },
        food_preference: {
          type: "string",
          enum: ["local", "international", "mixed"],
        },
      },
    },
  },
  required: [
    "destination",
    "start_date",
    "end_date",
    "total_budget",
    "travelers",
  ],
};

// Default trip data structure
export const createDefaultTrip = () => ({
  destination: "",
  start_date: "",
  end_date: "",
  total_budget: 0,
  travelers: 1,
  interests: [],
  preferences: {
    accommodation_type: "mid-range",
    transport_preference: "mixed",
    food_preference: "mixed",
  },
});

// Trip validation function
export const validateTrip = (trip) => {
  const errors = [];

  if (!trip.destination || trip.destination.trim() === "") {
    errors.push("Destination is required");
  }

  if (!trip.start_date) {
    errors.push("Start date is required");
  }

  if (!trip.end_date) {
    errors.push("End date is required");
  }

  if (trip.start_date && trip.end_date) {
    const startDate = new Date(trip.start_date);
    const endDate = new Date(trip.end_date);

    if (startDate >= endDate) {
      errors.push("End date must be after start date");
    }
  }

  if (!trip.total_budget || trip.total_budget <= 0) {
    errors.push("Total budget must be greater than 0");
  }

  if (!trip.travelers || trip.travelers < 1) {
    errors.push("Number of travelers must be at least 1");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Mock trip data storage (in a real app, this would be API calls)
let mockTrips = [];

// Trip service methods
export const TripService = {
  create: async (tripData) => {
    const trip = {
      id: Date.now().toString(),
      ...tripData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockTrips.push(trip);
    return trip;
  },

  update: async (id, updateData) => {
    const index = mockTrips.findIndex((trip) => trip.id === id);
    if (index !== -1) {
      mockTrips[index] = {
        ...mockTrips[index],
        ...updateData,
        updated_at: new Date().toISOString(),
      };
      return mockTrips[index];
    }
    throw new Error("Trip not found");
  },

  delete: async (id) => {
    const index = mockTrips.findIndex((trip) => trip.id === id);
    if (index !== -1) {
      mockTrips.splice(index, 1);
      return true;
    }
    throw new Error("Trip not found");
  },

  list: async (sortBy = "-created_at") => {
    return [...mockTrips].sort((a, b) => {
      if (sortBy.startsWith("-")) {
        const field = sortBy.substring(1);
        return new Date(b[field]) - new Date(a[field]);
      }
      return new Date(a[sortBy]) - new Date(b[sortBy]);
    });
  },

  filter: async (filters) => {
    return mockTrips.filter((trip) => {
      return Object.entries(filters).every(([key, value]) => {
        return trip[key] === value;
      });
    });
  },

  getById: async (id) => {
    return mockTrips.find((trip) => trip.id === id);
  },
};

// Create a Trip object that includes the service methods
export const Trip = {
  ...TripSchema,
  create: TripService.create,
  update: TripService.update,
  delete: TripService.delete,
  list: TripService.list,
  filter: TripService.filter,
  getById: TripService.getById,
};

export default Trip;
