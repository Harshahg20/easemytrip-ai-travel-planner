from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

from ...core.database import get_db
from ...models.trip import Trip, DailyItinerary, TripOption
from ...services.google_ai_service import google_ai_service
from ...services.google_maps_service import google_maps_service
from ...services.smart_adjustments_service import smart_adjustments_service
from ...services.translation_service import translation_service
from ...services.content_cache_service import content_cache_service
from ...core.config import settings
from ..schemas.trip import (
    TripCreate, TripResponse, TripUpdate,
    TripOptionResponse, DailyItineraryResponse,
    TripOptionsGenerate, PlaceSearchRequest, PlaceSearchResponse
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
    """Return a list of destination photo URLs using Google Places Photos API.
    Optimized with parallel search strategies.
    Requires Google Maps Platform API key with Places API enabled.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

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
            return {"destination": trip.destination, "photos": []}

        logger.info(f"Successfully found {len(photo_urls)} photos for {trip.destination}")
        return {"destination": trip.destination, "photos": photo_urls[:12]}
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
async def get_transport_details(trip_id: str, db: Session = Depends(get_db)):
    """Get local transport details (city/local transport) based on budget and total days"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
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
        
        # Store original content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="transport_details",
            content=transport_details,
            ttl_hours=24
        )
        
        return transport_details
        
    except Exception as e:
        logger.error(f"Error fetching transport details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transport details: {str(e)}"
        )


@router.get("/{trip_id}/travel-details", response_model=Dict[str, Any])
async def get_travel_details(trip_id: str, db: Session = Depends(get_db)):
    """Get inter-city travel details (flights, trains, buses) based on budget and total days"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    try:
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
        
        # Store original content in cache
        await content_cache_service.store(
            trip_id=trip_id,
            content_type="travel_details",
            content=travel_details,
            ttl_hours=24
        )
        
        return travel_details
        
    except Exception as e:
        logger.error(f"Error fetching travel details: {e}")
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
        
        # Total transportation cost
        total_transportation_cost = flight_cost + car_rental_cost
        
        # Ensure we're within budget - adjust if needed
        travel_budget = total_budget * 0.45
        transport_budget = total_budget * 0.18
        max_transportation_budget = travel_budget + transport_budget
        
        if total_transportation_cost > max_transportation_budget:
            # Scale down proportionally
            scale_factor = max_transportation_budget / total_transportation_cost
            flight_cost = int(flight_cost * scale_factor)
            car_rental_cost = int(car_rental_cost * scale_factor)
            # Update options with scaled costs
            for opt in flight_options:
                opt['cost'] = int(opt['cost'] * scale_factor)
            for opt in car_rental_options:
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
            "total_transportation_cost": flight_cost + car_rental_cost,
            "budget_allocated": max_transportation_budget,
            "budget_remaining": max_transportation_budget - (flight_cost + car_rental_cost),
            "within_budget": (flight_cost + car_rental_cost) <= max_transportation_budget
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
    Translate cached content in batches by content type.
    Retrieves original content from cache and translates each type separately.
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
            "translated_content": {}
        }
    
    try:
        translated_results = {}
        
        for content_type in content_types:
            # Get all cached content of this type
            cached_items = await content_cache_service.get_all_by_type(trip_id, content_type)
            
            if not cached_items:
                logger.warning(f"No cached content found for type: {content_type}")
                translated_results[content_type] = None
                continue
            
            # Use the most recent cached item
            latest_item = max(cached_items, key=lambda x: x['created_at'])
            original_content = latest_item['data']
            
            # Translate based on content type
            if content_type.startswith("daily_itinerary_"):
                # Translate daily itinerary
                translated_content = await translation_service.translate_itinerary(
                    original_content, target_language
                )
                translated_results[content_type] = translated_content
            elif content_type == "trip_options":
                # Translate trip options (list of options)
                translated_options = []
                for option in original_content:
                    translated_option = await translation_service.translate_itinerary(
                        option, target_language
                    )
                    translated_options.append(translated_option)
                translated_results[content_type] = translated_options
            else:
                # Generic translation for other content types
                translated_content = await translation_service.translate_dict(
                    original_content, target_language
                )
                translated_results[content_type] = translated_content
            
            logger.info(f"Translated {content_type} to {target_language}")
        
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


@router.get("/{trip_id}/day-weather/{day_number}", response_model=Dict[str, Any])
async def get_day_weather(
    trip_id: str,
    day_number: int,
    db: Session = Depends(get_db)
):
    """Get weather data for destination - fetches once for entire trip duration and caches it"""
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
            # OpenWeatherMap forecast API provides 5-day forecast, so we'll get forecast for start date
            # and if needed, we can fetch additional forecasts
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
