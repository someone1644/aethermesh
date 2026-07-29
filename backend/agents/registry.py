from __future__ import annotations
from typing import Dict
from agents.base_agent import BaseAgent
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    def register(
        self,
        agent_type: str,
        agent: BaseAgent,
    ) -> None:
        self._agents[agent_type] = agent
    def get(
        self,
        agent_type: str,
    ) -> BaseAgent | None:
        return self._agents.get(agent_type)
    def all(self) -> Dict[str, BaseAgent]:
        return self._agents