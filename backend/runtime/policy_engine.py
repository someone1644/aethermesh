from __future__ import annotations
from typing import List
from models.execution import ExecutionState
from models.runtime_decision import RuntimeDecision, DecisionAction
from policies.base_policy import BasePolicy
class PolicyEngine:
    """
    Evaluates all registered policies against the current
    execution state.
    Policies never mutate the workflow directly.
    They only return RuntimeDecision objects.
    """
    def __init__(
        self,
        policies: List[BasePolicy] | None = None,
    ):
        self.policies = policies or []

    def register_policy(
        self,
        policy: BasePolicy,
    ) -> None:
        """
        Register a new runtime policy.
        """
        self.policies.append(policy)

    def evaluate(
        self,
        state: ExecutionState,
    ) -> List[RuntimeDecision]:
        """
        Execute every policy and collect all actionable
        runtime decisions.
        """

        decisions: List[RuntimeDecision] = []

        for policy in self.policies:

            decision = policy.evaluate(state)

            if decision.action != DecisionAction.NONE:
                decisions.append(decision)

        return decisions

    def clear(self) -> None:
        """
        Remove every registered policy.
        """
        self.policies.clear()

    def count(self) -> int:
        """
        Number of registered policies.
        """
        return len(self.policies)