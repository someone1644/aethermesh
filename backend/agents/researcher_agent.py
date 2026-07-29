from __future__ import annotations
from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("researcher")
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        return AgentResult(
            answer="Research completed.",
            confidence=0.95,
            metadata={
                "repository_found": True,
                "contradiction_score": 0.0,
                "sources": 5,
            },
        )