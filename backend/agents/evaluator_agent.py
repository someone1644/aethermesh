from __future__ import annotations
from agents.base_agent import BaseAgent
from models.agent_result import AgentResult
from models.node import WorkflowNode
class EvaluatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("evaluator")
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        return AgentResult(
            answer="Evaluation completed.",
            confidence=0.97,
            metadata={},
        )