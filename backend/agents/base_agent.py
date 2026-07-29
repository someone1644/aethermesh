from __future__ import annotations
from abc import ABC, abstractmethod
from models.agent_result import AgentResult
from models.node import WorkflowNode
class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
    ):
        self.name = name
    @abstractmethod
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        """
        Execute the agent for the given workflow node.
        """
        raise NotImplementedError