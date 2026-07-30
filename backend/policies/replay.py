
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.event_logger import EventLogger


@dataclass
class ReplayStep:
    """A single reconstructed step in the execution history."""

    timestamp: Any
    node_id: Optional[str]
    agent_name: Optional[str]
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReplay:
    """Reconstructed, read-only view of a workflow's execution history."""

    workflow_id: str
    steps: List[ReplayStep] = field(default_factory=list)

    def node_history(self, node_id: str) -> List[ReplayStep]:
        """All steps involving a given node, in original order."""
        return [step for step in self.steps if step.node_id == node_id]

    def agent_history(self, agent_name: str) -> List[ReplayStep]:
        """All steps involving a given agent, in original order."""
        return [step for step in self.steps if step.agent_name == agent_name]

    def timeline(self) -> List[ReplayStep]:
        """All steps sorted chronologically."""
        return sorted(self.steps, key=lambda step: step.timestamp)


class ReplayReader:
    """
    Reconstructs execution history purely from RuntimeEvents.

    READ-ONLY: never mutates ExecutionState or Workflow, never calls
    RuntimeEngine, PolicyEngine, DecisionEngine, or MutationEngine, and
    never re-executes agents. It only reads what EventLogger already
    recorded.
    """

    def __init__(self, event_logger: EventLogger):
        self._event_logger = event_logger

    def reconstruct(self, workflow_id: str) -> ExecutionReplay:
        """Build an ExecutionReplay for a workflow from its logged events."""
        events = self._event_logger.get_events(workflow_id)

        steps = [
            ReplayStep(
                timestamp=getattr(event, "timestamp", None),
                node_id=getattr(event, "node_id", None),
                agent_name=getattr(event, "agent_name", None),
                event_type=getattr(event, "event_type", "unknown"),
                payload=getattr(event, "payload", {}) or {},
            )
            for event in events
        ]

        replay = ExecutionReplay(workflow_id=workflow_id, steps=steps)
        replay.steps = replay.timeline()
        return replay