from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.trip import Trip, DailyItinerary, TripOption
from ...services.google_ai_service import google_ai_service
from ...services.google_maps_service import google_maps_service
from ..schemas.trip import (
    TripCreate, TripResponse, TripUpdate,
    TripOptionResponse, DailyItineraryResponse,
    TripOptionsGenerate
)

router = APIRouter()


@router.post("/", response_model=TripResponse)
async def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    """Create a new trip"""
    try:
        # Create trip record
        trip_id = str(uuid.uuid4())
        db_trip = Trip(
            id=trip_id,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            total_budget=trip_data.total_budget,
            currency=trip_data.currency,
            travelers=trip_data.travelers,
            themes=trip_data.themes,
            accommodation_preference=trip_data.accommodation_preference,
            transportation_preference=trip_data.transportation_preference,
            food_preference=trip_data.food_preference,
            special_requirements=trip_data.special_requirements,
            status="draft"
        )
        
        db.add(db_trip)
        db.commit()
        db.refresh(db_trip)
        
        return db_trip
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating trip: {str(e)}"
        )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, db: Session = Depends(get_db)):
    """Get trip by ID"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    return trip


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str, 
    trip_update: TripUpdate, 
    db: Session = Depends(get_db)
):
    """Update trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Update fields
    update_data = trip_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    
    trip.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(trip)
    return trip


@router.delete("/{trip_id}")
async def delete_trip(trip_id: str, db: Session = Depends(get_db)):
    """Delete trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    db.delete(trip)
    db.commit()
    return {"message": "Trip deleted successfully"}


@router.get("/", response_model=List[TripResponse])
async def list_trips(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all trips with optional filtering"""
    query = db.query(Trip)
    
    if status:
        query = query.filter(Trip.status == status)
    
    trips = query.offset(skip).limit(limit).all()
    return trips


@router.post("/{trip_id}/generate-options", response_model=List[TripOptionResponse])
async def generate_trip_options(
    trip_id: str, 
    options_request: TripOptionsGenerate,
    db: Session = Depends(get_db)
):
    """Generate multiple trip options using AI"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Prepare trip data for AI
        trip_data = {
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "total_budget": trip.total_budget,
            "travelers": trip.travelers,
            "themes": trip.themes or [],
            "accommodation_preference": trip.accommodation_preference,
            "transportation_preference": trip.transportation_preference,
            "food_preference": trip.food_preference,
            "special_requirements": trip.special_requirements,
            "duration": (trip.end_date - trip.start_date).days + 1
        }
        
        # Generate options using AI
        ai_options = await google_ai_service.generate_trip_options(trip_data)
        
        # Save options to database
        saved_options = []
        for option_data in ai_options:
            option_id = str(uuid.uuid4())
            db_option = TripOption(
                id=option_id,
                trip_id=trip_id,
                option_name=option_data.get("option_name", "Generated Option"),
                theme=option_data.get("theme", "balanced"),
                description=option_data.get("description", ""),
                daily_itineraries=option_data.get("daily_itineraries", []),
                total_cost=option_data.get("total_cost", trip.total_budget * 0.8),
                highlights=option_data.get("highlights", [])
            )
            
            db.add(db_option)
            saved_options.append(db_option)
        
        db.commit()
        
        # Refresh all options
        for option in saved_options:
            db.refresh(option)
        
        return saved_options
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating trip options: {str(e)}"
        )


@router.get("/{trip_id}/options", response_model=List[TripOptionResponse])
async def get_trip_options(trip_id: str, db: Session = Depends(get_db)):
    """Get all options for a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    options = db.query(TripOption).filter(TripOption.trip_id == trip_id).all()
    return options


@router.post("/{trip_id}/select-option/{option_id}")
async def select_trip_option(trip_id: str, option_id: str, db: Session = Depends(get_db)):
    """Select a trip option and create daily itineraries"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    option = db.query(TripOption).filter(
        TripOption.id == option_id,
        TripOption.trip_id == trip_id
    ).first()
    
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip option not found"
        )
    
    try:
        # Mark this option as selected
        option.is_selected = True
        
        # Create daily itineraries from the selected option
        daily_itineraries_data = option.daily_itineraries or []
        
        # Clear existing daily itineraries
        db.query(DailyItinerary).filter(DailyItinerary.trip_id == trip_id).delete()
        
        # Create new daily itineraries
        for day_data in daily_itineraries_data:
            itinerary_id = str(uuid.uuid4())
            db_itinerary = DailyItinerary(
                id=itinerary_id,
                trip_id=trip_id,
                day_number=day_data.get("day_number", 1),
                date=datetime.fromisoformat(day_data.get("date", trip.start_date.isoformat())),
                daily_budget=day_data.get("daily_budget", trip.total_budget / len(daily_itineraries_data)),
                activities=day_data.get("activities", []),
                meals=day_data.get("meals", []),
                accommodation=day_data.get("accommodation", {}),
                transport=day_data.get("transport", {})
            )
            db.add(db_itinerary)
        
        # Update trip status
        trip.status = "planned"
        trip.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Trip option selected successfully", "option_id": option_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error selecting trip option: {str(e)}"
        )


@router.get("/{trip_id}/itinerary", response_model=List[DailyItineraryResponse])
async def get_trip_itinerary(trip_id: str, db: Session = Depends(get_db)):
    """Get daily itinerary for a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    itineraries = db.query(DailyItinerary).filter(
        DailyItinerary.trip_id == trip_id
    ).order_by(DailyItinerary.day_number).all()
    
    return itineraries


@router.post("/{trip_id}/recommendations")
async def get_travel_recommendations(
    trip_id: str, 
    db: Session = Depends(get_db)
):
    """Get travel recommendations for a trip destination"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Get recommendations using AI
        recommendations = await google_ai_service.get_travel_recommendations(
            destination=trip.destination,
            interests=trip.themes or []
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.post("/{trip_id}/places/search")
async def search_places(
    trip_id: str,
    query: str,
    place_type: str = None,
    db: Session = Depends(get_db)
):
    """Search for places near the trip destination"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Get coordinates for the destination
        coordinates = await google_maps_service.geocode_address(trip.destination)
        
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find coordinates for destination"
            )
        
        # Search for places
        places = await google_maps_service.search_places(
            query=query,
            location=coordinates,
            place_type=place_type
        )
        
        return {"places": places, "destination": trip.destination}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching places: {str(e)}"
        )
