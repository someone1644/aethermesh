from __future__ import annotations

from policies.base_policy import BasePolicy
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction
from models.node import WorkflowNode

CONTRADICTION_THRESHOLD = 0.6


class ContradictionPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "ContradictionPolicy"

    def evaluate(self, state: ExecutionState) -> RuntimeDecision:
        already_added = any(
            n.metadata.get("reason") == "contradiction_resolution"
            for n in state.workflow.nodes
        )
        if state.contradiction_score > CONTRADICTION_THRESHOLD and not already_added:
            return RuntimeDecision(
                action=DecisionAction.ADD,
                new_node=WorkflowNode(
                    name="Re-evaluate (contradiction detected)",
                    agent_type="evaluator",
                    metadata={"reason": "contradiction_resolution"},
                ),
                reason=(
                    f"Contradiction score {state.contradiction_score:.2f} "
                    f"exceeds threshold {CONTRADICTION_THRESHOLD:.2f}."
                ),
                policy_name=self.name,
                priority=2,
                metadata={
                    "contradiction_score": state.contradiction_score,
                    "threshold": CONTRADICTION_THRESHOLD,
                },
            )
        return RuntimeDecision(policy_name=self.name)