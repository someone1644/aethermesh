from __future__ import annotations
from abc import ABC, abstractmethod
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision
class BasePolicy(ABC):
    """
    Base class for all runtime safety policies.
    """
    name: str = "Base Policy"
    @abstractmethod
    def evaluate(
        self,
        state: ExecutionState,
    ) -> RuntimeDecision:
        """
        Inspect the execution state and return a RuntimeDecision.

        Return DecisionAction.NONE if no action is required.
        """
        pass