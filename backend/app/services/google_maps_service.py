import googlemaps
from typing import Dict, List, Any, Optional, Tuple
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsService:
    def __init__(self):
        if not settings.google_maps_api_key:
            logger.warning("Google Maps API key not configured")
            self.client = None
        else:
            self.client = googlemaps.Client(key=settings.google_maps_api_key)
    
    async def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information about a place"""
        if not self.client:
            return self._get_fallback_place_details(place_id)
        
        try:
            place = self.client.place(place_id=place_id)
            return self._format_place_details(place)
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return self._get_fallback_place_details(place_id)
    
    async def search_places(self, query: str, location: Optional[Tuple[float, float]] = None, 
                          radius: int = 5000, place_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for places near a location"""
        if not self.client:
            return self._get_fallback_search_results(query)
        
        try:
            if location:
                places = self.client.places_nearby(
                    location=location,
                    radius=radius,
                    keyword=query,
                    type=place_type
                )
            else:
                places = self.client.places(query=query, type=place_type)
            
            return [self._format_place_details(place) for place in places.get('results', [])]
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return self._get_fallback_search_results(query)
    
    async def get_directions(self, origin: str, destination: str, 
                           mode: str = "driving") -> Dict[str, Any]:
        """Get directions between two points"""
        if not self.client:
            return self._get_fallback_directions(origin, destination)
        
        try:
            directions = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode
            )
            return self._format_directions(directions)
        except Exception as e:
            logger.error(f"Error getting directions: {e}")
            return self._get_fallback_directions(origin, destination)
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates"""
        if not self.client:
            return self._get_fallback_coordinates(address)
        
        try:
            geocode_result = self.client.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return (location['lat'], location['lng'])
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
        
        return self._get_fallback_coordinates(address)
    
    async def get_nearby_restaurants(self, location: Tuple[float, float], 
                                   radius: int = 1000) -> List[Dict[str, Any]]:
        """Get nearby restaurants"""
        return await self.search_places(
            query="restaurant",
            location=location,
            radius=radius,
            place_type="restaurant"
        )
    
    async def get_nearby_hotels(self, location: Tuple[float, float], 
                              radius: int = 2000) -> List[Dict[str, Any]]:
        """Get nearby hotels"""
        return await self.search_places(
            query="hotel",
            location=location,
            radius=radius,
            place_type="lodging"
        )
    
    async def get_nearby_attractions(self, location: Tuple[float, float], 
                                   radius: int = 5000) -> List[Dict[str, Any]]:
        """Get nearby tourist attractions"""
        return await self.search_places(
            query="tourist attraction",
            location=location,
            radius=radius,
            place_type="tourist_attraction"
        )
    
    def _format_place_details(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Format place details from Google Maps API"""
        geometry = place.get('geometry', {})
        location = geometry.get('location', {})
        
        return {
            "place_id": place.get('place_id'),
            "name": place.get('name'),
            "formatted_address": place.get('formatted_address'),
            "coordinates": {
                "lat": location.get('lat'),
                "lng": location.get('lng')
            },
            "rating": place.get('rating'),
            "price_level": place.get('price_level'),
            "types": place.get('types', []),
            "photos": place.get('photos', []),
            "opening_hours": place.get('opening_hours', {}),
            "reviews": place.get('reviews', [])[:3],  # Limit to 3 reviews
            "website": place.get('website'),
            "phone_number": place.get('formatted_phone_number')
        }
    
    def _format_directions(self, directions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format directions from Google Maps API"""
        if not directions:
            return {}
        
        route = directions[0]
        legs = route.get('legs', [])
        
        if not legs:
            return {}
        
        leg = legs[0]
        steps = leg.get('steps', [])
        
        return {
            "distance": leg.get('distance', {}).get('text'),
            "duration": leg.get('duration', {}).get('text'),
            "start_address": leg.get('start_address'),
            "end_address": leg.get('end_address'),
            "steps": [
                {
                    "instruction": step.get('html_instructions'),
                    "distance": step.get('distance', {}).get('text'),
                    "duration": step.get('duration', {}).get('text'),
                    "travel_mode": step.get('travel_mode')
                }
                for step in steps
            ],
            "overview_polyline": route.get('overview_polyline', {}).get('points')
        }
    
    def _get_fallback_place_details(self, place_id: str) -> Dict[str, Any]:
        """Fallback place details when API fails"""
        return {
            "place_id": place_id,
            "name": "Sample Place",
            "formatted_address": "Sample Address",
            "coordinates": {"lat": 28.6139, "lng": 77.209},
            "rating": 4.0,
            "price_level": 2,
            "types": ["tourist_attraction"],
            "photos": [],
            "opening_hours": {},
            "reviews": [],
            "website": None,
            "phone_number": None
        }
    
    def _get_fallback_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search results when API fails"""
        return [
            {
                "place_id": f"fallback_{query}_1",
                "name": f"Sample {query.title()} 1",
                "formatted_address": "Sample Address 1",
                "coordinates": {"lat": 28.6139, "lng": 77.209},
                "rating": 4.0,
                "price_level": 2,
                "types": ["establishment"],
                "photos": [],
                "opening_hours": {},
                "reviews": [],
                "website": None,
                "phone_number": None
            },
            {
                "place_id": f"fallback_{query}_2",
                "name": f"Sample {query.title()} 2",
                "formatted_address": "Sample Address 2",
                "coordinates": {"lat": 28.6140, "lng": 77.210},
                "rating": 4.2,
                "price_level": 3,
                "types": ["establishment"],
                "photos": [],
                "opening_hours": {},
                "reviews": [],
                "website": None,
                "phone_number": None
            }
        ]
    
    def _get_fallback_directions(self, origin: str, destination: str) -> Dict[str, Any]:
        """Fallback directions when API fails"""
        return {
            "distance": "5 km",
            "duration": "15 minutes",
            "start_address": origin,
            "end_address": destination,
            "steps": [
                {
                    "instruction": f"Start from {origin}",
                    "distance": "0 km",
                    "duration": "0 min",
                    "travel_mode": "driving"
                },
                {
                    "instruction": f"Drive to {destination}",
                    "distance": "5 km",
                    "duration": "15 min",
                    "travel_mode": "driving"
                }
            ],
            "overview_polyline": ""
        }
    
    def _get_fallback_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Fallback coordinates when geocoding fails"""
        # Return Delhi coordinates as fallback
        return (28.6139, 77.209)


# Create service instance
google_maps_service = GoogleMapsService()
