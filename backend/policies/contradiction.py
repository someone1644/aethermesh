

from typing import Optional

from policies.base_policy import BasePolicy
from models.execution_state import ExecutionState
from models.runtime_decision import RuntimeDecision

CONTRADICTION_THRESHOLD = 0.6


class ContradictionPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "ContradictionPolicy"

    def evaluate(self, state: ExecutionState) -> Optional[RuntimeDecision]:
        if state.contradiction_score > CONTRADICTION_THRESHOLD:
            return RuntimeDecision(
                action="replace_node",
                target_agent="EvaluatorAgent",
                node_type="evaluator",
                reason=(
                    f"Contradiction score {state.contradiction_score:.2f} "
                    f"exceeds threshold {CONTRADICTION_THRESHOLD:.2f}."
                ),
                source_policy=self.name,
                metadata={
                    "contradiction_score": state.contradiction_score,
                    "threshold": CONTRADICTION_THRESHOLD,
                    "replaced_node_type": "reviewer",
                },
            )
        return None