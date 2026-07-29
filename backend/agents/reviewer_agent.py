from __future__ import annotations
from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("reviewer")
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        return AgentResult(
            answer="Review completed.",
            confidence=0.96,
            metadata={},
        )