from __future__ import annotations

from policies.base_policy import BasePolicy
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction
from models.node import WorkflowNode

CONFIDENCE_THRESHOLD = 0.4


class LowConfidencePolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "LowConfidencePolicy"

    def evaluate(self, state: ExecutionState) -> RuntimeDecision:
        already_added = any(
            n.metadata.get("reason") == "confidence_boost"
            for n in state.workflow.nodes
        )
        if state.metrics.completed_agents > 0 and state.confidence < CONFIDENCE_THRESHOLD and not already_added:
            return RuntimeDecision(
                action=DecisionAction.ADD,
                new_node=WorkflowNode(
                    name="Extra research (low confidence)",
                    agent_type="researcher",
                    metadata={"reason": "confidence_boost"},
                ),
                reason=(
                    f"Confidence {state.confidence:.2f} is below the "
                    f"required threshold of {CONFIDENCE_THRESHOLD:.2f}."
                ),
                policy_name=self.name,
                priority=2,
                metadata={
                    "confidence": state.confidence,
                    "threshold": CONFIDENCE_THRESHOLD,
                },
            )
        return RuntimeDecision(policy_name=self.name)