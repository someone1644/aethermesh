from __future__ import annotations

from policies.base_policy import BasePolicy
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction
from models.node import WorkflowNode


class MissingRepoPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "MissingRepoPolicy"

    def evaluate(self, state: ExecutionState) -> RuntimeDecision:
        already_added = any(
            n.metadata.get("reason") == "repository_search"
            for n in state.workflow.nodes
        )
        if not state.repository_found and not already_added:
            return RuntimeDecision(
                action=DecisionAction.ADD,
                new_node=WorkflowNode(
                    name="Repository search",
                    agent_type="researcher",
                    metadata={"reason": "repository_search"},
                ),
                reason="No repository was located during execution.",
                policy_name=self.name,
                priority=3,
                metadata={"repository_found": state.repository_found},
            )
        return RuntimeDecision(policy_name=self.name)