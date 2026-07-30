
from typing import Optional

from policies.base_policy import BasePolicy
from models.execution_state import ExecutionState
from models.runtime_decision import RuntimeDecision

CONFIDENCE_THRESHOLD = 0.4


class LowConfidencePolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "LowConfidencePolicy"

    def evaluate(self, state: ExecutionState) -> Optional[RuntimeDecision]:
        if state.confidence < CONFIDENCE_THRESHOLD:
            return RuntimeDecision(
                action="insert_node",
                target_agent="ResearcherAgent",
                node_type="researcher",
                reason=(
                    f"Confidence {state.confidence:.2f} is below the "
                    f"required threshold of {CONFIDENCE_THRESHOLD:.2f}."
                ),
                source_policy=self.name,
                metadata={
                    "confidence": state.confidence,
                    "threshold": CONFIDENCE_THRESHOLD,
                },
            )
        return None