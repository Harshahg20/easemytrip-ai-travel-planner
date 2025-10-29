import asyncio
from typing import Dict, List, Any, Optional
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip
import json
import logging

from ..orchestrator.orchestrator_agent import OrchestratorAgent
from ..orchestrator.agent_communication import agent_communication

logger = logging.getLogger(__name__)

class TravelConciergeAgent:
    """
    Main Travel Concierge Agent using Google ADK
    Now uses advanced orchestrator for multi-agent coordination
    """
    
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
        self.subagents = {}
        self.conversation_history = []
        
        # Initialize AI Platform with proper authentication
        try:
            aiplatform.init(project=project_id, location=region)
            logger.info(f"AI Platform initialized for project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AI Platform: {e}")
        
        # Initialize advanced orchestrator
        self.orchestrator = OrchestratorAgent(project_id, region)
        
        # Get subagents from orchestrator for backward compatibility
        self.subagents = self.orchestrator.subagents
        
        # Register agents for communication
        for agent_name, agent_instance in self.subagents.items():
            agent_communication.register_agent(agent_name, agent_instance)
        
        logger.info("Travel Concierge Agent initialized with orchestrator")
    
    def _initialize_subagents(self):
        """Initialize all sub-agents"""
        from ..subagents.inspiration_agent import InspirationAgent
        from ..subagents.planning_agent import PlanningAgent
        from ..subagents.booking_agent import BookingAgent
        from ..subagents.assistant_agent import AssistantAgent
        from ..subagents.emergency_agent import EmergencyAgent
        
        self.subagents = {
            'inspiration': InspirationAgent(self.project_id, self.region),
            'planning': PlanningAgent(self.project_id, self.region),
            'booking': BookingAgent(self.project_id, self.region),
            'assistant': AssistantAgent(self.project_id, self.region),
            'emergency': EmergencyAgent(self.project_id, self.region)
        }
    
    async def process_user_request(self, user_input: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing user requests
        Now delegates to orchestrator for intelligent coordination
        """
        try:
            # Use orchestrator for advanced multi-agent coordination
            response = await self.orchestrator.process_request(
                user_input, user_id, context or {}
            )
            
            # Update conversation history for backward compatibility
            self.conversation_history.append({
                'user_id': user_id,
                'input': user_input,
                'response': response,
                'timestamp': asyncio.get_event_loop().time()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return {
                'type': 'error',
                'message': 'I apologize, but I encountered an error. Please try again.',
                'suggestions': ['Try rephrasing your request', 'Contact support if the issue persists']
            }
    
    async def _analyze_intent(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user intent using AI Platform"""
        try:
            # Use AI Platform for intent classification
            prompt = f"""
            Analyze the following user input and determine the intent and required sub-agent:
            
            User Input: "{user_input}"
            Context: {json.dumps(context, indent=2)}
            
            Available sub-agents:
            - inspiration: For destination discovery, travel ideas, trending places
            - planning: For itinerary creation, trip planning, scheduling
            - booking: For flight/hotel/activity reservations
            - assistant: For real-time assistance, questions, support
            - emergency: For urgent situations, crisis management
            
            Return JSON with:
            {{
                "intent": "primary_intent",
                "sub_agent": "recommended_sub_agent",
                "confidence": 0.95,
                "entities": {{"destination": "Tokyo", "date": "2024-03-15"}},
                "urgency": "low|medium|high"
            }}
            """
            
            # This would use AI Platform's text generation
            # For now, using a simple rule-based approach
            return self._rule_based_intent_analysis(user_input, context)
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                'intent': 'general_query',
                'sub_agent': 'assistant',
                'confidence': 0.5,
                'entities': {},
                'urgency': 'low'
            }
    
    def _rule_based_intent_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based intent analysis (fallback)"""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['book', 'reserve', 'buy', 'purchase']):
            return {
                'intent': 'booking',
                'sub_agent': 'booking',
                'confidence': 0.8,
                'entities': {},
                'urgency': 'medium'
            }
        elif any(word in user_input_lower for word in ['plan', 'itinerary', 'schedule', 'organize']):
            return {
                'intent': 'planning',
                'sub_agent': 'planning',
                'confidence': 0.8,
                'entities': {},
                'urgency': 'low'
            }
        elif any(word in user_input_lower for word in ['inspire', 'discover', 'suggest', 'recommend']):
            return {
                'intent': 'inspiration',
                'sub_agent': 'inspiration',
                'confidence': 0.8,
                'entities': {},
                'urgency': 'low'
            }
        elif any(word in user_input_lower for word in ['help', 'urgent', 'emergency', 'problem']):
            return {
                'intent': 'emergency',
                'sub_agent': 'emergency',
                'confidence': 0.9,
                'entities': {},
                'urgency': 'high'
            }
        else:
            return {
                'intent': 'general_query',
                'sub_agent': 'assistant',
                'confidence': 0.6,
                'entities': {},
                'urgency': 'low'
            }
    
    async def _route_to_subagent(self, intent: Dict[str, Any], user_input: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate sub-agent"""
        sub_agent_name = intent.get('sub_agent', 'assistant')
        
        if sub_agent_name in self.subagents:
            return await self.subagents[sub_agent_name].process_request(
                user_input, user_id, context, intent
            )
        else:
            return await self.subagents['assistant'].process_request(
                user_input, user_id, context, intent
            )
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        user_history = [
            conv for conv in self.conversation_history 
            if conv['user_id'] == user_id
        ]
        return user_history[-limit:]
