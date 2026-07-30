
from typing import Optional

from policies.base_policy import BasePolicy
from models.execution_state import ExecutionState
from models.runtime_decision import RuntimeDecision
import config

DEFAULT_MIN_SOURCES = 3


class LowSourcesPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "LowSourcesPolicy"

    def __init__(self, min_sources: Optional[int] = None):
        self.min_sources = (
            min_sources
            if min_sources is not None
            else getattr(config, "MIN_SOURCES_THRESHOLD", DEFAULT_MIN_SOURCES)
        )

    def evaluate(self, state: ExecutionState) -> Optional[RuntimeDecision]:
        source_count = len(getattr(state, "sources", None) or [])

        if source_count < self.min_sources:
            return RuntimeDecision(
                action="insert_node",
                target_agent="ResearcherAgent",
                node_type="researcher",
                reason=(
                    f"Only {source_count} source(s) found; minimum "
                    f"required is {self.min_sources}."
                ),
                source_policy=self.name,
                metadata={
                    "source_count": source_count,
                    "min_sources": self.min_sources,
                },
            )
        return None