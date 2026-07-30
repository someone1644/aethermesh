from __future__ import annotations
from models.agent_result import AgentResult
from models.event import RuntimeEvent
from models.execution import (
    ExecutionState,
    ExecutionStatus,
)
from models.node import (
    WorkflowNode,
    NodeStatus,
)
class StateManager:
    """
    Central interface for updating ExecutionState.
    No other component should directly modify the state.
    """
    def __init__(self, state: ExecutionState):
        self.state = state
    def start_execution(self) -> None:
        self.state.status = ExecutionStatus.RUNNING
    def complete_execution(self) -> None:
        self.state.status = ExecutionStatus.COMPLETED
    def fail_execution(self) -> None:
        self.state.status = ExecutionStatus.FAILED
    def update_confidence(self, confidence: float) -> None:
        self.state.confidence = confidence
        self.state.metrics.confidence = confidence
    def increment_completed_agents(self) -> None:
        self.state.metrics.completed_agents += 1
    def increment_failed_agents(self) -> None:
        self.state.metrics.failed_agents += 1
    def increment_mutations(self) -> None:
        self.state.metrics.mutations += 1
    def set_execution_time(self, execution_time: float) -> None:
        self.state.metrics.execution_time = execution_time
    def update_repository_status(
        self,
        repository_found: bool,
    ) -> None:
        self.state.repository_found = repository_found
    def update_contradiction_score(
        self,
        score: float,
    ) -> None:
        self.state.contradiction_score = score
    def update_sources(
        self,
        sources: int,
    ) -> None:
        self.state.sources = sources
    def update_final_output(
        self,
        output: str,
    ) -> None:
        self.state.final_output = output
    def apply_agent_result(
        self,
        result: AgentResult,
        *,
        agent_type: str | None = None,
    ) -> None:
        """
        Update execution state using an AgentResult.
        Calculates cumulative confidence and captures deliverables from primary agents.
        """
        # Calculate running average confidence across completed agent results
        if not hasattr(self, "_confidence_scores"):
            self._confidence_scores: list[float] = []
        self._confidence_scores.append(result.confidence)

        # If Evaluator or Reviewer completed, prioritize their score; otherwise take average
        if agent_type in ("evaluator", "reviewer") and "score" in result.metadata:
            computed_conf = float(result.metadata["score"])
        elif agent_type == "evaluator":
            computed_conf = result.confidence
        else:
            computed_conf = round(sum(self._confidence_scores) / len(self._confidence_scores), 2)

        self.update_confidence(computed_conf)

        self.state.repository_found = result.metadata.get(
            "repository_found",
            self.state.repository_found,
        )
        self.state.contradiction_score = result.metadata.get(
            "contradiction_score",
            self.state.contradiction_score,
        )
        self.state.sources = result.metadata.get(
            "sources",
            self.state.sources,
        )

        # Capture deliverables from any primary artifact-producing agent
        deliverable_agents = (
            "coder",
            "summarizer",
            "analyst",
            "security_auditor",
            "optimizer",
            "debugger",
            "sandbox_runner",
        )
        if agent_type in deliverable_agents or not self.state.final_output:
            self.update_final_output(result.answer)
    def mark_node_active(
        self,
        node: WorkflowNode,
    ) -> None:
        self.state.workflow.mark_running(node.id)
    def mark_node_completed(
        self,
        node: WorkflowNode,
    ) -> None:
        self.state.workflow.mark_completed(node.id)
        self.increment_completed_agents()

    def mark_node_failed(
        self,
        node: WorkflowNode,
    ) -> None:
        self.state.workflow.mark_failed(node.id)
        self.increment_failed_agents()

    def mark_node_skipped(
        self,
        node: WorkflowNode,
    ) -> None:
        node.status = NodeStatus.SKIPPED
    def add_event(
        self,
        event: RuntimeEvent,
    ) -> None:
        self.state.events.append(event)
    def get_state(self) -> ExecutionState:
        return self.state