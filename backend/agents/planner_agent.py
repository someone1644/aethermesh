from __future__ import annotations
from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner")
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        return AgentResult(
            answer="Planning completed.",
            confidence=1.0,
            metadata={
                "repository_found": True,
                "contradiction_score": 0.0,
                "sources": 0,
            },
        )