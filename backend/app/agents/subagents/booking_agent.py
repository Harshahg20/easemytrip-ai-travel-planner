from typing import Dict, List, Any
import asyncio
import logging
from google.cloud import aiplatform

logger = logging.getLogger(__name__)

class BookingAgent:
    """Handles flight, hotel, and activity bookings"""
    
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
    
    async def process_request(self, user_input: str, user_id: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process booking-related requests"""
        try:
            # Extract booking parameters
            entities = intent.get('entities', {})
            
            if 'flight' in user_input.lower():
                return await self._handle_flight_booking(entities, context)
            elif 'hotel' in user_input.lower() or 'accommodation' in user_input.lower():
                return await self._handle_hotel_booking(entities, context)
            elif 'activity' in user_input.lower() or 'tour' in user_input.lower():
                return await self._handle_activity_booking(entities, context)
            else:
                return await self._get_booking_options(entities, context)
                
        except Exception as e:
            logger.error(f"Error in booking agent: {e}")
            return {
                'type': 'booking',
                'message': 'I can help you book flights, hotels, and activities! What would you like to book?',
                'suggestions': [
                    'Book flights',
                    'Find hotels',
                    'Reserve activities',
                    'Check availability'
                ]
            }
    
    async def _handle_flight_booking(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle flight booking requests"""
        return {
            'type': 'booking',
            'category': 'flight',
            'message': 'I can help you find and book flights!',
            'options': [
                'Search for flights',
                'Compare prices',
                'Check flight status',
                'Manage bookings'
            ],
            'suggestions': [
                'Enter departure city',
                'Enter destination',
                'Select travel dates',
                'Choose number of passengers'
            ]
        }
    
    async def _handle_hotel_booking(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hotel booking requests"""
        return {
            'type': 'booking',
            'category': 'hotel',
            'message': 'I can help you find and book hotels!',
            'options': [
                'Search for hotels',
                'Compare prices',
                'Check availability',
                'Manage reservations'
            ],
            'suggestions': [
                'Enter destination',
                'Select check-in date',
                'Select check-out date',
                'Choose room type'
            ]
        }
    
    async def _handle_activity_booking(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle activity booking requests"""
        return {
            'type': 'booking',
            'category': 'activity',
            'message': 'I can help you find and book activities!',
            'options': [
                'Search for activities',
                'Browse tours',
                'Check availability',
                'Make reservations'
            ],
            'suggestions': [
                'Enter destination',
                'Select activity type',
                'Choose date',
                'Select number of people'
            ]
        }
    
    async def _get_booking_options(self, entities: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general booking options"""
        return {
            'type': 'booking',
            'message': 'What would you like to book for your trip?',
            'categories': [
                {
                    'name': 'Flights',
                    'description': 'Search and book flights',
                    'icon': '✈️'
                },
                {
                    'name': 'Hotels',
                    'description': 'Find and reserve accommodations',
                    'icon': '🏨'
                },
                {
                    'name': 'Activities',
                    'description': 'Book tours and experiences',
                    'icon': '🎯'
                },
                {
                    'name': 'Transportation',
                    'description': 'Rent cars or book transfers',
                    'icon': '🚗'
                }
            ]
        }
