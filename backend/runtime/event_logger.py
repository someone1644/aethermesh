from __future__ import annotations

import logging
from typing import Dict, List

from models.event import (
    EventType,
    RuntimeEvent,
)
from models.execution import ExecutionState

logger = logging.getLogger(__name__)


class EventLogger:
    """
    Records RuntimeEvents onto an ExecutionState and keeps a
    parallel in-memory index keyed by workflow_id so the
    ReplayReader can reconstruct execution history.
    """

    def __init__(self) -> None:
        # workflow_id → list of events (for replay)
        self._event_store: Dict[str, List[RuntimeEvent]] = {}

    # ------------------------------------------------------------------
    # Core logging
    # ------------------------------------------------------------------

    def log(
        self,
        state: ExecutionState,
        event_type: EventType,
        reason: str,
        details: dict | None = None,
    ) -> RuntimeEvent:

        event = RuntimeEvent(
            event_type=event_type,
            reason=reason,
            details=details or {},
        )

        state.add_event(event)
        if hasattr(state, "workflow") and hasattr(state.workflow, "id"):
            self.store_event(state.workflow.id, event)
        logger.debug(
            "EventLogger | %s | %s",
            event_type.value,
            reason,
        )

        return event

    # ------------------------------------------------------------------
    # Replay support
    # ------------------------------------------------------------------

    def store_event(
        self,
        workflow_id: str,
        event: RuntimeEvent,
    ) -> None:
        """Persist an event in the in-memory store for replay."""
        self._event_store.setdefault(workflow_id, []).append(event)

    def get_events(
        self,
        workflow_id: str,
    ) -> List[RuntimeEvent]:
        """Return all recorded events for *workflow_id*."""
        return list(self._event_store.get(workflow_id, []))

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def workflow_started(
        self,
        state: ExecutionState,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.WORKFLOW_STARTED,
            "Workflow execution started.",
        )

    def workflow_completed(
        self,
        state: ExecutionState,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.WORKFLOW_COMPLETED,
            "Workflow execution completed.",
        )

    def agent_started(
        self,
        state: ExecutionState,
        node_id: str,
        agent_type: str,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.AGENT_STARTED,
            f"Agent '{agent_type}' started.",
            {
                "node_id": node_id,
                "agent_name": agent_type,
            },
        )

    def agent_completed(
        self,
        state: ExecutionState,
        node_id: str,
        agent_type: str,
        confidence: float,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.AGENT_COMPLETED,
            f"Agent '{agent_type}' completed.",
            {
                "node_id": node_id,
                "agent_name": agent_type,
                "confidence": confidence,
            },
        )

    def policy_triggered(
        self,
        state: ExecutionState,
        policy_name: str,
        reason: str,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.POLICY_TRIGGERED,
            reason,
            {
                "policy": policy_name,
            },
        )

    def node_added(
        self,
        state: ExecutionState,
        node_id: str,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.NODE_ADDED,
            "Node added.",
            {
                "node_id": node_id,
            },
        )

    def node_removed(
        self,
        state: ExecutionState,
        node_id: str,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.NODE_REMOVED,
            "Node removed.",
            {
                "node_id": node_id,
            },
        )

    def node_replaced(
        self,
        state: ExecutionState,
        old_node: str,
        new_node: str,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.NODE_REPLACED,
            "Node replaced.",
            {
                "old_node": old_node,
                "new_node": new_node,
            },
        )