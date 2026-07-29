from __future__ import annotations
from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__("coder")
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        return AgentResult(
            answer="Code generated.",
            confidence=0.93,
            metadata={},
        )