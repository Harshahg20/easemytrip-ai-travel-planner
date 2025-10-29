"""
Agent Communication Protocol
Handles agent-to-agent communication and message routing
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Standard message format for agent communication"""
    message_id: str
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data


class AgentCommunicationProtocol:
    """
    Manages communication between agents
    Provides message routing, queuing, and delivery
    """
    
    def __init__(self):
        self.message_queue: List[AgentMessage] = []
        self.agent_registry: Dict[str, Any] = {}
        self.message_history: List[AgentMessage] = []
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register an agent for communication"""
        self.agent_registry[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    async def send_message(self, sender: str, receiver: str, 
                          message_type: MessageType,
                          payload: Dict[str, Any],
                          correlation_id: Optional[str] = None) -> AgentMessage:
        """Send a message from one agent to another"""
        message = AgentMessage(
            message_id=f"{sender}_{receiver}_{datetime.now().timestamp()}",
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now().isoformat(),
            correlation_id=correlation_id
        )
        
        self.message_queue.append(message)
        self.message_history.append(message)
        
        # Keep only last 100 messages
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        logger.info(f"Message sent: {sender} -> {receiver} ({message_type.value})")
        
        return message
    
    async def request_from_agent(self, requester: str, target_agent: str,
                                 request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Request information from another agent"""
        if target_agent not in self.agent_registry:
            raise ValueError(f"Agent {target_agent} not registered")
        
        message = await self.send_message(
            requester, target_agent, MessageType.REQUEST, request_payload
        )
        
        # This would trigger the target agent to process the request
        # For now, return the message
        return message.to_dict()
    
    async def notify_agent(self, sender: str, receiver: str,
                          notification: Dict[str, Any]):
        """Send notification to an agent"""
        await self.send_message(
            sender, receiver, MessageType.NOTIFICATION, notification
        )
    
    def get_message_history(self, agent_name: Optional[str] = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get message history, optionally filtered by agent"""
        history = self.message_history[-limit:]
        
        if agent_name:
            history = [
                msg for msg in history
                if msg.sender == agent_name or msg.receiver == agent_name
            ]
        
        return [msg.to_dict() for msg in history]
    
    def get_pending_messages(self, agent_name: str) -> List[AgentMessage]:
        """Get pending messages for an agent"""
        return [
            msg for msg in self.message_queue
            if msg.receiver == agent_name
        ]


# Global communication protocol instance
agent_communication = AgentCommunicationProtocol()
