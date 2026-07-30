from __future__ import annotations

from typing import Optional

from policies.base_policy import BasePolicy
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction

DEFAULT_TIMEOUT_SECONDS = 30.0


class ExecutionTimeoutPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "ExecutionTimeoutPolicy"

    def __init__(self, timeout_seconds: Optional[float] = None):
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else DEFAULT_TIMEOUT_SECONDS
        )

    def evaluate(self, state: ExecutionState) -> RuntimeDecision:
        # execution_time lives on state.metrics, not state directly
        if state.metrics.execution_time > self.timeout_seconds:
            return RuntimeDecision(
                action=DecisionAction.REMOVE,
                target_node=state.workflow.current_node,
                reason=(
                    f"Execution time {state.metrics.execution_time:.2f}s exceeded "
                    f"timeout of {self.timeout_seconds:.2f}s."
                ),
                policy_name=self.name,
                priority=4,
                metadata={
                    "execution_time": state.metrics.execution_time,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
        return RuntimeDecision(policy_name=self.name)