from __future__ import annotations

from runtime.state_manager import StateManager

from models.runtime_decision import (
    DecisionAction,
    RuntimeDecision,
)


class MutationEngine:

    def apply(
        self,
        manager: StateManager,
        decision: RuntimeDecision,
    ) -> bool:

        workflow = manager.state.workflow

        if decision.action == DecisionAction.NONE:
            return False

        if decision.action == DecisionAction.ADD:

            if decision.new_node is None:
                return False

            workflow.add_node(decision.new_node)

            manager.increment_mutations()

            return True

        if decision.action == DecisionAction.REMOVE:

            if decision.target_node is None:
                return False

            workflow.remove_node(decision.target_node)

            manager.increment_mutations()

            return True

        if decision.action == DecisionAction.REPLACE:

            if (
                decision.target_node is None
                or decision.new_node is None
            ):
                return False

            workflow.replace_node(
                decision.target_node,
                decision.new_node,
            )

            manager.increment_mutations()

            return True

        return False