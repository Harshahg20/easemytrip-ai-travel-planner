"""
Advanced Orchestrator Agent with Gemini-powered Intent Analysis
Coordinates multiple agents for precise responses
"""
import asyncio
from typing import Dict, List, Any, Optional
import json
import logging
from google.cloud import aiplatform
import google.generativeai as genai

from ...core.config import settings
from .shared_context import shared_context

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Advanced orchestrator that coordinates multiple agents
    Uses Gemini for intelligent intent analysis and routing
    """
    
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
        self.subagents = {}
        self.gemini_model = None
        
        # Initialize AI Platform
        try:
            aiplatform.init(project=project_id, location=region)
            logger.info(f"AI Platform initialized for project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AI Platform: {e}")
        
        # Initialize Gemini model for intent analysis
        self._initialize_gemini()
        
        # Initialize sub-agents
        self._initialize_subagents()
    
    def _initialize_gemini(self):
        """Initialize Gemini model for intent analysis"""
        try:
            # Load API key the same way as GoogleAIService
            api_key = None
            try:
                from dotenv import load_dotenv
                import os
                # Try multiple possible paths for .env file
                env_paths = [
                    '.env',
                    os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),
                    os.path.join(os.getcwd(), '.env'),
                ]
                
                for env_path in env_paths:
                    abs_path = os.path.abspath(env_path)
                    if os.path.exists(abs_path):
                        load_dotenv(dotenv_path=abs_path, override=True)
                        api_key = os.getenv('GOOGLE_AI_API_KEY')
                        if api_key:
                            api_key = api_key.strip('"').strip("'")
                            break
                
                if not api_key:
                    load_dotenv(override=True)
                    api_key = os.getenv('GOOGLE_AI_API_KEY')
                    if api_key:
                        api_key = api_key.strip('"').strip("'")
            except Exception as e:
                logger.warning(f"Could not load API key from .env: {e}")
            
            # Fallback to settings
            if not api_key or len(api_key) < 30:
                api_key = settings.google_ai_api_key
                if api_key:
                    api_key = api_key.strip('"').strip("'")
            
            if api_key and len(api_key) >= 30:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini model initialized for intent analysis")
            else:
                logger.warning("Google AI API key not configured, using rule-based intent analysis")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
    
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
        logger.info(f"Initialized {len(self.subagents)} sub-agents")
    
    async def process_request(self, user_input: str, user_id: str, 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing user requests
        Uses Gemini for intent analysis and coordinates agents
        """
        try:
            # Get user context from shared memory
            user_context = shared_context.get_user_context(user_id)
            
            # Merge provided context with stored context
            full_context = {**user_context, **(context or {})}
            
            # Analyze intent using Gemini
            intent = await self._analyze_intent_with_gemini(user_input, full_context)
            
            # Store entities in shared context
            if intent.get('entities'):
                shared_context.extract_and_store_entities(user_id, intent['entities'])
            
            # Determine if multiple agents are needed
            if self._requires_multi_agent(intent):
                response = await self._orchestrate_multiple_agents(
                    intent, user_input, user_id, full_context
                )
            else:
                # Single agent routing
                response = await self._route_to_single_agent(
                    intent, user_input, user_id, full_context
                )
            
            # Update conversation history
            shared_context.add_to_history(user_id, {
                'input': user_input,
                'intent': intent,
                'response': response,
                'agent_used': intent.get('sub_agent', 'unknown')
            })
            
            # Store in agent memory
            agent_name = intent.get('sub_agent', 'orchestrator')
            shared_context.store_agent_memory(user_id, agent_name, {
                'last_query': user_input,
                'last_response': response,
                'entities': intent.get('entities', {})
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)
            return {
                'type': 'error',
                'message': 'I apologize, but I encountered an error. Please try again.',
                'suggestions': ['Try rephrasing your request', 'Contact support if the issue persists']
            }
    
    async def _analyze_intent_with_gemini(self, user_input: str, 
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini for intelligent intent analysis"""
        if not self.gemini_model:
            return self._rule_based_intent_analysis(user_input, context)
        
        try:
            # Build context from shared memory
            history = shared_context.get_recent_history(context.get('user_id', 'unknown'), limit=5)
            history_text = '\n'.join([
                f"User: {h.get('input', '')}\nAssistant: {h.get('response', {}).get('message', '')}"
                for h in history[-3:]  # Last 3 interactions
            ])
            
            prompt = f"""
You are an intelligent travel concierge intent analyzer. Analyze the following user input and determine:
1. Primary intent (inspiration, planning, booking, assistant, emergency)
2. Required sub-agent(s)
3. Extracted entities (destination, dates, budget, travelers, etc.)
4. Confidence score (0.0-1.0)
5. Urgency level (low, medium, high)
6. Whether multiple agents need to collaborate

Available agents:
- inspiration: Destination discovery, travel ideas, trending places
- planning: Itinerary creation, trip planning, scheduling
- booking: Flight/hotel/activity reservations
- assistant: Real-time assistance, questions, support
- emergency: Urgent situations, crisis management

User Input: "{user_input}"

Conversation History:
{history_text}

Current Context:
{json.dumps(context.get('trip_data', {}), indent=2)}

Extracted Entities (if any):
{json.dumps(context.get('entities', {}), indent=2)}

Return ONLY valid JSON in this exact format:
{{
    "intent": "primary_intent_name",
    "sub_agent": "primary_agent_name",
    "collaborating_agents": ["agent1", "agent2"] or [],
    "confidence": 0.95,
    "entities": {{
        "destination": "destination_name" or null,
        "start_date": "YYYY-MM-DD" or null,
        "end_date": "YYYY-MM-DD" or null,
        "budget": number or null,
        "travelers": number or null,
        "interests": ["interest1", "interest2"] or []
    }},
    "urgency": "low|medium|high",
    "requires_multi_agent": true or false,
    "reasoning": "Brief explanation of intent analysis"
}}
"""
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            # Parse Gemini response
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            intent_data = json.loads(response_text)
            
            logger.info(f"Gemini intent analysis: {intent_data.get('intent')} "
                       f"(confidence: {intent_data.get('confidence', 0)})")
            
            return intent_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Gemini response: {response_text}")
            return self._rule_based_intent_analysis(user_input, context)
        except Exception as e:
            logger.error(f"Error in Gemini intent analysis: {e}")
            return self._rule_based_intent_analysis(user_input, context)
    
    def _rule_based_intent_analysis(self, user_input: str, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based intent analysis"""
        user_input_lower = user_input.lower()
        
        # Check for booking keywords
        if any(word in user_input_lower for word in ['book', 'reserve', 'buy', 'purchase']):
            return {
                'intent': 'booking',
                'sub_agent': 'booking',
                'collaborating_agents': [],
                'confidence': 0.75,
                'entities': {},
                'urgency': 'medium',
                'requires_multi_agent': False,
                'reasoning': 'Booking-related keywords detected'
            }
        # Check for planning keywords
        elif any(word in user_input_lower for word in ['plan', 'itinerary', 'schedule', 'organize']):
            return {
                'intent': 'planning',
                'sub_agent': 'planning',
                'collaborating_agents': ['inspiration'],
                'confidence': 0.80,
                'entities': {},
                'urgency': 'low',
                'requires_multi_agent': True,
                'reasoning': 'Planning request may benefit from inspiration agent'
            }
        # Check for inspiration keywords
        elif any(word in user_input_lower for word in ['inspire', 'discover', 'suggest', 'recommend']):
            return {
                'intent': 'inspiration',
                'sub_agent': 'inspiration',
                'collaborating_agents': [],
                'confidence': 0.75,
                'entities': {},
                'urgency': 'low',
                'requires_multi_agent': False,
                'reasoning': 'Inspiration-related keywords detected'
            }
        # Check for emergency keywords
        elif any(word in user_input_lower for word in ['help', 'urgent', 'emergency', 'problem', 'stuck']):
            return {
                'intent': 'emergency',
                'sub_agent': 'emergency',
                'collaborating_agents': [],
                'confidence': 0.90,
                'entities': {},
                'urgency': 'high',
                'requires_multi_agent': False,
                'reasoning': 'Emergency keywords detected'
            }
        else:
            return {
                'intent': 'general_query',
                'sub_agent': 'assistant',
                'collaborating_agents': [],
                'confidence': 0.60,
                'entities': {},
                'urgency': 'low',
                'requires_multi_agent': False,
                'reasoning': 'General query, routing to assistant agent'
            }
    
    def _requires_multi_agent(self, intent: Dict[str, Any]) -> bool:
        """Check if request requires multiple agents"""
        return intent.get('requires_multi_agent', False) or \
               len(intent.get('collaborating_agents', [])) > 0
    
    async def _orchestrate_multiple_agents(self, intent: Dict[str, Any], 
                                          user_input: str, user_id: str,
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple agents for complex requests"""
        primary_agent = intent.get('sub_agent', 'assistant')
        collaborating_agents = intent.get('collaborating_agents', [])
        
        logger.info(f"Orchestrating: Primary={primary_agent}, "
                   f"Collaborating={collaborating_agents}")
        
        # Execute primary agent
        primary_response = await self._execute_agent(
            primary_agent, user_input, user_id, context, intent
        )
        
        # Execute collaborating agents in parallel
        if collaborating_agents:
            collaborator_tasks = [
                self._execute_agent(agent, user_input, user_id, context, intent)
                for agent in collaborating_agents
                if agent in self.subagents
            ]
            
            collaborator_responses = await asyncio.gather(*collaborator_tasks, return_exceptions=True)
            
            # Combine responses
            return self._combine_agent_responses(
                primary_response, collaborator_responses, intent
            )
        
        return primary_response
    
    async def _route_to_single_agent(self, intent: Dict[str, Any],
                                    user_input: str, user_id: str,
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Route to a single agent"""
        agent_name = intent.get('sub_agent', 'assistant')
        return await self._execute_agent(agent_name, user_input, user_id, context, intent)
    
    async def _execute_agent(self, agent_name: str, user_input: str,
                            user_id: str, context: Dict[str, Any],
                            intent: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent"""
        if agent_name not in self.subagents:
            logger.warning(f"Agent {agent_name} not found, using assistant")
            agent_name = 'assistant'
        
        try:
            agent = self.subagents[agent_name]
            
            # Get agent-specific memory
            agent_memory = shared_context.get_agent_memory(user_id, agent_name)
            enhanced_context = {**context, 'agent_memory': agent_memory}
            
            response = await agent.process_request(
                user_input, user_id, enhanced_context, intent
            )
            
            # Store agent response in memory
            shared_context.store_agent_memory(user_id, agent_name, {
                'last_response': response,
                'timestamp': asyncio.get_event_loop().time()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing agent {agent_name}: {e}")
            return {
                'type': 'error',
                'message': f'Error processing request with {agent_name} agent',
                'agent': agent_name
            }
    
    def _combine_agent_responses(self, primary_response: Dict[str, Any],
                                collaborator_responses: List[Dict[str, Any]],
                                intent: Dict[str, Any]) -> Dict[str, Any]:
        """Combine responses from multiple agents"""
        combined = {
            'type': 'multi_agent_response',
            'primary': primary_response,
            'collaborators': [],
            'combined_message': primary_response.get('message', ''),
            'suggestions': primary_response.get('suggestions', [])
        }
        
        # Add collaborator responses
        for response in collaborator_responses:
            if isinstance(response, Exception):
                logger.error(f"Collaborator agent error: {response}")
                continue
            
            combined['collaborators'].append(response)
            
            # Enhance combined message with collaborator insights
            if response.get('message'):
                combined['combined_message'] += f"\n\nAdditional insights: {response['message']}"
        
        return combined
