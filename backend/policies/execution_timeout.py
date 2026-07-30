

from typing import Optional

from policies.base_policy import BasePolicy
from models.execution_state import ExecutionState
from models.runtime_decision import RuntimeDecision
import config

DEFAULT_TIMEOUT_SECONDS = 30.0


class ExecutionTimeoutPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "ExecutionTimeoutPolicy"

    def __init__(self, timeout_seconds: Optional[float] = None):
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(config, "EXECUTION_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
        )

    def evaluate(self, state: ExecutionState) -> Optional[RuntimeDecision]:
        if state.execution_time > self.timeout_seconds:
            return RuntimeDecision(
                action="skip_node",
                target_agent=None,
                node_type=None,
                reason=(
                    f"Execution time {state.execution_time:.2f}s exceeded "
                    f"timeout of {self.timeout_seconds:.2f}s."
                ),
                source_policy=self.name,
                metadata={
                    "execution_time": state.execution_time,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
        return None