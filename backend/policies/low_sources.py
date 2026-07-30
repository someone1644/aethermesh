from __future__ import annotations

from typing import Optional

from policies.base_policy import BasePolicy
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction
from models.node import WorkflowNode

DEFAULT_MIN_SOURCES = 3


class LowSourcesPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "LowSourcesPolicy"

    def __init__(self, min_sources: Optional[int] = None):
        self.min_sources = min_sources if min_sources is not None else DEFAULT_MIN_SOURCES

    def evaluate(self, state: ExecutionState) -> RuntimeDecision:
        # state.sources is an int, not a list
        source_count: int = state.sources

        already_added = any(
            n.metadata.get("reason") == "source_augmentation"
            for n in state.workflow.nodes
        )
        if state.metrics.completed_agents > 0 and source_count < self.min_sources and not already_added:
            return RuntimeDecision(
                action=DecisionAction.ADD,
                new_node=WorkflowNode(
                    name="Gather more sources",
                    agent_type="researcher",
                    metadata={"reason": "source_augmentation"},
                ),
                reason=(
                    f"Only {source_count} source(s) found; minimum "
                    f"required is {self.min_sources}."
                ),
                policy_name=self.name,
                priority=1,
                metadata={
                    "source_count": source_count,
                    "min_sources": self.min_sources,
                },
            )
        return RuntimeDecision(policy_name=self.name)