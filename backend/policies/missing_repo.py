

from typing import Optional

from policies.base_policy import BasePolicy
from models.execution_state import ExecutionState
from models.runtime_decision import RuntimeDecision


class MissingRepoPolicy(BasePolicy):
    """Reads ExecutionState only. Never mutates Workflow or ExecutionState."""

    name = "MissingRepoPolicy"

    def evaluate(self, state: ExecutionState) -> Optional[RuntimeDecision]:
        if not state.repository_found:
            return RuntimeDecision(
                action="insert_node",
                target_agent="ResearcherAgent",
                node_type="repository_search",
                reason="No repository was located during execution.",
                source_policy=self.name,
                metadata={"repository_found": state.repository_found},
            )
        return None