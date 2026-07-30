from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from models.agent_result import AgentResult
from models.node import WorkflowNode


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        gemini_client: Optional[object] = None,
    ):
        self.name = name
        self.gemini = gemini_client  # type: ignore[assignment]

    @abstractmethod
    def run(
        self,
        node: WorkflowNode,
    ) -> AgentResult:
        """
        Execute the agent for the given workflow node.
        """
        raise NotImplementedError