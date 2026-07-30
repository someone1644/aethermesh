from __future__ import annotations

import logging
import time

from agents.registry import AgentRegistry

from models.agent_result import AgentResult
from models.execution import ExecutionState
from models.node import WorkflowNode
from models.runtime_decision import DecisionAction

from runtime.decision_engine import DecisionEngine
from runtime.event_logger import EventLogger
from runtime.mutation_engine import MutationEngine
from runtime.policy_engine import PolicyEngine
from runtime.state_manager import StateManager

logger = logging.getLogger(__name__)


class RuntimeEngine:

    def __init__(
        self,
        policy_engine: PolicyEngine,
        registry: AgentRegistry,
        event_logger: EventLogger | None = None,
    ):
        self.policy_engine = policy_engine
        self.registry = registry

        self.decision_engine = DecisionEngine()
        self.mutation_engine = MutationEngine()
        self.logger = event_logger or EventLogger()

    def execute(
        self,
        state: ExecutionState,
    ) -> ExecutionState:

        manager = StateManager(state)

        manager.start_execution()

        self.logger.workflow_started(state)

        start_time = time.time()

        workflow = state.workflow

        while workflow.has_next():

            node = workflow.get_next_node()

            if node is None:
                break

            manager.mark_node_active(node)

            self.logger.agent_started(
                state,
                node.id,
                node.agent_type,
            )

            try:
                result = self.execute_agent(node)
            except Exception as exc:
                logger.error(
                    "Agent '%s' (node=%s) crashed: %s",
                    node.agent_type,
                    node.id,
                    exc,
                )
                manager.mark_node_failed(node)
                self.logger.agent_completed(
                    state,
                    node.id,
                    node.agent_type,
                    confidence=0.0,
                )
                continue

            self.process_result(
                manager,
                node,
                result,
            )

            # Update current elapsed execution time before evaluating policies
            manager.set_execution_time(time.time() - start_time)

            # Evaluate policies and apply mutations while node is active
            try:
                self._evaluate_and_mutate(manager, state)
            except Exception as exc:
                logger.error(
                    "Policy evaluation failed: %s",
                    exc,
                )

            # Mark node completed after policy evaluation
            manager.mark_node_completed(node)

            self.logger.agent_completed(
                state,
                node.id,
                node.agent_type,
                confidence=result.confidence,
            )

        elapsed = time.time() - start_time
        manager.set_execution_time(elapsed)

        manager.complete_execution()

        self.logger.workflow_completed(state)

        return manager.get_state()

    def execute_agent(
        self,
        node: WorkflowNode,
    ) -> AgentResult:

        agent = self.registry.get(node.agent_type)

        if agent is None:
            raise ValueError(
                f"No registered agent for '{node.agent_type}'"
            )

        return agent.run(node)

    def process_result(
        self,
        manager: StateManager,
        node: WorkflowNode,
        result: AgentResult,
    ) -> None:

        manager.apply_agent_result(result)

    def _evaluate_and_mutate(
        self,
        manager: StateManager,
        state: ExecutionState,
    ) -> None:
        """Run policies, pick the winning decision, apply mutation."""

        decisions = self.policy_engine.evaluate(
            manager.state,
        )

        decision = self.decision_engine.select(
            decisions,
        )

        if decision is not None:

            self.logger.policy_triggered(
                state,
                decision.policy_name,
                decision.reason,
            )

            applied = self.mutation_engine.apply(
                manager,
                decision,
            )

            if applied:

                if decision.action == DecisionAction.ADD:

                    self.logger.node_added(
                        state,
                        decision.new_node.id,
                    )

                elif decision.action == DecisionAction.REMOVE:

                    self.logger.node_removed(
                        state,
                        decision.target_node,
                    )

                elif decision.action == DecisionAction.REPLACE:

                    self.logger.node_replaced(
                        state,
                        decision.target_node,
                        decision.new_node.id,
                    )