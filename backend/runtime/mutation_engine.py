from __future__ import annotations

from copy import deepcopy

from models.runtime_decision import (
    DecisionAction,
    RuntimeDecision,
)
from models.workflow import Workflow
from runtime.state_manager import StateManager
from runtime.workflow_graph import is_valid_dag


class MutationEngine:

    def apply(
        self,
        manager: StateManager,
        decision: RuntimeDecision,
    ) -> bool:

        workflow = manager.state.workflow

        if decision.action == DecisionAction.NONE:
            return False

        if decision.action == DecisionAction.ADD and decision.new_node is None:
            return False

        if decision.action == DecisionAction.REMOVE and decision.target_node is None:
            return False

        if decision.action == DecisionAction.REPLACE and (
            decision.target_node is None or decision.new_node is None
        ):
            return False

        # Simulate on a scratch copy first — reject the mutation outright
        # if it would leave the workflow graph with a cycle, rather than
        # committing a broken graph and discovering it during execution.
        scratch = deepcopy(workflow)
        self._mutate(scratch, decision)

        if not is_valid_dag(scratch):
            return False

        self._mutate(workflow, decision)

        manager.increment_mutations()

        return True

    @staticmethod
    def _mutate(
        workflow: Workflow,
        decision: RuntimeDecision,
    ) -> None:
        """Apply *decision*'s node/edge change to *workflow* in place."""

        if decision.action == DecisionAction.ADD:

            workflow.add_node(decision.new_node)

            # Wire the new node in after whatever was just executing, so it
            # has a real dependency edge instead of floating disconnected
            # in the graph (which would leave its execution order
            # undefined relative to the rest of the workflow).
            if workflow.current_node:
                workflow.add_edge(workflow.current_node, decision.new_node.id)

        elif decision.action == DecisionAction.REMOVE:

            workflow.remove_node(decision.target_node)

        elif decision.action == DecisionAction.REPLACE:

            workflow.replace_node(
                decision.target_node,
                decision.new_node,
            )
