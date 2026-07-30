from __future__ import annotations

import logging
import time
from copy import deepcopy
from typing import Any

from agents.context_utils import format_shared_context
from agents.registry import AgentRegistry
from config import settings

from models.agent_result import AgentResult
from models.event import EventType
from models.execution import ExecutionState
from models.node import WorkflowNode
from models.runtime_decision import DecisionAction

from runtime.decision_engine import DecisionEngine
from runtime.event_logger import EventLogger
from runtime.mutation_engine import MutationEngine
from runtime.policy_engine import PolicyEngine
from runtime.state_manager import StateManager
from runtime.workflow_graph import next_ready_node

logger = logging.getLogger(__name__)

_GEMINI_AGENTS = frozenset({"planner", "researcher"})


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
        shared_context: dict[str, str] = {}
        delay_s = max(0.0, settings.GEMINI_AGENT_DELAY_SECONDS)

        while workflow.has_next():

            # Graph-aware selection: the next PENDING/READY node in
            # topological order (networkx), not just list position — same
            # result as before for today's linear workflows, but correct
            # if a workflow ever branches.
            node = next_ready_node(workflow)

            if node is None:
                break

            workflow.current_node = node.id

            if delay_s > 0:
                time.sleep(delay_s)

            prepared = self._prepare_node(node, shared_context)

            manager.mark_node_active(prepared)

            self.logger.agent_started(
                state,
                prepared.id,
                prepared.agent_type,
            )

            try:
                result = self.execute_agent(prepared)
            except Exception as exc:
                logger.error(
                    "Agent '%s' (node=%s) crashed: %s",
                    prepared.agent_type,
                    prepared.id,
                    exc,
                )
                manager.mark_node_failed(prepared)
                self.logger.agent_completed(
                    state,
                    prepared.id,
                    prepared.agent_type,
                    confidence=0.0,
                    failed=True,
                )
                continue

            shared_context[prepared.agent_type] = result.answer

            self.process_result(
                manager,
                prepared,
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
            manager.mark_node_completed(prepared)

            self.logger.agent_completed(
                state,
                prepared.id,
                prepared.agent_type,
                confidence=result.confidence,
            )

        elapsed = time.time() - start_time
        manager.set_execution_time(elapsed)

        manager.complete_execution()

        self.logger.workflow_completed(state)

        return manager.get_state()

    @staticmethod
    def _prepare_node(
        node: WorkflowNode,
        shared_context: dict[str, str],
    ) -> WorkflowNode:
        """Inject accumulated context before an agent runs."""
        prepared = deepcopy(node)
        metadata: dict[str, Any] = dict(prepared.metadata)
        metadata["shared_context"] = dict(shared_context)

        if prepared.agent_type in ("coder", "reviewer", "evaluator"):
            metadata["context"] = format_shared_context(shared_context)

        if prepared.agent_type in ("reviewer", "evaluator"):
            metadata["artifact"] = shared_context.get(
                "coder",
                shared_context.get("plan", shared_context.get("planner", "")),
            )

        prepared.metadata = metadata
        return prepared

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

        manager.apply_agent_result(result, agent_type=node.agent_type)

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
                        name=decision.new_node.name,
                        agent_type=decision.new_node.agent_type,
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
                        name=decision.new_node.name,
                        agent_type=decision.new_node.agent_type,
                    )

            else:

                # MutationEngine rejects a mutation that would leave the
                # workflow graph with a cycle (or is otherwise malformed) —
                # don't silently drop it, record why.
                self.logger.log(
                    state,
                    EventType.POLICY_TRIGGERED,
                    (
                        f"Mutation rejected — applying it would break the "
                        f"workflow graph (policy={decision.policy_name}, "
                        f"action={decision.action.value})."
                    ),
                    {
                        "policy": decision.policy_name,
                        "action": decision.action.value,
                        "rejected": True,
                    },
                )