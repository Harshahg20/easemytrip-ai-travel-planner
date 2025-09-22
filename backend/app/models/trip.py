from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(String(255), primary_key=True, index=True)
    destination = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_budget = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    travelers = Column(Integer, nullable=False)
    themes = Column(JSON)  # List of themes like ["adventure", "cultural"]
    
    # Preferences
    accommodation_preference = Column(String(50), default="mid-range")
    transportation_preference = Column(String(50), default="mixed")
    food_preference = Column(String(50), default="mixed")
    special_requirements = Column(Text)
    
    # Status and metadata
    status = Column(String(50), default="draft")  # draft, planned, booked, completed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    daily_itineraries = relationship("DailyItinerary", back_populates="trip", cascade="all, delete-orphan")
    trip_options = relationship("TripOption", back_populates="trip", cascade="all, delete-orphan")


class DailyItinerary(Base):
    __tablename__ = "daily_itineraries"
    
    id = Column(String(255), primary_key=True, index=True)
    trip_id = Column(String(255), ForeignKey("trips.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    daily_budget = Column(Float)
    
    # Activities, meals, accommodation stored as JSON
    activities = Column(JSON)  # List of activity objects
    meals = Column(JSON)  # List of meal objects
    accommodation = Column(JSON)  # Accommodation object
    transport = Column(JSON)  # Transport details
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    trip = relationship("Trip", back_populates="daily_itineraries")


class TripOption(Base):
    __tablename__ = "trip_options"
    
    id = Column(String(255), primary_key=True, index=True)
    trip_id = Column(String(255), ForeignKey("trips.id"), nullable=False)
    option_name = Column(String(255), nullable=False)  # e.g., "Adventure", "Cultural", "Balanced"
    theme = Column(String(50), nullable=False)  # adventure, cultural, balanced
    description = Column(Text)
    
    # Option details stored as JSON
    daily_itineraries = Column(JSON)  # Complete daily itineraries for this option
    total_cost = Column(Float)
    highlights = Column(JSON)  # List of highlights
    
    is_selected = Column(String(10), default="False")  # True if this is the selected option
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    trip = relationship("Trip", back_populates="trip_options")
