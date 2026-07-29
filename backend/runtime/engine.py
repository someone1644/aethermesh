from __future__ import annotations

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


class RuntimeEngine:

    def __init__(
        self,
        policy_engine: PolicyEngine,
        registry: AgentRegistry,
    ):
        self.policy_engine = policy_engine
        self.registry = registry

        self.decision_engine = DecisionEngine()
        self.mutation_engine = MutationEngine()
        self.logger = EventLogger()

    def execute(
        self,
        state: ExecutionState,
    ) -> ExecutionState:

        manager = StateManager(state)

        manager.start_execution()

        self.logger.workflow_started(state)

        workflow = state.workflow

        while workflow.has_next():

            node = workflow.get_next_node()

            if node is None:
                break

            manager.mark_node_active(node)

            result = self.execute_agent(node)

            self.process_result(
                manager,
                node,
                result,
            )

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

        decisions = self.policy_engine.evaluate(
            manager.state,
        )

        decision = self.decision_engine.select(
            decisions,
        )

        if decision is not None:

            self.logger.policy_triggered(
                manager.state,
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
                        manager.state,
                        decision.new_node.id,
                    )

                elif decision.action == DecisionAction.REMOVE:

                    self.logger.node_removed(
                        manager.state,
                        decision.target_node,
                    )

                elif decision.action == DecisionAction.REPLACE:

                    self.logger.node_replaced(
                        manager.state,
                        decision.target_node,
                        decision.new_node.id,
                    )

        manager.mark_node_completed(node)