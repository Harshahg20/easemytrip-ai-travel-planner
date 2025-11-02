from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timedelta
import asyncio
import base64
import httpx
import json
import hashlib

logger = logging.getLogger(__name__)

from ...core.database import get_db
from ...core.auth import get_current_active_user, get_user_or_guest
from ...models.trip import Trip, DailyItinerary, TripOption, TripContentCache
from ...models.user import User
from ...services.google_ai_service import google_ai_service
from ...services.google_maps_service import google_maps_service
from ...services.smart_adjustments_service import smart_adjustments_service
from ...services.translation_service import translation_service
from ...services.content_cache_service import content_cache_service
from ...services.enhanced_translation_service import enhanced_translation_service
from ...core.config import settings
from ..schemas.trip import (
    TripCreate, TripResponse, TripUpdate,
    TripOptionResponse, DailyItineraryResponse,
    TripOptionsGenerate, PlaceSearchRequest, PlaceSearchResponse
)
from .trips_protected import verify_trip_ownership

router = APIRouter()


def _generate_content_hash(content: Any) -> str:
    """Generate hash for content"""
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode()).hexdigest()


async def _store_content_in_db(
    db: Session,
    trip_id: str,
    content_type: str,
    content: Any,
    ttl_hours: Optional[int] = None
):
    """
    Store content in database for persistent storage.
    Used for planned/booked trips to ensure content survives server restarts.
    """
    try:
        content_hash = _generate_content_hash(content)
        
        # Check if content already exists
        existing = db.query(TripContentCache).filter(
            TripContentCache.trip_id == trip_id,
            TripContentCache.content_type == content_type
        ).first()
        
        expires_at = None
        if ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        if existing:
            # Update existing content
            existing.content = content
            existing.content_hash = content_hash
            existing.updated_at = datetime.utcnow()
            existing.expires_at = expires_at
            logger.debug(f"Updated DB cache for {content_type} in trip {trip_id}")
        else:
            # Create new content cache entry
            cache_id = str(uuid.uuid4())
            new_cache = TripContentCache(
                id=cache_id,
                trip_id=trip_id,
                content_type=content_type,
                content=content,
                content_hash=content_hash,
                expires_at=expires_at
            )
            db.add(new_cache)
            logger.debug(f"Stored {content_type} in DB for trip {trip_id}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Error storing content in DB: {e}")
        db.rollback()


async def _get_content_from_db(
    db: Session,
    trip_id: str,
    content_type: str
) -> Optional[Any]:
    """
    Retrieve content from database.
    Returns None if not found or expired.
    """
    try:
        now = datetime.utcnow()
        cached = db.query(TripContentCache).filter(
            TripContentCache.trip_id == trip_id,
            TripContentCache.content_type == content_type,
            (TripContentCache.expires_at.is_(None)) | (TripContentCache.expires_at > now)
        ).first()
        
        if cached:
            logger.debug(f"Retrieved {content_type} from DB for trip {trip_id}")
            return cached.content
        
        return None
    except Exception as e:
        logger.warning(f"Error retrieving content from DB: {e}")
        return None


async def _precache_travel_and_transport(
    trip_id: str,
    trip_data: Dict[str, Any],
    translation_service
):
    """
    Background task to pre-cache travel and transport details when trip becomes planned.
    This ensures content is ready for translation requests.
    Stores in both in-memory cache and database.
    Creates a new DB session for background task.
    """
    # Get a new database session for background task
    from ...core.database import SessionLocal
    db = SessionLocal()
    
    try:
        logger.info(f"Pre-caching travel and transport details for trip {trip_id}")
        
        # Generate and cache travel details
        travel_details = await google_ai_service.generate_travel_details(trip_data)
        
        # Store in in-memory cache
        await translation_service.cache_api_response(
            trip_id=trip_id,
            content_type="travel_details",
            content=travel_details,
            ttl_hours=168  # 7 days cache for planned trips
        )
        
        # Store in database
        await _store_content_in_db(db, trip_id, "travel_details", travel_details, ttl_hours=168)
        
        logger.info(f"Pre-cached travel details for trip {trip_id}")
        
        # Generate and cache transport details
        transport_details = await google_ai_service.generate_transport_details(trip_data)
        
        # Store in in-memory cache
        await translation_service.cache_api_response(
            trip_id=trip_id,
            content_type="transport_details",
            content=transport_details,
            ttl_hours=168  # 7 days cache for planned trips
        )
        
        # Store in database
        await _store_content_in_db(db, trip_id, "transport_details", transport_details, ttl_hours=168)
        
        logger.info(f"Pre-cached transport details for trip {trip_id}")
        
    except Exception as e:
        logger.error(f"Error pre-caching travel/transport details for trip {trip_id}: {e}")
    finally:
        db.close()


@router.post("/", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_user_or_guest),
    db: Session = Depends(get_db)
):
    """Create a new trip (works with or without authentication)"""
    try:
        # Create trip record
        trip_id = str(uuid.uuid4())
        db_trip = Trip(
            id=trip_id,
            user_id=current_user.id,
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
    """Get trip by ID with selected option information"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Get the selected trip option if any
    # Note: is_selected is stored as a String ("True"/"False"), not boolean
    selected_option = db.query(TripOption).filter(
        TripOption.trip_id == trip_id,
        TripOption.is_selected == "True"
    ).first()
    
    # Convert selected_option to dict if it exists
    selected_option_dict = None
    if selected_option:
        # Convert is_selected from string ("True"/"False") to boolean
        is_selected_bool = selected_option.is_selected == "True" if isinstance(selected_option.is_selected, str) else bool(selected_option.is_selected)
        
        selected_option_dict = {
            "id": selected_option.id,
            "trip_id": selected_option.trip_id,
            "option_name": selected_option.option_name,
            "theme": selected_option.theme,
            "description": selected_option.description,
            "total_cost": selected_option.total_cost,
            "highlights": selected_option.highlights,
            "is_selected": is_selected_bool,
            "daily_itineraries": selected_option.daily_itineraries,
            "created_at": selected_option.created_at,
            "updated_at": selected_option.updated_at
        }
    
    # Convert trip to dict and add selected option
    trip_dict = {
        "id": trip.id,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "total_budget": trip.total_budget,
        "currency": trip.currency,
        "travelers": trip.travelers,
        "themes": trip.themes,
        "accommodation_preference": trip.accommodation_preference,
        "transportation_preference": trip.transportation_preference,
        "food_preference": trip.food_preference,
        "special_requirements": trip.special_requirements,
        "status": trip.status,
        "photos_base64": trip.photos_base64,  # Include cached photos if available
        "created_at": trip.created_at,
        "updated_at": trip.updated_at,
        "selected_option": selected_option_dict
    }
    
    return trip_dict


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
    options_request: TripOptionsGenerate = Body(default=TripOptionsGenerate()),
    db: Session = Depends(get_db)
):
    """Generate multiple trip options using AI with optional automatic translation"""
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
        
        # Generate options using AI with lazy loading (only first day)
        ai_options = await google_ai_service.generate_trip_options_lazy(trip_data)
        
        if not ai_options or len(ai_options) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate trip options"
            )
        
        # Store original (non-translated) content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="trip_options",
            content=ai_options,
            ttl_hours=24
        )
        
        # Automatically translate if language is specified and not English
        target_language = options_request.language or "english"
        if target_language.lower() != "english":
            logger.info(f"Translating trip options to {target_language}")
            translated_options = []
            for option in ai_options:
                translated_option = await translation_service.translate_itinerary(
                    option, target_language
                )
                translated_options.append(translated_option)
            ai_options = translated_options
        
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


@router.get("/{trip_id}/trip-structure", response_model=Dict[str, Any])
async def get_or_generate_trip_structure(trip_id: str, db: Session = Depends(get_db)):
    """Get or generate trip structure (main places per day) for ensuring diversity"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Check cache first
        cached_structure = await content_cache_service.get(trip_id, "trip_structure")
        
        if cached_structure:
            logger.info(f"Returning cached trip structure for trip {trip_id}")
            return {
                "trip_id": trip_id,
                "structure": cached_structure,
                "cached": True
            }
        
        # Prepare trip data
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
        
        logger.info(f"Generating trip structure for {trip_data['duration']}-day trip to {trip.destination}")
        
        # Generate trip structure
        structure = await google_ai_service.generate_trip_structure(trip_data)
        
        # Cache the structure
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="trip_structure",
            content=structure,
            ttl_hours=24
        )
        
        return {
            "trip_id": trip_id,
            "structure": structure,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Error generating trip structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating trip structure: {str(e)}"
        )


@router.post("/{trip_id}/generate-day/{day_number}", response_model=Dict[str, Any])
async def generate_single_day_itinerary(
    trip_id: str,
    day_number: int,
    option_id: str = None,
    language: str = Query(default="english", description="Target language for translation"),
    db: Session = Depends(get_db)
):
    """Generate itinerary for a specific day (lazy loading) with optional automatic translation"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    if day_number < 1 or day_number > (trip.end_date - trip.start_date).days + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid day number"
        )
    
    try:
        # Check cache first for this specific day
        content_type = f"daily_itinerary_{day_number}"
        cached_itinerary = await content_cache_service.get(trip_id, content_type)
        
        if cached_itinerary:
            logger.info(f"Found cached itinerary for day {day_number}, returning cached version")
            # Still translate if needed
            if language.lower() != "english":
                logger.info(f"Translating cached day {day_number} itinerary to {language}")
                cached_itinerary = await translation_service.translate_itinerary(
                    cached_itinerary, language
                )
            return {
                "day_number": day_number,
                "itinerary": cached_itinerary,
                "trip_id": trip_id,
                "cached": True
            }
        
        # Get or generate trip structure for diversity
        trip_structure = await content_cache_service.get(trip_id, "trip_structure")
        if not trip_structure:
            # Generate structure if not cached
            trip_data_for_structure = {
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
            trip_structure = await google_ai_service.generate_trip_structure(trip_data_for_structure)
            await content_cache_service.store(
                trip_id=trip_id,
                content_type="trip_structure",
                content=trip_structure,
                ttl_hours=24
            )
            logger.info(f"Generated and cached trip structure for trip {trip_id}")
        
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
            "duration": (trip.end_date - trip.start_date).days + 1,
            "day_number": day_number
        }
        
        logger.info(f"Generating NEW itinerary for day {day_number} of {trip_data['duration']}-day trip to {trip.destination}")
        
        # Generate single day itinerary using AI with trip structure
        day_itinerary = await google_ai_service.generate_daily_itinerary(trip_data, day_number, trip_structure)
        
        if not day_itinerary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate day itinerary"
            )
        
        # Store original (non-translated) content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type=f"daily_itinerary_{day_number}",
            content=day_itinerary,
            ttl_hours=24
        )
        
        # Automatically translate if language is specified and not English
        if language.lower() != "english":
            logger.info(f"Translating day {day_number} itinerary to {language}")
            day_itinerary = await translation_service.translate_itinerary(
                day_itinerary, language
            )
        
        return {
            "day_number": day_number,
            "itinerary": day_itinerary,
            "trip_id": trip_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating day itinerary: {str(e)}"
        )


@router.post("/{trip_id}/generate-optimized", response_model=List[Dict[str, Any]])
async def generate_optimized_trip_options(
    trip_id: str, 
    options_request: TripOptionsGenerate = Body(default=TripOptionsGenerate()),
    db: Session = Depends(get_db)
):
    """Generate trip options using hybrid loading strategy for optimal performance with optional automatic translation"""
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
        
        # Generate options using hybrid loading strategy
        ai_options = await google_ai_service.generate_optimized_trip_options(trip_data)
        
        if not ai_options or len(ai_options) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate optimized trip options"
            )
        
        # Store original (non-translated) content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="trip_options",
            content=ai_options,
            ttl_hours=24
        )
        
        # Automatically translate if language is specified and not English
        target_language = options_request.language or "english"
        if target_language.lower() != "english":
            logger.info(f"Translating optimized trip options to {target_language}")
            translated_options = []
            for option in ai_options:
                translated_option = await translation_service.translate_itinerary(
                    option, target_language
                )
                translated_options.append(translated_option)
            ai_options = translated_options
        
        logger.info(f"Successfully generated {len(ai_options)} optimized trip options")
        return ai_options
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating optimized trip options: {str(e)}"
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
async def select_trip_option(
    trip_id: str,
    option_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
        # Mark this option as selected (store as string "True")
        option.is_selected = "True"
        
        # Unselect all other options for this trip
        db.query(TripOption).filter(
            TripOption.trip_id == trip_id,
            TripOption.id != option_id
        ).update({"is_selected": "False"})
        
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
        
        # Set db session for enhanced translation service
        enhanced_translation_service.set_db(db)
        
        # After trip becomes planned, pre-cache travel and transport details for faster access
        # This happens in background - don't block the response
        try:
            # Pre-generate and cache travel details (non-blocking)
            total_days = (trip.end_date - trip.start_date).days + 1
            trip_data = {
                "destination": trip.destination,
                "duration": total_days,
                "total_days": total_days,
                "total_budget": trip.total_budget,
                "travelers": trip.travelers,
                "transportation_preference": trip.transportation_preference,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat()
            }
            
            # Schedule background task to generate and cache travel/transport details
            # The background task will create its own DB session
            background_tasks.add_task(
                _precache_travel_and_transport, trip_id, trip_data, enhanced_translation_service
            )
        except Exception as e:
            logger.warning(f"Failed to pre-cache travel/transport details: {e}")
            # Don't fail the request if pre-caching fails
        
        return {"message": "Trip option selected successfully", "option_id": option_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error selecting trip option: {str(e)}"
        )


@router.get("/{trip_id}/itinerary", response_model=List[DailyItineraryResponse])
async def get_trip_itinerary(
    trip_id: str,
    language: str = Query(default="english", description="Target language for translation"),
    db: Session = Depends(get_db)
):
    """Get daily itinerary for a trip with optional translation"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Set db session for translation cache
    enhanced_translation_service.set_db(db)
    
    itineraries = db.query(DailyItinerary).filter(
        DailyItinerary.trip_id == trip_id
    ).order_by(DailyItinerary.day_number).all()
    
    # Convert to dict format for caching and translation
    itineraries_data = []
    for itinerary in itineraries:
        itinerary_dict = {
            "id": itinerary.id,
            "trip_id": itinerary.trip_id,
            "day_number": itinerary.day_number,
            "date": itinerary.date.isoformat() if itinerary.date else None,
            "daily_budget": itinerary.daily_budget,
            "activities": itinerary.activities or [],
            "meals": itinerary.meals or [],
            "accommodation": itinerary.accommodation or {},
            "transport": itinerary.transport or {},
            "created_at": itinerary.created_at.isoformat() if itinerary.created_at else None,
            "updated_at": itinerary.updated_at.isoformat() if itinerary.updated_at else None,
        }
        itineraries_data.append(itinerary_dict)
    
    # Cache the original content for translation lookup (longer cache for planned trips)
    cache_ttl = 168 if trip.status in ["planned", "booked", "completed"] else 24
    if itineraries_data:
        await enhanced_translation_service.cache_api_response(
            trip_id=trip_id,
            content_type="daily_itineraries",
            content=itineraries_data,
            ttl_hours=cache_ttl
        )
    
    # Translate if needed
    if language.lower() != "english" and itineraries_data:
        try:
            translated = await enhanced_translation_service.get_translated_content(
                trip_id=trip_id,
                content_type="daily_itineraries",
                target_language=language
            )
            if translated:
                return translated
        except Exception as e:
            logger.warning(f"Translation failed, returning original: {e}")
    
    return itineraries_data


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


@router.post("/{trip_id}/places/search", response_model=PlaceSearchResponse)
async def search_places(
    trip_id: str,
    request: PlaceSearchRequest,
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
            query=request.query,
            location=coordinates,
            place_type=request.place_type,
            radius=request.radius
        )
        
        return {"places": places, "destination": trip.destination}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching places: {str(e)}"
        )


@router.get("/{trip_id}/photos", response_model=Dict[str, Any])
async def get_destination_photos(trip_id: str, db: Session = Depends(get_db)):
    """Return a list of destination photos.
    For planned/booked trips: Returns cached base64 images from database (no API calls).
    For draft trips: Fetches and returns photo URLs from Google Places API.
    Optimized with parallel search strategies.
    Requires Google Maps Platform API key with Places API enabled.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # For planned/booked/completed trips, check if we have cached base64 images
    if trip.status in ["planned", "booked", "completed"]:
        if trip.photos_base64 and isinstance(trip.photos_base64, list) and len(trip.photos_base64) > 0:
            logger.info(f"Returning {len(trip.photos_base64)} cached base64 photos for {trip.status} trip {trip_id}")
            return {
                "destination": trip.destination,
                "photos": trip.photos_base64,
                "cached": True,
                "format": "base64"
            }
        else:
            # Trip is planned but no cached images - fetch and cache them
            logger.info(f"Trip {trip_id} is {trip.status} but has no cached photos. Fetching and caching...")

    if not settings.google_maps_api_key or settings.google_maps_api_key == "your_google_maps_api_key_here":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Maps API key not configured for photos"
        )

    try:
        # Get coordinates first
        coords = await google_maps_service.geocode_address(trip.destination)
        logger.info(f"Geocoded {trip.destination} to coordinates: {coords}")
        
        places = []
        
        # Run multiple search strategies in parallel for better performance
        if coords:
            search_tasks = [
                google_maps_service.get_nearby_attractions(coords, radius=15000),
                google_maps_service.search_places(query=trip.destination),
                google_maps_service.search_places(
                    query="tourist attractions",
                    location=coords,
                    radius=10000
                ),
                google_maps_service.search_places(
                    query=f"{trip.destination} monuments temples",
                    location=coords,
                    radius=15000
                )
            ]
            
            # Execute all searches in parallel
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Collect results from successful searches
            for result in search_results:
                if isinstance(result, list) and result:
                    places.extend(result)
                    if len(places) >= 10:  # We have enough places
                        break
            
            # Remove duplicates based on place_id
            seen_ids = set()
            unique_places = []
            for p in places:
                place_id = p.get("place_id")
                if place_id and place_id not in seen_ids:
                    seen_ids.add(place_id)
                    unique_places.append(p)
                    if len(unique_places) >= 10:
                        break
            places = unique_places
            
            logger.info(f"Found {len(places)} unique places from parallel searches")
        else:
            # Fallback: single search without coordinates
            places = await google_maps_service.search_places(query=trip.destination)
            logger.info(f"Found {len(places)} places searching for '{trip.destination}'")

        photo_urls: List[str] = []
        api_key = settings.google_maps_api_key

        # Extract photos from places that already have photos
        logger.info(f"Processing {len(places)} places for photos")
        places_with_photos = []
        places_without_photos = []
        
        for p in places:
            photos_list = p.get("photos") or []
            if photos_list:
                places_with_photos.append(p)
            else:
                places_without_photos.append(p)
        
        # Process places with photos first
        for p in places_with_photos:
            place_name = p.get("name", "Unknown")
            photos_list = p.get("photos") or []
            
            for ph in photos_list[:3]:  # take up to 3 photos per place
                if isinstance(ph, dict):
                    ref = ph.get("photo_reference") or ph.get("photoReference")
                elif isinstance(ph, str):
                    ref = ph
                else:
                    continue
                
                if ref:
                    url = (
                        f"https://maps.googleapis.com/maps/api/place/photo"
                        f"?maxwidth=1200&photo_reference={ref}&key={api_key}"
                    )
                    photo_urls.append(url)
            
            if len(photo_urls) >= 12:
                break
        
        # If we don't have enough photos, fetch place details in parallel for places without photos
        if len(photo_urls) < 12 and places_without_photos:
            logger.info(f"Fetching place details in parallel for {min(5, len(places_without_photos))} places...")
            detail_tasks = []
            for p in places_without_photos[:5]:
                place_id = p.get("place_id")
                if place_id:
                    detail_tasks.append(google_maps_service.get_place_details(place_id))
            
            if detail_tasks:
                detail_results = await asyncio.gather(*detail_tasks, return_exceptions=True)
                
                for place_details in detail_results:
                    if isinstance(place_details, dict):
                        detail_photos = place_details.get("photos") or []
                        if detail_photos:
                            logger.debug(f"Found {len(detail_photos)} photos in place details for {place_details.get('name')}")
                            for ph in detail_photos[:3]:
                                if isinstance(ph, dict):
                                    ref = ph.get("photo_reference") or ph.get("photoReference")
                                    if ref:
                                        url = (
                                            f"https://maps.googleapis.com/maps/api/place/photo"
                                            f"?maxwidth=1200&photo_reference={ref}&key={api_key}"
                                        )
                                        photo_urls.append(url)
                        
                        if len(photo_urls) >= 12:
                            break
        
        # If we still don't have photos, log detailed info
        if not photo_urls:
            logger.warning(
                f"No photos found for destination: {trip.destination}. "
                f"Searched {len(places)} places. "
                f"Coordinates: {coords}"
            )
            return {"destination": trip.destination, "photos": [], "cached": False, "format": "url"}

        final_photo_urls = photo_urls[:12]
        logger.info(f"Successfully found {len(final_photo_urls)} photos for {trip.destination}")
        
        # If trip is planned/booked/completed, convert photos to base64 and cache them
        if trip.status in ["planned", "booked", "completed"]:
            try:
                logger.info(f"Converting {len(final_photo_urls)} photos to base64 for caching...")
                photos_base64 = []
                
                async def fetch_and_encode(url):
                    """Fetch image from URL and convert to base64 data URI"""
                    try:
                        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                            response = await client.get(url)
                            if response.status_code == 200:
                                # Convert to base64
                                image_base64 = base64.b64encode(response.content).decode('utf-8')
                                # Determine content type from response or default to jpeg
                                content_type = response.headers.get('content-type', 'image/jpeg')
                                # Return data URI format: data:image/jpeg;base64,...
                                return f"data:{content_type};base64,{image_base64}"
                            else:
                                logger.warning(f"Failed to fetch photo: HTTP {response.status_code}")
                                return None
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout fetching photo from {url[:50]}...")
                        return None
                    except Exception as e:
                        logger.warning(f"Failed to fetch and encode photo from {url[:50]}...: {e}")
                        return None
                
                # Fetch and convert all photos in parallel (limit concurrency to avoid overwhelming)
                encode_tasks = [fetch_and_encode(url) for url in final_photo_urls]
                encoded_results = await asyncio.gather(*encode_tasks, return_exceptions=True)
                
                # Filter out None, exceptions, and invalid results
                for result in encoded_results:
                    if result and not isinstance(result, Exception) and isinstance(result, str) and result.startswith("data:image"):
                        photos_base64.append(result)
                
                if photos_base64:
                    # Store in database
                    trip.photos_base64 = photos_base64
                    trip.updated_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Cached {len(photos_base64)} photos as base64 for {trip.status} trip {trip_id}")
                    return {
                        "destination": trip.destination,
                        "photos": photos_base64,
                        "cached": True,
                        "format": "base64"
                    }
                else:
                    logger.warning("Failed to encode any photos, returning URLs instead")
            except Exception as e:
                logger.error(f"Error caching photos as base64: {e}", exc_info=True)
                # Continue to return URLs if caching fails
        
        # Return URLs for draft trips or if caching failed
        return {
            "destination": trip.destination,
            "photos": final_photo_urls,
            "cached": False,
            "format": "url"
        }
    except Exception as e:
        logger.error(f"Error fetching destination photos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching destination photos: {str(e)}"
        )


@router.get("/{trip_id}/geocode", response_model=Dict[str, Any])
async def geocode_place(trip_id: str, q: str, db: Session = Depends(get_db)):
    """Geocode a place for the trip's destination using Google Maps.
    Returns { lat, lng } or 400 if not found.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    try:
        # Prefer destination context to improve precision
        query = q
        if trip.destination and trip.destination.lower() not in q.lower():
            query = f"{q}, {trip.destination}"
        coords = await google_maps_service.geocode_address(query)
        if not coords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not geocode query"
            )
        return {"lat": coords[0], "lng": coords[1]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error geocoding: {str(e)}"
        )


@router.get("/{trip_id}/smart-adjustments/{day_number}", response_model=Dict[str, Any])
async def get_smart_adjustments(
    trip_id: str,
    day_number: int,
    db: Session = Depends(get_db)
):
    """Get smart adjustment suggestions for a specific day based on weather, traffic, and attractions"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Validate day number
    total_days = (trip.end_date - trip.start_date).days + 1
    if day_number < 1 or day_number > total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day number. Must be between 1 and {total_days}"
        )
    
    try:
        # Calculate the date for this day
        target_date = trip.start_date + timedelta(days=day_number - 1)
        
        # Get the itinerary for this day if it exists
        daily_itinerary = db.query(DailyItinerary).filter(
            DailyItinerary.trip_id == trip_id,
            DailyItinerary.day_number == day_number
        ).first()
        
        current_itinerary = None
        if daily_itinerary:
            current_itinerary = {
                "places": daily_itinerary.activities or [],
                "activities": daily_itinerary.activities or [],
                "meals": daily_itinerary.meals or [],
                "transport": daily_itinerary.transport or {}
            }
        
        # Get coordinates for destination
        coordinates = await google_maps_service.geocode_address(trip.destination)
        
        # Fetch smart adjustments using the service
        adjustments = await smart_adjustments_service.get_smart_adjustments(
            trip_id=trip_id,
            destination=trip.destination,
            date=target_date,
            coordinates=coordinates,
            current_itinerary=current_itinerary
        )
        
        return {
            "trip_id": trip_id,
            "day_number": day_number,
            "date": target_date.isoformat(),
            "adjustments": adjustments,
            "count": len(adjustments)
        }
        
    except Exception as e:
        logger.error(f"Error fetching smart adjustments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching smart adjustments: {str(e)}"
        )


@router.post("/{trip_id}/adjust-itinerary/{day_number}", response_model=Dict[str, Any])
async def adjust_itinerary(
    trip_id: str,
    day_number: int,
    adjustment_type: str = Body(..., description="Type of adjustment: weather, traffic, or opportunity"),
    adjustment_data: Dict[str, Any] = Body(..., description="Adjustment data and preferences"),
    db: Session = Depends(get_db)
):
    """Apply smart adjustments to modify the itinerary for a specific day based on weather/traffic conditions"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Validate day number
    total_days = (trip.end_date - trip.start_date).days + 1
    if day_number < 1 or day_number > total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day number. Must be between 1 and {total_days}"
        )
    
    try:
        # Get the current itinerary for this day
        daily_itinerary = db.query(DailyItinerary).filter(
            DailyItinerary.trip_id == trip_id,
            DailyItinerary.day_number == day_number
        ).first()
        
        if not daily_itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily itinerary not found for this day"
            )
        
        # Get target date
        target_date = trip.start_date + timedelta(days=day_number - 1)
        
        # Get coordinates
        coordinates = await google_maps_service.geocode_address(trip.destination)
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find coordinates for destination"
            )
        
        # Apply adjustments using AI service
        # For weather adjustments, regenerate itinerary considering weather
        if adjustment_type == "weather":
            # Use AI to generate weather-adjusted itinerary
            trip_data = {
                "destination": trip.destination,
                "date": target_date.isoformat(),
                "current_itinerary": {
                    "activities": daily_itinerary.activities or [],
                    "meals": daily_itinerary.meals or [],
                    "places": daily_itinerary.activities or []
                },
                "weather_data": adjustment_data.get("weather_data", {})
            }
            
            # Generate adjusted daily itinerary
            adjusted_itinerary = await google_ai_service.generate_daily_itinerary(
                trip_data, day_number
            )
            
            # Update with adjusted data
            if adjusted_itinerary:
                daily_itinerary.activities = adjusted_itinerary.get("activities") or adjusted_itinerary.get("places", [])
                daily_itinerary.meals = adjusted_itinerary.get("meals", daily_itinerary.meals)
                daily_itinerary.transport = adjusted_itinerary.get("transport", daily_itinerary.transport) or adjusted_itinerary.get("transportation")
        
        elif adjustment_type == "traffic":
            # For traffic, mainly update transport timing and suggest alternatives
            transport = daily_itinerary.transport or {}
            if isinstance(transport, dict):
                route_info = adjustment_data.get("route_info", {})
                transport["adjusted_timing"] = adjustment_data.get("suggested_departure_time")
                transport["traffic_delay_minutes"] = route_info.get("traffic_delay_seconds", 0) / 60
                transport["duration_in_traffic"] = route_info.get("duration_in_traffic")
                transport["alternative_route"] = adjustment_data.get("alternative_route")
                daily_itinerary.transport = transport
        
        elif adjustment_type == "route":
            # For route updates, update transport with new route
            route_info = adjustment_data.get("route_info", {})
            recommended_route = route_info.get("recommended_route", {})
            transport = daily_itinerary.transport or {}
            if isinstance(transport, dict):
                transport["updated_route"] = recommended_route.get("summary", "")
                transport["route_duration"] = recommended_route.get("duration", "")
                transport["route_distance"] = recommended_route.get("distance", "")
                transport["route_polyline"] = recommended_route.get("overview_polyline", "")
                transport["time_saved_minutes"] = route_info.get("time_saved_minutes", 0)
                daily_itinerary.transport = transport
            
            # Optionally update activities timing if route affects schedule
            if recommended_route:
                activities = daily_itinerary.activities or []
                if activities:
                    # Adjust first activity timing if needed
                    for activity in activities[:1]:
                        if isinstance(activity, dict):
                            # Could add logic here to adjust timing based on route changes
                            pass
        
        elif adjustment_type == "alert":
            # For place closures, use AI to suggest alternatives or remove activities
            place_info = adjustment_data.get("place_info", {})
            place_name = place_info.get("name", "")
            issue_type = place_info.get("issue_type", "")
            
            if issue_type in ["closed_permanently", "closed_temporarily"]:
                # Remove or replace closed places from itinerary
                activities = daily_itinerary.activities or []
                if isinstance(activities, list):
                    # Filter out closed place
                    daily_itinerary.activities = [
                        act for act in activities
                        if isinstance(act, dict) and act.get("name", "").lower() != place_name.lower()
                        and act.get("place", "").lower() != place_name.lower()
                        and act.get("activity", "").lower() != place_name.lower()
                    ]
                    
                    # Use AI to suggest replacement if place was removed
                    if len(activities) > len(daily_itinerary.activities):
                        trip_data = {
                            "destination": trip.destination,
                            "date": target_date.isoformat(),
                            "current_itinerary": {
                                "activities": daily_itinerary.activities,
                                "meals": daily_itinerary.meals or [],
                            },
                            "removed_place": place_name,
                            "reason": f"Place is {issue_type.replace('_', ' ')}"
                        }
                        # Generate replacement suggestion (optional - can be async)
                        # adjusted_itinerary = await google_ai_service.suggest_alternative_place(...)
        
        daily_itinerary.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(daily_itinerary)
        
        return {
            "message": "Itinerary adjusted successfully",
            "trip_id": trip_id,
            "day_number": day_number,
            "adjusted_itinerary": {
                "activities": daily_itinerary.activities,
                "meals": daily_itinerary.meals,
                "transport": daily_itinerary.transport
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adjusting itinerary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adjusting itinerary: {str(e)}"
        )


@router.get("/{trip_id}/transport-details", response_model=Dict[str, Any])
async def get_transport_details(
    trip_id: str,
    language: str = Query(default="english", description="Target language for translation"),
    force_regenerate: bool = Query(default=False, description="Force regeneration even for planned trips"),
    db: Session = Depends(get_db)
):
    """
    Get local transport details (city/local transport) based on budget and total days.
    For planned/booked trips: Returns cached content (translated if needed).
    For new trips: Generates new content and caches it.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Set db session for translation cache
    enhanced_translation_service.set_db(db)
    
    try:
        # For planned/booked/completed trips, check cache first (unless forced to regenerate)
        if trip.status in ["planned", "booked", "completed"] and not force_regenerate:
            # First check database (persistent storage)
            cached_content = await _get_content_from_db(db, trip_id, "transport_details")
            
            # If not in DB, check in-memory cache
            if not cached_content:
                cached_content = await enhanced_translation_service.content_cache.get(trip_id, "transport_details")
                # If found in memory cache, also store in DB for persistence
                if cached_content:
                    await _store_content_in_db(db, trip_id, "transport_details", cached_content, ttl_hours=168)
            
            if cached_content:
                logger.info(f"Returning cached transport details for {trip.status} trip {trip_id}")
                
                # Also update in-memory cache for faster subsequent access
                await enhanced_translation_service.cache_api_response(
                    trip_id=trip_id,
                    content_type="transport_details",
                    content=cached_content,
                    ttl_hours=168
                )
                
                # Translate if needed
                if language.lower() != "english":
                    try:
                        translated = await enhanced_translation_service.get_translated_content(
                            trip_id=trip_id,
                            content_type="transport_details",
                            target_language=language
                        )
                        if translated:
                            return translated
                    except Exception as e:
                        logger.warning(f"Translation failed, returning cached original: {e}")
                
                return cached_content
        
        # Generate new content (for draft trips, or when cache is missing, or when forced)
        logger.info(f"Generating transport details for trip {trip_id} (status: {trip.status})")
        
        # Calculate total days
        total_days = (trip.end_date - trip.start_date).days + 1
        
        # Prepare trip data for AI service
        trip_data = {
            "destination": trip.destination,
            "duration": total_days,
            "total_days": total_days,
            "total_budget": trip.total_budget,
            "travelers": trip.travelers,
            "transportation_preference": trip.transportation_preference,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat()
        }
        
        # Generate transport details using AI
        transport_details = await google_ai_service.generate_transport_details(trip_data)
        
        # Cache the original content (important for planned/booked trips)
        cache_ttl = 168 if trip.status in ["planned", "booked", "completed"] else 24
        
        # Store in in-memory cache
        await enhanced_translation_service.cache_api_response(
            trip_id=trip_id,
            content_type="transport_details",
            content=transport_details,
            ttl_hours=cache_ttl
        )
        
        # Store in database for planned/booked trips (persistent storage)
        if trip.status in ["planned", "booked", "completed"]:
            await _store_content_in_db(db, trip_id, "transport_details", transport_details, ttl_hours=cache_ttl)
        
        # Translate if needed
        if language.lower() != "english":
            try:
                translated = await enhanced_translation_service.get_translated_content(
                    trip_id=trip_id,
                    content_type="transport_details",
                    target_language=language
                )
                if translated:
                    return translated
            except Exception as e:
                logger.warning(f"Translation failed, returning original: {e}")
        
        return transport_details
        
    except Exception as e:
        logger.error(f"Error fetching transport details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transport details: {str(e)}"
        )


@router.get("/{trip_id}/travel-details", response_model=Dict[str, Any])
async def get_travel_details(
    trip_id: str,
    language: str = Query(default="english", description="Target language for translation"),
    force_regenerate: bool = Query(default=False, description="Force regeneration even for planned trips"),
    db: Session = Depends(get_db)
):
    """
    Get inter-city travel details (flights, trains, buses) based on budget and total days.
    For planned/booked trips: Returns cached content (translated if needed).
    For new trips: Generates new content and caches it.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Set db session for translation cache
    enhanced_translation_service.set_db(db)
    
    try:
        # For planned/booked/completed trips, check cache first (unless forced to regenerate)
        if trip.status in ["planned", "booked", "completed"] and not force_regenerate:
            # First check database (persistent storage)
            cached_content = await _get_content_from_db(db, trip_id, "travel_details")
            
            # If not in DB, check in-memory cache
            if not cached_content:
                cached_content = await enhanced_translation_service.content_cache.get(trip_id, "travel_details")
                # If found in memory cache, also store in DB for persistence
                if cached_content:
                    await _store_content_in_db(db, trip_id, "travel_details", cached_content, ttl_hours=168)
            
            if cached_content:
                logger.info(f"Returning cached travel details for {trip.status} trip {trip_id}")
                
                # Also update in-memory cache for faster subsequent access
                await enhanced_translation_service.cache_api_response(
                    trip_id=trip_id,
                    content_type="travel_details",
                    content=cached_content,
                    ttl_hours=168
                )
                
                # Translate if needed
                if language.lower() != "english":
                    try:
                        translated = await enhanced_translation_service.get_translated_content(
                            trip_id=trip_id,
                            content_type="travel_details",
                            target_language=language
                        )
                        if translated:
                            return translated
                    except Exception as e:
                        logger.warning(f"Translation failed, returning cached original: {e}")
                
                return cached_content
        
        # Generate new content (for draft trips, or when cache is missing, or when forced)
        logger.info(f"Generating travel details for trip {trip_id} (status: {trip.status})")
        
        # Calculate total days
        total_days = (trip.end_date - trip.start_date).days + 1
        
        # Prepare trip data for AI service
        trip_data = {
            "destination": trip.destination,
            "duration": total_days,
            "total_days": total_days,
            "total_budget": trip.total_budget,
            "travelers": trip.travelers,
            "transportation_preference": trip.transportation_preference,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat()
        }
        
        # Generate travel details using AI
        travel_details = await google_ai_service.generate_travel_details(trip_data)
        
        # Cache the original content (important for planned/booked trips)
        cache_ttl = 168 if trip.status in ["planned", "booked", "completed"] else 24
        
        # Store in in-memory cache
        await enhanced_translation_service.cache_api_response(
            trip_id=trip_id,
            content_type="travel_details",
            content=travel_details,
            ttl_hours=cache_ttl
        )
        
        # Store in database for planned/booked trips (persistent storage)
        if trip.status in ["planned", "booked", "completed"]:
            await _store_content_in_db(db, trip_id, "travel_details", travel_details, ttl_hours=cache_ttl)
        
        # Translate if needed
        if language.lower() != "english":
            try:
                translated = await enhanced_translation_service.get_translated_content(
                    trip_id=trip_id,
                    content_type="travel_details",
                    target_language=language
                )
                if translated:
                    return translated
            except Exception as e:
                logger.warning(f"Translation failed, returning original: {e}")
        
        return travel_details
        
    except Exception as e:
        logger.error(f"Error fetching travel details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching travel details: {str(e)}"
        )


@router.get("/{trip_id}/booking-prices", response_model=Dict[str, Any])
async def get_booking_prices(trip_id: str, db: Session = Depends(get_db)):
    """
    Get calculated booking prices for flights and car rentals based on travel and transport data.
    Filters options to ensure they stay within the user's budget.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Calculate total days
        total_days = (trip.end_date - trip.start_date).days + 1
        travelers = trip.travelers
        total_budget = trip.total_budget
        
        # Fetch travel details (flights, trains, buses)
        trip_data = {
            "destination": trip.destination,
            "duration": total_days,
            "total_days": total_days,
            "total_budget": trip.total_budget,
            "travelers": trip.travelers,
            "transportation_preference": trip.transportation_preference,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat()
        }
        
        travel_details = await google_ai_service.generate_travel_details(trip_data)
        transport_details = await google_ai_service.generate_transport_details(trip_data)
        
        # Calculate flight costs from travel details
        flight_cost = 0
        flight_options = []
        
        # Get flights from outbound and return options
        for option in travel_details.get('outbound_options', []):
            if option.get('type') == 'flight':
                cost = option.get('total_cost') or (option.get('cost_per_person', 0) * travelers)
                flight_cost += cost
                flight_options.append({
                    'type': 'outbound',
                    'route': option.get('route', ''),
                    'provider': option.get('provider', ''),
                    'cost': cost,
                    'cost_per_person': option.get('cost_per_person', 0),
                    'departure_time': option.get('departure_time', ''),
                    'arrival_time': option.get('arrival_time', ''),
                    'class': option.get('class', 'Economy')
                })
        
        for option in travel_details.get('return_options', []):
            if option.get('type') == 'flight':
                cost = option.get('total_cost') or (option.get('cost_per_person', 0) * travelers)
                flight_cost += cost
                flight_options.append({
                    'type': 'return',
                    'route': option.get('route', ''),
                    'provider': option.get('provider', ''),
                    'cost': cost,
                    'cost_per_person': option.get('cost_per_person', 0),
                    'departure_time': option.get('departure_time', ''),
                    'arrival_time': option.get('arrival_time', ''),
                    'class': option.get('class', 'Economy')
                })
        
        # If no flights found, calculate estimated flight cost (25% of budget)
        if flight_cost == 0:
            flight_cost = int(total_budget * 0.25)
        
        # Calculate car rental costs from transport details
        car_rental_cost = 0
        car_rental_options = []
        
        for rec in transport_details.get('recommendations', []):
            if rec.get('type') == 'car_rental':
                cost = rec.get('total_cost') or (rec.get('daily_cost', 0) * total_days)
                car_rental_cost += cost
                car_rental_options.append({
                    'provider': rec.get('provider', ''),
                    'title': rec.get('title', 'Car Rental'),
                    'cost': cost,
                    'daily_cost': rec.get('daily_cost', 0),
                    'duration': rec.get('duration', f'{total_days} days'),
                    'description': rec.get('description', ''),
                    'features': rec.get('features', [])
                })
        
        # If no car rental found but preference is private, estimate cost
        if car_rental_cost == 0 and trip.transportation_preference in ['private', 'mixed']:
            transport_budget = total_budget * 0.18
            car_rental_cost = int(transport_budget * 0.4)  # 40% of transport budget
            car_rental_options.append({
                'provider': 'Zoomcar / Ola Outstation',
                'title': 'Car Rental',
                'cost': car_rental_cost,
                'daily_cost': int(car_rental_cost / total_days),
                'duration': f'{total_days} days',
                'description': 'Estimated car rental cost',
                'features': ['AC', 'GPS', 'Flexible routes']
            })
        
        # Calculate train costs (for alternative transport)
        train_cost = 0
        train_options = []
        
        for option in travel_details.get('outbound_options', []) + travel_details.get('return_options', []):
            if option.get('type') == 'train':
                cost = option.get('total_cost') or (option.get('cost_per_person', 0) * travelers)
                train_cost += cost
                train_options.append({
                    'route': option.get('route', ''),
                    'provider': option.get('provider', ''),
                    'cost': cost,
                    'cost_per_person': option.get('cost_per_person', 0),
                    'class': option.get('class', '')
                })
        
        # Total transportation cost (include all transport types)
        total_transportation_cost = flight_cost + car_rental_cost + train_cost
        
        # Ensure we're within budget - adjust if needed
        travel_budget = total_budget * 0.45
        transport_budget = total_budget * 0.18
        max_transportation_budget = travel_budget + transport_budget
        
        if total_transportation_cost > max_transportation_budget:
            # Scale down proportionally
            scale_factor = max_transportation_budget / total_transportation_cost
            flight_cost = int(flight_cost * scale_factor)
            car_rental_cost = int(car_rental_cost * scale_factor)
            train_cost = int(train_cost * scale_factor)
            # Update options with scaled costs
            for opt in flight_options:
                opt['cost'] = int(opt['cost'] * scale_factor)
            for opt in car_rental_options:
                opt['cost'] = int(opt['cost'] * scale_factor)
            for opt in train_options:
                opt['cost'] = int(opt['cost'] * scale_factor)
        
        booking_prices_result = {
            "flight": {
                "total_cost": flight_cost,
                "options": flight_options,
                "count": len(flight_options)
            },
            "car_rental": {
                "total_cost": car_rental_cost,
                "options": car_rental_options,
                "count": len(car_rental_options)
            },
            "train": {
                "total_cost": train_cost,
                "options": train_options,
                "count": len(train_options)
            },
            "total_transportation_cost": total_transportation_cost,
            "budget_allocated": max_transportation_budget,
            "budget_remaining": max_transportation_budget - total_transportation_cost,
            "within_budget": total_transportation_cost <= max_transportation_budget
        }
        
        # Store original content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="booking_prices",
            content=booking_prices_result,
            ttl_hours=24
        )
        
        return booking_prices_result
        
    except Exception as e:
        logger.error(f"Error calculating booking prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating booking prices: {str(e)}"
        )


@router.post("/translate", response_model=Dict[str, Any])
async def translate_content(
    content: Dict[str, Any] = Body(..., description="Content to translate"),
    target_language: str = Body(..., description="Target language (e.g., 'kannada', 'hindi', 'tamil')"),
    source_language: Optional[str] = Body(None, description="Source language (optional)")
):
    """
    Translate content using Google Cloud Translation API
    Supports translating text, lists, dictionaries, and nested structures
    """
    try:
        if not content:
            return {"translated": {}}
        
        # Translate the content
        if isinstance(content, dict):
            translated = await translation_service.translate_dict(content, target_language)
        elif isinstance(content, list):
            translated = await translation_service.translate_list_or_dict_list(content, target_language)
        elif isinstance(content, str):
            translated = await translation_service.translate_text(content, target_language, source_language)
        else:
            translated = content
        
        return {"translated": translated, "target_language": target_language}
        
    except Exception as e:
        logger.error(f"Error translating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating content: {str(e)}"
        )


@router.post("/translate/itinerary", response_model=Dict[str, Any])
async def translate_itinerary(
    itinerary: Dict[str, Any] = Body(..., description="Itinerary data to translate"),
    target_language: str = Body(..., description="Target language")
):
    """
    Translate itinerary data structure including activities, meals, accommodation, etc.
    """
    try:
        if not itinerary:
            return {"translated": {}}
        
        translated = await translation_service.translate_itinerary(itinerary, target_language)
        
        return {"translated": translated, "target_language": target_language}
        
    except Exception as e:
        logger.error(f"Error translating itinerary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating itinerary: {str(e)}"
        )


@router.post("/translate/texts", response_model=Dict[str, Any])
async def translate_texts(
    texts: List[str] = Body(..., description="List of texts to translate"),
    target_language: str = Body(..., description="Target language"),
    source_language: Optional[str] = Body(None, description="Source language (optional)")
):
    """
    Translate a list of texts
    """
    try:
        if not texts:
            return {"translated": []}
        
        translated = await translation_service.translate_list(texts, target_language, source_language)
        
        return {"translated": translated, "target_language": target_language}
        
    except Exception as e:
        logger.error(f"Error translating texts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating texts: {str(e)}"
        )


@router.post("/{trip_id}/translate-cached", response_model=Dict[str, Any])
async def translate_cached_content_batch(
    trip_id: str,
    content_types: List[str] = Body(..., description="List of content types to translate (e.g., 'daily_itineraries', 'trip_options', 'transport_details')"),
    target_language: str = Body(..., description="Target language"),
    db: Session = Depends(get_db)
):
    """
    Translate cached content in batches by content type using enhanced translation service.
    Retrieves original content from cache and translates each type separately.
    Uses database cache for efficient translation storage.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Set db session for translation cache
    enhanced_translation_service.set_db(db)
    
    if target_language.lower() == "english":
        return {
            "message": "Target language is English, no translation needed",
            "translated_content": {}
        }
    
    try:
        # Use enhanced translation service for batch translation
        translated_results = await enhanced_translation_service.translate_cached_content_batch(
            trip_id=trip_id,
            content_types=content_types,
            target_language=target_language
        )
        
        return {
            "trip_id": trip_id,
            "target_language": target_language,
            "translated_content": translated_results
        }
        
    except Exception as e:
        logger.error(f"Error translating cached content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating cached content: {str(e)}"
        )


@router.post("/{trip_id}/translate-daily-itineraries", response_model=Dict[str, Any])
async def translate_all_daily_itineraries(
    trip_id: str,
    target_language: str = Body(..., description="Target language"),
    db: Session = Depends(get_db)
):
    """
    Translate all cached daily itineraries for a trip.
    Fetches all daily itinerary content types and translates them separately.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    if target_language.lower() == "english":
        return {
            "message": "Target language is English, no translation needed",
            "translated_itineraries": {}
        }
    
    try:
        total_days = (trip.end_date - trip.start_date).days + 1
        translated_itineraries = {}
        
        # Translate each day's itinerary separately
        for day_number in range(1, total_days + 1):
            content_type = f"daily_itinerary_{day_number}"
            cached_items = await content_cache_service.get_all_by_type(trip_id, content_type)
            
            if cached_items:
                latest_item = max(cached_items, key=lambda x: x['created_at'])
                original_itinerary = latest_item['data']
                
                translated_itinerary = await translation_service.translate_itinerary(
                    original_itinerary, target_language
                )
                translated_itineraries[str(day_number)] = translated_itinerary
                logger.debug(f"Translated day {day_number} itinerary to {target_language}")
            else:
                logger.warning(f"No cached itinerary found for day {day_number}")
        
        return {
            "trip_id": trip_id,
            "target_language": target_language,
            "translated_itineraries": translated_itineraries,
            "total_days": total_days,
            "translated_count": len(translated_itineraries)
        }
        
    except Exception as e:
        logger.error(f"Error translating daily itineraries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating daily itineraries: {str(e)}"
        )


@router.get("/{trip_id}/cache-stats", response_model=Dict[str, Any])
async def get_cache_stats(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Get cache statistics for a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    stats = await content_cache_service.get_cache_stats(trip_id=trip_id)
    return stats


@router.get("/{trip_id}/weather", response_model=Dict[str, Any])
async def get_trip_weather(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Get weather data for destination for entire trip period"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
        # Check if weather API key is configured (Google Maps API key or OpenWeatherMap)
        if not settings.google_maps_api_key and not settings.openweather_api_key:
            logger.error("Weather API key is not configured. Please configure either GOOGLE_MAPS_API_KEY or OPENWEATHER_API_KEY")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Weather service is not available. Please configure GOOGLE_MAPS_API_KEY (preferred) or OPENWEATHER_API_KEY in environment variables."
            )
        
        # Get coordinates for destination
        logger.info(f"Geocoding destination: {trip.destination}")
        coordinates = await google_maps_service.geocode_address(trip.destination)
        if not coordinates:
            logger.error(f"Could not geocode destination: {trip.destination}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not geocode destination: {trip.destination}"
            )
        
        logger.info(f"Coordinates for {trip.destination}: {coordinates}")
        
        # Check if we have cached weather for the entire trip
        cache_key = "trip_weather_forecast"
        cached_weather_forecast = await content_cache_service.get(trip_id, cache_key)
        
        # If not cached or cache expired, fetch weather for entire trip duration
        if not cached_weather_forecast:
            logger.info(f"Fetching weather forecast for {trip.destination} for entire trip duration ({trip.start_date.date()} to {trip.end_date.date()})")
            
            # Fetch weather forecast for the entire trip period
            try:
                weather_forecast_data = await smart_adjustments_service._fetch_weather_forecast_for_period(
                    coordinates=coordinates,
                    start_date=trip.start_date,
                    end_date=trip.end_date
                )
            except Exception as e:
                logger.error(f"Error calling _fetch_weather_forecast_for_period: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error fetching weather data: {str(e)}"
                )
            
            # Cache the forecast for 6 hours (forecast data updates frequently)
            if weather_forecast_data:
                logger.info(f"Successfully fetched weather forecast. Organizing by date...")
                await content_cache_service.store(
                    trip_id=trip_id,
                    content_type=cache_key,
                    content=weather_forecast_data,
                    ttl_hours=6
                )
                cached_weather_forecast = weather_forecast_data
            else:
                logger.warning(f"Failed to fetch weather forecast for {trip.destination} - will fetch day by day")
                # Don't raise error, instead we'll fetch day by day below
                cached_weather_forecast = None
        
        # Process all weather data for the trip period
        forecast_by_date = cached_weather_forecast.get("forecast_by_date", {}) if cached_weather_forecast else {}
        logger.info(f"Processing weather data. Found {len(forecast_by_date)} dates in forecast cache")
        
        if not forecast_by_date:
            logger.warning("No weather forecast data found in cache. Will fetch day by day as fallback.")
        
        total_days = (trip.end_date - trip.start_date).days + 1
        
        weather_updates = []
        for day_number in range(1, total_days + 1):
            target_date = trip.start_date + timedelta(days=day_number - 1)
            date_key = target_date.date().isoformat()
            
            day_weather = forecast_by_date.get(date_key)
            
            # If exact date not found, use closest forecast
            if not day_weather and forecast_by_date:
                target_date_obj = target_date.date()
                try:
                    # Helper function to safely parse date keys
                    def parse_date_key(key):
                        if isinstance(key, str):
                            # Try parsing as ISO format date string
                            try:
                                return datetime.fromisoformat(key).date()
                            except (ValueError, AttributeError):
                                # If that fails, try just date parsing
                                try:
                                    return datetime.strptime(key, "%Y-%m-%d").date()
                                except ValueError:
                                    return None
                        return key
                    
                    # Find closest date
                    valid_dates = [(k, parse_date_key(k)) for k in forecast_by_date.keys() if parse_date_key(k)]
                    if valid_dates:
                        closest_date_key = min(
                            valid_dates,
                            key=lambda x: abs((x[1] - target_date_obj).days) if x[1] else float('inf')
                        )[0]
                        day_weather = forecast_by_date.get(closest_date_key)
                        logger.debug(f"Using closest forecast for day {day_number}: {closest_date_key}")
                except Exception as e:
                    logger.warning(f"Error finding closest forecast date: {e}")
                    day_weather = None
            
            # Fallback: fetch weather directly for this day if cached data unavailable
            if not day_weather:
                logger.info(f"Fetching weather directly for {trip.destination} on {target_date.date()}")
                day_weather = await smart_adjustments_service._fetch_weather_data(coordinates, target_date)
            
            if day_weather:
                # Calculate temperature range
                temp = day_weather.get("temperature", 0)
                feels_like = day_weather.get("feels_like", temp)
                min_temp = min(temp, feels_like) - 2
                max_temp = max(temp, feels_like) + 3
                
                # Format condition text
                condition = day_weather.get("condition", "clear").title()
                description = day_weather.get("description", "")
                description_text = description.title() if description else ""
                
                # Create formatted weather summary
                month_name = target_date.strftime("%B")
                condition_text = f"Likely {condition}"
                if description_text:
                    condition_text += f" - {description_text}"
                condition_text += f", Typical For {month_name}."
                
                # Add additional context based on weather
                if day_weather.get("rain", 0) > 0:
                    condition_text += " Potential For Rain."
                if day_weather.get("wind_speed", 0) > 10:
                    condition_text += " Windy Conditions Expected."
                elif day_weather.get("clouds", 0) > 50:
                    condition_text += " Cloudy Skies Possible."
                
                # Create recommendations
                recommendations = []
                if temp > 30:
                    recommendations.append("Stay hydrated and seek shade during peak hours.")
                    recommendations.append("Pack light, breathable clothing. Sun protection is crucial.")
                elif temp < 15:
                    recommendations.append("Dress in layers. Carry warm clothing.")
                else:
                    recommendations.append("Pack light, breathable clothing. Sun protection recommended.")
                
                if day_weather.get("rain", 0) > 0:
                    recommendations.append("Carry an umbrella or rain gear.")
                if day_weather.get("wind_speed", 0) > 10:
                    recommendations.append("Secure loose items. Wind-resistant clothing recommended.")
                
                weather_summary = {
                    "temperature_range": f"{int(min_temp)}-{int(max_temp)}°C",
                    "condition": condition_text,
                    "recommendations": " ".join(recommendations),
                    "temperature": temp,
                    "condition_keyword": condition.lower(),
                    "description": description
                }
                
                weather_updates.append({
                    "day_number": day_number,
                    "date": target_date.isoformat(),
                    "coordinates": coordinates,
                    "place_name": trip.destination,
                    "location": trip.destination,
                    "weather_data": day_weather,
                    "weather_summary": weather_summary
                })
        
        return {
            "trip_id": trip_id,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "weather_updates": weather_updates,
            "count": len(weather_updates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trip weather: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching trip weather: {str(e)}"
        )


@router.get("/{trip_id}/day-weather/{day_number}", response_model=Dict[str, Any])
async def get_day_weather(
    trip_id: str,
    day_number: int,
    db: Session = Depends(get_db)
):
    """Get weather data for destination for a specific day - fetches once for entire trip duration and caches it"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Validate day number
    total_days = (trip.end_date - trip.start_date).days + 1
    if day_number < 1 or day_number > total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day number. Must be between 1 and {total_days}"
        )
    
    try:
        # Calculate the date for this day
        target_date = trip.start_date + timedelta(days=day_number - 1)
        
        # Get coordinates for destination
        coordinates = await google_maps_service.geocode_address(trip.destination)
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not geocode destination: {trip.destination}"
            )
        
        # Check if we have cached weather for the entire trip
        cache_key = "trip_weather_forecast"
        cached_weather_forecast = await content_cache_service.get(trip_id, cache_key)
        
        # If not cached or cache expired, fetch weather for entire trip duration
        if not cached_weather_forecast:
            logger.info(f"Fetching weather forecast for {trip.destination} for entire trip duration")
            
            # Fetch weather forecast for the entire trip period
            weather_forecast_data = await smart_adjustments_service._fetch_weather_forecast_for_period(
                coordinates=coordinates,
                start_date=trip.start_date,
                end_date=trip.end_date
            )
            
            # Cache the forecast for 6 hours (forecast data updates frequently)
            if weather_forecast_data:
                await content_cache_service.store(
                    trip_id=trip_id,
                    content_type=cache_key,
                    content=weather_forecast_data,
                    ttl_hours=6
                )
                cached_weather_forecast = weather_forecast_data
            else:
                logger.warning(f"Failed to fetch weather forecast for {trip.destination}")
        
        # Extract weather for the specific day
        day_weather = None
        if cached_weather_forecast and isinstance(cached_weather_forecast, dict):
            # Find weather for the target date
            forecast_by_date = cached_weather_forecast.get("forecast_by_date", {})
            date_key = target_date.date().isoformat()
            day_weather = forecast_by_date.get(date_key)
            
            # If exact date not found, use closest forecast
            if not day_weather and forecast_by_date:
                # Find closest date
                target_date_obj = target_date.date()
                closest_date = min(
                    forecast_by_date.keys(),
                    key=lambda x: abs((datetime.fromisoformat(x).date() - target_date_obj).days)
                )
                day_weather = forecast_by_date.get(closest_date)
        
        # Fallback: fetch weather directly for this day if cached data unavailable
        if not day_weather:
            logger.info(f"Fetching weather directly for {trip.destination} on {target_date.date()}")
            day_weather = await smart_adjustments_service._fetch_weather_data(coordinates, target_date)
        
        # Format response with weather summary
        weather_summary = None
        if day_weather:
            # Calculate temperature range (estimate based on current temp ±2-3°C)
            temp = day_weather.get("temperature", 0)
            feels_like = day_weather.get("feels_like", temp)
            min_temp = min(temp, feels_like) - 2
            max_temp = max(temp, feels_like) + 3
            
            # Format condition text
            condition = day_weather.get("condition", "clear").title()
            description = day_weather.get("description", "")
            description_text = description.title() if description else ""
            
            # Create formatted weather summary
            month_name = target_date.strftime("%B")
            condition_text = f"Likely {condition}"
            if description_text:
                condition_text += f" - {description_text}"
            condition_text += f", Typical For {month_name}."
            
            # Add additional context based on weather
            if day_weather.get("rain", 0) > 0:
                condition_text += " Potential For Rain."
            if day_weather.get("wind_speed", 0) > 10:
                condition_text += " Windy Conditions Expected."
            elif day_weather.get("clouds", 0) > 50:
                condition_text += " Cloudy Skies Possible."
            
            # Create recommendations
            recommendations = []
            if temp > 30:
                recommendations.append("Stay hydrated and seek shade during peak hours.")
                recommendations.append("Pack light, breathable clothing. Sun protection is crucial.")
            elif temp < 15:
                recommendations.append("Dress in layers. Carry warm clothing.")
            else:
                recommendations.append("Pack light, breathable clothing. Sun protection recommended.")
            
            if day_weather.get("rain", 0) > 0:
                recommendations.append("Carry an umbrella or rain gear.")
            if day_weather.get("wind_speed", 0) > 10:
                recommendations.append("Secure loose items. Wind-resistant clothing recommended.")
            
            weather_summary = {
                "temperature_range": f"{int(min_temp)}-{int(max_temp)}°C (estimated)",
                "condition": condition_text,
                "recommendations": " ".join(recommendations),
                "temperature": temp,
                "condition_keyword": condition.lower(),
                "description": description
            }
            
            weather_data_list = [{
                "coordinates": coordinates,
                "place_name": trip.destination,
                "location": trip.destination,
                "weather_data": day_weather,
                "weather_summary": weather_summary
            }]
        else:
            weather_data_list = []
            logger.warning(f"No weather data available for {trip.destination} on {target_date.date()}")
        
        return {
            "trip_id": trip_id,
            "day_number": day_number,
            "date": target_date.isoformat(),
            "weather_updates": weather_data_list,
            "count": len(weather_data_list),
            "weather_summary": weather_summary  # Add summary at top level too
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching day weather: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching day weather: {str(e)}"
        )


@router.get("/{trip_id}/day-traffic/{day_number}", response_model=Dict[str, Any])
async def get_day_traffic(
    trip_id: str,
    day_number: int,
    db: Session = Depends(get_db)
):
    """Get traffic/routing data between places in a specific day's itinerary"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Validate day number
    total_days = (trip.end_date - trip.start_date).days + 1
    if day_number < 1 or day_number > total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day number. Must be between 1 and {total_days}"
        )
    
    try:
        # Calculate the date for this day
        target_date = trip.start_date + timedelta(days=day_number - 1)
        
        # Get the itinerary for this day
        daily_itinerary = db.query(DailyItinerary).filter(
            DailyItinerary.trip_id == trip_id,
            DailyItinerary.day_number == day_number
        ).first()
        
        # Try to get from cache first
        content_type = f"daily_itinerary_{day_number}"
        cached_itinerary = await content_cache_service.get(trip_id, content_type)
        
        if not cached_itinerary and not daily_itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily itinerary not found for this day"
            )
        
        # Use cached itinerary if available, otherwise use DB itinerary
        day_data = cached_itinerary if cached_itinerary else {
            "places": daily_itinerary.activities or [],
            "activities": daily_itinerary.activities or [],
            "meals": daily_itinerary.meals or []
        }
        
        # Get coordinates for destination (fallback)
        coordinates = await google_maps_service.geocode_address(trip.destination)
        
        # Prepare current itinerary structure
        current_itinerary = {
            "places": day_data.get("places", []),
            "activities": day_data.get("activities", []),
            "meals": day_data.get("meals", [])
        }
        
        # Fetch traffic data for routes between places
        traffic_data = await smart_adjustments_service._fetch_traffic_data(
            coordinates=coordinates,
            current_itinerary=current_itinerary,
            date=target_date
        )
        
        return {
            "trip_id": trip_id,
            "day_number": day_number,
            "date": target_date.isoformat(),
            "traffic_data": traffic_data,
            "has_traffic": traffic_data.get("has_delays", False),
            "segments_count": len(traffic_data.get("segments", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching day traffic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching day traffic: {str(e)}"
        )


@router.get("/{trip_id}/packing/{day_number}", response_model=Dict[str, Any])
async def get_day_packing(
    trip_id: str,
    day_number: int,
    db: Session = Depends(get_db)
):
    """Get packing suggestions for a specific day based on weather, activities, and temple dress codes"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Validate day number
    total_days = (trip.end_date - trip.start_date).days + 1
    if day_number < 1 or day_number > total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day number. Must be between 1 and {total_days}"
        )
    
    try:
        # Calculate the date for this day
        target_date = trip.start_date + timedelta(days=day_number - 1)
        
        # Get the itinerary for this day (optional - can work without it)
        daily_itinerary = db.query(DailyItinerary).filter(
            DailyItinerary.trip_id == trip_id,
            DailyItinerary.day_number == day_number
        ).first()
        
        # Try to get from cache first
        content_type = f"daily_itinerary_{day_number}"
        cached_itinerary = await content_cache_service.get(trip_id, content_type)
        
        # Use cached itinerary if available, otherwise use DB itinerary, or empty if neither exists
        if cached_itinerary:
            day_data = cached_itinerary
        elif daily_itinerary:
            day_data = {
                "places": daily_itinerary.activities or [],
                "activities": daily_itinerary.activities or [],
                "meals": daily_itinerary.meals or []
            }
        else:
            # No itinerary found - use empty data, we'll still generate packing based on destination and weather
            logger.info(f"No daily itinerary found for day {day_number}, generating packing based on destination and weather")
            day_data = {
                "places": [],
                "activities": [],
                "meals": []
            }
        
        # Get activities
        activities = day_data.get("activities", [])
        
        # Get weather data for this day (using the same cached weather approach as weather endpoint)
        coordinates = await google_maps_service.geocode_address(trip.destination)
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not geocode destination: {trip.destination}"
            )
        
        # Use the same weather fetching logic as day-weather endpoint
        cache_key = "trip_weather_forecast"
        cached_weather_forecast = await content_cache_service.get(trip_id, cache_key)
        
        # If not cached or cache expired, fetch weather for entire trip duration
        if not cached_weather_forecast:
            logger.info(f"Fetching weather forecast for {trip.destination} for entire trip duration (from packing endpoint)")
            
            # Fetch weather forecast for the entire trip period
            weather_forecast_data = await smart_adjustments_service._fetch_weather_forecast_for_period(
                coordinates=coordinates,
                start_date=trip.start_date,
                end_date=trip.end_date
            )
            
            # Cache the forecast for 6 hours (forecast data updates frequently)
            if weather_forecast_data:
                await content_cache_service.store(
                    trip_id=trip_id,
                    content_type=cache_key,
                    content=weather_forecast_data,
                    ttl_hours=6
                )
                cached_weather_forecast = weather_forecast_data
        
        # Get weather for this specific day
        day_weather = None
        if cached_weather_forecast and isinstance(cached_weather_forecast, dict):
            forecast_by_date = cached_weather_forecast.get("forecast_by_date", {})
            date_key = target_date.date().isoformat()
            day_weather = forecast_by_date.get(date_key)
            
            # If exact date not found, use closest forecast
            if not day_weather and forecast_by_date:
                target_date_obj = target_date.date()
                closest_date = min(
                    forecast_by_date.keys(),
                    key=lambda x: abs((datetime.fromisoformat(x).date() - target_date_obj).days)
                )
                day_weather = forecast_by_date.get(closest_date)
        
        # Fallback: fetch weather directly for this day if cached data unavailable
        if not day_weather:
            logger.info(f"Fetching weather directly for {trip.destination} on {target_date.date()} (from packing endpoint)")
            day_weather = await smart_adjustments_service._fetch_weather_data(coordinates, target_date)
        
        # Format weather data for packing API
        weather_data_list = []
        if day_weather:
            weather_data_list = [{
                "coordinates": coordinates,
                "place_name": trip.destination,
                "location": trip.destination,
                "weather_data": day_weather
            }]
        
        # Prepare trip data for packing generation
        trip_data = {
            "destination": trip.destination,
            "date": target_date.isoformat(),
            "travelers": trip.travelers
        }
        
        # Generate packing suggestions using AI
        packing_suggestions = await google_ai_service.generate_packing_suggestions(
            trip_data=trip_data,
            day_number=day_number,
            weather_data=weather_data_list,
            activities=activities
        )
        
        return {
            "trip_id": trip_id,
            "day_number": day_number,
            "date": target_date.isoformat(),
            "packing_suggestions": packing_suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching packing suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching packing suggestions: {str(e)}"
        )
