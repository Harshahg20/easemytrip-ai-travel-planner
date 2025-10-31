"""
Attractions Agent - Specialized agent for fetching and analyzing attractions data
Part of the multi-agent smart adjustments system
"""
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class AttractionsAgent:
    """Agent specialized in attractions and points of interest data"""
    
    async def process_request(
        self, 
        user_input: str, 
        user_id: str, 
        context: Dict[str, Any], 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process attractions-related requests"""
        try:
            # Extract location information from context
            destination = context.get("destination") or context.get("location")
            coordinates = context.get("coordinates")
            radius = context.get("radius", 5000)  # Default 5km
            
            if not destination and not coordinates:
                return {
                    "type": "attractions",
                    "message": "Please provide a location to find attractions",
                    "status": "error"
                }
            
            # Get coordinates if needed
            if not coordinates and destination:
                from ....services.google_maps_service import google_maps_service
                coordinates = await google_maps_service.geocode_address(destination)
            
            if not coordinates:
                return {
                    "type": "attractions",
                    "message": f"Could not find coordinates for {destination}",
                    "status": "error"
                }
            
            # Fetch attractions
            attractions = await self.fetch_attractions(coordinates, radius)
            
            return {
                "type": "attractions",
                "message": f"Found {len(attractions)} attractions nearby",
                "attractions": attractions,
                "status": "success",
                "suggestions": self._generate_attraction_suggestions(attractions)
            }
            
        except Exception as e:
            logger.error(f"Error in attractions agent: {e}")
            return {
                "type": "attractions",
                "message": "Unable to fetch attractions data at this time",
                "status": "error"
            }
    
    async def fetch_attractions(
        self, 
        coordinates: Tuple[float, float],
        radius: int = 5000
    ) -> List[Dict[str, Any]]:
        """Fetch nearby attractions using Google Places API"""
        try:
            from ....services.google_maps_service import google_maps_service
            
            # Get nearby attractions
            attractions = await google_maps_service.get_nearby_attractions(
                location=coordinates,
                radius=radius
            )
            
            # Filter and format attractions
            formatted_attractions = []
            for attr in attractions[:15]:  # Limit to top 15
                rating = attr.get("rating", 0)
                # Only include well-rated places
                if rating >= 3.5:
                    formatted_attractions.append({
                        "name": attr.get("name"),
                        "location": attr.get("formatted_address"),
                        "rating": rating,
                        "types": attr.get("types", []),
                        "coordinates": attr.get("coordinates"),
                        "place_id": attr.get("place_id"),
                        "price_level": attr.get("price_level"),
                        "photos": attr.get("photos", [])[:3]  # Limit photos
                    })
            
            # Sort by rating (highest first)
            formatted_attractions.sort(key=lambda x: x.get("rating", 0), reverse=True)
            
            return formatted_attractions
            
        except Exception as e:
            logger.error(f"Error fetching attractions: {e}")
            return []
    
    def _generate_attraction_suggestions(self, attractions: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions based on available attractions"""
        suggestions = []
        
        if attractions:
            top_attraction = attractions[0]
            suggestions.append(f"Highly rated: {top_attraction.get('name')} ({top_attraction.get('rating', 0)}⭐)")
            
            if len(attractions) > 1:
                suggestions.append(f"Explore {len(attractions)} nearby attractions")
        
        return suggestions
