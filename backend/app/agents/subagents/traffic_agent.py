"""
Traffic Agent - Specialized agent for fetching and analyzing traffic data
Part of the multi-agent smart adjustments system
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class TrafficAgent:
    """Agent specialized in traffic data fetching and route analysis"""
    
    async def process_request(
        self, 
        user_input: str, 
        user_id: str, 
        context: Dict[str, Any], 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process traffic-related requests"""
        try:
            # Extract route information from context
            origin = context.get("origin") or context.get("start_location")
            destination = context.get("destination") or context.get("end_location")
            itinerary = context.get("itinerary") or context.get("current_itinerary")
            
            if not itinerary and (not origin or not destination):
                return {
                    "type": "traffic",
                    "message": "Please provide route information to analyze traffic",
                    "status": "error"
                }
            
            # Fetch traffic data
            traffic_data = await self.fetch_traffic_data(context)
            
            return {
                "type": "traffic",
                "message": self._format_traffic_message(traffic_data),
                "traffic_data": traffic_data,
                "status": "success",
                "suggestions": self._generate_traffic_suggestions(traffic_data)
            }
            
        except Exception as e:
            logger.error(f"Error in traffic agent: {e}")
            return {
                "type": "traffic",
                "message": "Unable to fetch traffic data at this time",
                "status": "error"
            }
    
    async def fetch_traffic_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch traffic data using Google Maps Directions API"""
        try:
            from ....services.google_maps_service import google_maps_service
            
            itinerary = context.get("itinerary") or context.get("current_itinerary")
            origin = context.get("origin")
            destination = context.get("destination")
            
            if itinerary:
                # Extract locations from itinerary
                locations = []
                places = itinerary.get("places", []) or []
                activities = itinerary.get("activities", []) or []
                
                for item in places + activities:
                    location = item.get("location") or item.get("address")
                    if location:
                        locations.append(location)
                
                if len(locations) < 2:
                    return {}
                
                # Get traffic data for route segments
                traffic_segments = []
                for i in range(len(locations) - 1):
                    origin_loc = locations[i]
                    dest_loc = locations[i + 1]
                    
                    directions = await google_maps_service.get_directions(
                        origin=origin_loc,
                        destination=dest_loc,
                        mode="driving"
                    )
                    
                    if directions:
                        traffic_segments.append({
                            "origin": origin_loc,
                            "destination": dest_loc,
                            "duration": directions.get("duration", ""),
                            "distance": directions.get("distance", ""),
                            "steps": directions.get("steps", [])
                        })
                
                return {
                    "segments": traffic_segments,
                    "has_delays": len(traffic_segments) > 0
                }
            
            elif origin and destination:
                # Single route
                directions = await google_maps_service.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving"
                )
                
                if directions:
                    return {
                        "segments": [{
                            "origin": origin,
                            "destination": destination,
                            "duration": directions.get("duration", ""),
                            "distance": directions.get("distance", ""),
                            "steps": directions.get("steps", [])
                        }],
                        "has_delays": True
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            return {}
    
    def _format_traffic_message(self, traffic_data: Dict[str, Any]) -> str:
        """Format traffic data into a user-friendly message"""
        if not traffic_data or not traffic_data.get("segments"):
            return "No traffic data available"
        
        segments = traffic_data.get("segments", [])
        if segments:
            first_segment = segments[0]
            duration = first_segment.get("duration", "Unknown")
            return f"Estimated travel time: {duration}"
        
        return "Traffic data unavailable"
    
    def _generate_traffic_suggestions(self, traffic_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on traffic conditions"""
        suggestions = []
        segments = traffic_data.get("segments", [])
        
        if segments:
            # Check for long durations (indicating traffic)
            for segment in segments:
                duration_str = segment.get("duration", "")
                if "hour" in duration_str.lower():
                    suggestions.append("Consider leaving earlier")
                    suggestions.append("Check alternative routes")
                    suggestions.append("Use public transportation if available")
                    break
        
        return suggestions
