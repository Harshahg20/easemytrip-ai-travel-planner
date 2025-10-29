from typing import Dict, List, Any
import asyncio
import logging
from google.cloud import aiplatform

logger = logging.getLogger(__name__)

class EmergencyAgent:
    """Handles emergency situations and urgent requests"""
    
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
    
    async def process_request(self, user_input: str, user_id: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process emergency and urgent requests"""
        try:
            # Analyze the type of emergency
            if 'flight' in user_input.lower() and ('delay' in user_input.lower() or 'cancel' in user_input.lower()):
                return await self._handle_flight_emergency(user_input, context)
            elif 'lost' in user_input.lower() or 'directions' in user_input.lower():
                return await self._handle_lost_emergency(user_input, context)
            elif 'medical' in user_input.lower() or 'health' in user_input.lower():
                return await self._handle_medical_emergency(user_input, context)
            elif 'theft' in user_input.lower() or 'stolen' in user_input.lower():
                return await self._handle_theft_emergency(user_input, context)
            else:
                return await self._handle_general_emergency(user_input, context)
                
        except Exception as e:
            logger.error(f"Error in emergency agent: {e}")
            return {
                'type': 'emergency',
                'message': 'I understand you need urgent help. Let me assist you immediately!',
                'suggestions': [
                    'Flight issues',
                    'Lost or need directions',
                    'Medical emergency',
                    'Theft or security issue'
                ]
            }
    
    async def _handle_flight_emergency(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle flight-related emergencies"""
        return {
            'type': 'emergency',
            'category': 'flight',
            'message': 'I can help you with flight issues immediately!',
            'urgent_actions': [
                'Check flight status',
                'Find alternative flights',
                'Contact airline',
                'Rebook if necessary'
            ],
            'emergency_contacts': [
                'Airline customer service',
                'Airport information',
                'Travel insurance',
                'Embassy/Consulate'
            ],
            'suggestions': [
                'Check flight status',
                'Find alternative routes',
                'Contact airline directly',
                'Get compensation info'
            ]
        }
    
    async def _handle_lost_emergency(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle lost/directions emergencies"""
        return {
            'type': 'emergency',
            'category': 'lost',
            'message': 'Don\'t worry! I can help you get back on track!',
            'urgent_actions': [
                'Share your location',
                'Get directions to hotel',
                'Find nearest landmarks',
                'Contact local help'
            ],
            'emergency_contacts': [
                'Local emergency services',
                'Hotel front desk',
                'Tourist information',
                'Taxi services'
            ],
            'suggestions': [
                'Share your location',
                'Get directions',
                'Find nearest hotel',
                'Call for help'
            ]
        }
    
    async def _handle_medical_emergency(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle medical emergencies"""
        return {
            'type': 'emergency',
            'category': 'medical',
            'message': 'Medical emergency! I\'ll help you get immediate assistance!',
            'urgent_actions': [
                'Call emergency services',
                'Find nearest hospital',
                'Contact travel insurance',
                'Get medical assistance'
            ],
            'emergency_contacts': [
                'Emergency services (911)',
                'Nearest hospital',
                'Travel insurance hotline',
                'Embassy/Consulate'
            ],
            'suggestions': [
                'Call emergency services',
                'Find nearest hospital',
                'Contact travel insurance',
                'Get medical help'
            ]
        }
    
    async def _handle_theft_emergency(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle theft/security emergencies"""
        return {
            'type': 'emergency',
            'category': 'theft',
            'message': 'I\'m sorry this happened! Let me help you immediately!',
            'urgent_actions': [
                'Report to police',
                'Cancel stolen cards',
                'Contact embassy',
                'File insurance claim'
            ],
            'emergency_contacts': [
                'Local police',
                'Bank/credit card companies',
                'Embassy/Consulate',
                'Travel insurance'
            ],
            'suggestions': [
                'Report to police',
                'Cancel stolen cards',
                'Contact embassy',
                'File insurance claim'
            ]
        }
    
    async def _handle_general_emergency(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general emergencies"""
        return {
            'type': 'emergency',
            'message': 'I understand you need urgent help! Here\'s how I can assist:',
            'emergency_services': [
                'Flight and travel issues',
                'Lost or need directions',
                'Medical emergencies',
                'Theft or security issues',
                'General travel problems'
            ],
            'emergency_contacts': [
                'Local emergency services',
                'Embassy/Consulate',
                'Travel insurance',
                'Hotel assistance'
            ],
            'suggestions': [
                'Describe your emergency',
                'Get immediate help',
                'Contact emergency services',
                'Find local assistance'
            ]
        }
