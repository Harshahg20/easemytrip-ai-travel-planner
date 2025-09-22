from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TripCreate(BaseModel):
    destination: str = Field(..., description="Travel destination")
    start_date: datetime = Field(..., description="Trip start date")
    end_date: datetime = Field(..., description="Trip end date")
    total_budget: float = Field(..., description="Total budget for the trip")
    currency: str = Field(default="INR", description="Currency code")
    travelers: int = Field(..., ge=1, description="Number of travelers")
    themes: Optional[List[str]] = Field(default=[], description="Travel themes/interests")
    accommodation_preference: str = Field(default="mid-range", description="Accommodation preference")
    transportation_preference: str = Field(default="mixed", description="Transportation preference")
    food_preference: str = Field(default="mixed", description="Food preference")
    special_requirements: Optional[str] = Field(default=None, description="Special requirements")


class TripUpdate(BaseModel):
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = None
    currency: Optional[str] = None
    travelers: Optional[int] = None
    themes: Optional[List[str]] = None
    accommodation_preference: Optional[str] = None
    transportation_preference: Optional[str] = None
    food_preference: Optional[str] = None
    special_requirements: Optional[str] = None
    status: Optional[str] = None


class TripOptionResponse(BaseModel):
    id: str
    trip_id: str
    option_name: str
    theme: str
    description: Optional[str]
    daily_itineraries: Optional[List[Dict[str, Any]]]
    total_cost: Optional[float]
    highlights: Optional[List[str]]
    is_selected: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripResponse(BaseModel):
    id: str
    destination: str
    start_date: datetime
    end_date: datetime
    total_budget: float
    currency: str
    travelers: int
    themes: Optional[List[str]]
    accommodation_preference: str
    transportation_preference: str
    food_preference: str
    special_requirements: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    selected_option: Optional[TripOptionResponse] = None

    class Config:
        from_attributes = True


class ActivitySchema(BaseModel):
    time: str = Field(..., description="Activity time")
    activity: str = Field(..., description="Activity name")
    location: str = Field(..., description="Activity location")
    duration: str = Field(..., description="Activity duration")
    cost: float = Field(..., description="Activity cost")
    description: str = Field(..., description="Activity description")
    category: str = Field(..., description="Activity category")
    coordinates: Optional[Dict[str, float]] = Field(default=None, description="Coordinates")


class MealSchema(BaseModel):
    meal_type: str = Field(..., description="Type of meal")
    restaurant: str = Field(..., description="Restaurant name")
    cost: float = Field(..., description="Meal cost")
    cuisine: str = Field(..., description="Cuisine type")
    location: Optional[str] = Field(default=None, description="Restaurant location")
    time: Optional[str] = Field(default=None, description="Meal time")


class AccommodationSchema(BaseModel):
    name: str = Field(..., description="Accommodation name")
    type: str = Field(..., description="Accommodation type")
    cost: float = Field(..., description="Accommodation cost")
    location: str = Field(..., description="Accommodation location")
    amenities: Optional[List[str]] = Field(default=[], description="Available amenities")


class TransportSchema(BaseModel):
    mode: str = Field(..., description="Transport mode")
    cost: float = Field(..., description="Transport cost")
    duration: str = Field(..., description="Transport duration")
    route: Optional[str] = Field(default=None, description="Route description")


class DailyItineraryResponse(BaseModel):
    id: str
    trip_id: str
    day_number: int
    date: datetime
    daily_budget: Optional[float]
    activities: Optional[List[Dict[str, Any]]]
    meals: Optional[List[Dict[str, Any]]]
    accommodation: Optional[Dict[str, Any]]
    transport: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripOptionsGenerate(BaseModel):
    force_regenerate: bool = Field(default=False, description="Force regeneration of options")


class PlaceSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    place_type: Optional[str] = Field(default=None, description="Type of place to search")
    radius: int = Field(default=5000, description="Search radius in meters")


class PlaceSearchResponse(BaseModel):
    places: List[Dict[str, Any]]
    destination: str


class RecommendationsResponse(BaseModel):
    destination: str
    attractions: List[Dict[str, Any]]
    restaurants: List[Dict[str, Any]]
    accommodation: List[Dict[str, Any]]
    transportation: Dict[str, Any]
    best_time: str
    budget_estimate: Dict[str, str]
    tips: List[str]


class DirectionsRequest(BaseModel):
    origin: str = Field(..., description="Starting point")
    destination: str = Field(..., description="Destination point")
    mode: str = Field(default="driving", description="Travel mode")


class DirectionsResponse(BaseModel):
    distance: str
    duration: str
    start_address: str
    end_address: str
    steps: List[Dict[str, Any]]
    overview_polyline: str
