"""
Shared Context System for Multi-Agent Orchestration
Manages shared memory and context across all agents
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SharedContext:
    """
    Shared memory system for coordinating agents
    Stores user context, entities, preferences, and conversation history
    """
    
    def __init__(self):
        self.context_store: Dict[str, Dict[str, Any]] = {}
        self.entity_store: Dict[str, Dict[str, Any]] = {}
        self.preference_store: Dict[str, Dict[str, Any]] = {}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.agent_memory: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete context for a user"""
        return {
            'user_id': user_id,
            'entities': self.entity_store.get(user_id, {}),
            'preferences': self.preference_store.get(user_id, {}),
            'history': self.conversation_history.get(user_id, []),
            'trip_data': self.context_store.get(user_id, {}).get('trip_data', {}),
            'current_task': self.context_store.get(user_id, {}).get('current_task', None)
        }
    
    def update_context(self, user_id: str, context_updates: Dict[str, Any]):
        """Update user context"""
        if user_id not in self.context_store:
            self.context_store[user_id] = {}
        
        self.context_store[user_id].update(context_updates)
        self.context_store[user_id]['last_updated'] = datetime.now().isoformat()
    
    def extract_and_store_entities(self, user_id: str, entities: Dict[str, Any]):
        """Extract and store entities from user input"""
        if user_id not in self.entity_store:
            self.entity_store[user_id] = {}
        
        self.entity_store[user_id].update(entities)
        self.entity_store[user_id]['last_updated'] = datetime.now().isoformat()
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        if user_id not in self.preference_store:
            self.preference_store[user_id] = {}
        
        self.preference_store[user_id].update(preferences)
    
    def add_to_history(self, user_id: str, interaction: Dict[str, Any]):
        """Add interaction to conversation history"""
        interaction['timestamp'] = datetime.now().isoformat()
        self.conversation_history[user_id].append(interaction)
        
        # Keep only last 50 interactions
        if len(self.conversation_history[user_id]) > 50:
            self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
    
    def get_recent_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[user_id][-limit:]
    
    def store_agent_memory(self, user_id: str, agent_name: str, memory: Dict[str, Any]):
        """Store agent-specific memory"""
        key = f"{user_id}:{agent_name}"
        self.agent_memory[key].update(memory)
    
    def get_agent_memory(self, user_id: str, agent_name: str) -> Dict[str, Any]:
        """Retrieve agent-specific memory"""
        key = f"{user_id}:{agent_name}"
        return self.agent_memory.get(key, {})
    
    def clear_context(self, user_id: str):
        """Clear all context for a user"""
        self.context_store.pop(user_id, None)
        self.entity_store.pop(user_id, None)
        self.preference_store.pop(user_id, None)
        self.conversation_history[user_id] = []
        
        # Clear agent memory for this user
        keys_to_remove = [k for k in self.agent_memory.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.agent_memory[key]


# Global shared context instance
shared_context = SharedContext()
