from __future__ import annotations

from typing import List, Optional

from models.runtime_decision import RuntimeDecision


class DecisionEngine:
    """
    Resolves conflicts between multiple runtime decisions.

    The PolicyEngine may return several RuntimeDecision objects.
    The DecisionEngine selects the one that should be executed.
    """

    def select(
        self,
        decisions: List[RuntimeDecision],
    ) -> Optional[RuntimeDecision]:
        """
        Return the highest-priority decision.

        Returns None if there are no decisions.
        """

        if not decisions:
            return None

        return max(
            decisions,
            key=lambda decision: decision.priority,
        )

    def sort(
        self,
        decisions: List[RuntimeDecision],
    ) -> List[RuntimeDecision]:
        """
        Return all decisions sorted by priority.
        """

        return sorted(
            decisions,
            key=lambda decision: decision.priority,
            reverse=True,
        )