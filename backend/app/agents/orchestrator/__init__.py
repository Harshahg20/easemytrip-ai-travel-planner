"""
Orchestrator package for multi-agent coordination
"""
from .orchestrator_agent import OrchestratorAgent
from .shared_context import shared_context, SharedContext
from .agent_communication import agent_communication, AgentCommunicationProtocol

__all__ = [
    'OrchestratorAgent',
    'shared_context',
    'SharedContext',
    'agent_communication',
    'AgentCommunicationProtocol'
]
