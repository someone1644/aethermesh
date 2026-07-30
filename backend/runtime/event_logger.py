from __future__ import annotations

import logging
from typing import Callable, Dict, List

from models.event import (
    EventType,
    RuntimeEvent,
)
from models.execution import ExecutionState

logger = logging.getLogger(__name__)

EventListener = Callable[[RuntimeEvent], None]


class EventLogger:
    """
    Records RuntimeEvents onto an ExecutionState and keeps a
    parallel in-memory index keyed by workflow_id so the
    ReplayReader can reconstruct execution history.

    Also supports live listeners per workflow_id so an in-progress
    execution can be streamed (e.g. over SSE) as events are logged.
    """

    def __init__(self) -> None:
        # workflow_id → list of events (for replay)
        self._event_store: Dict[str, List[RuntimeEvent]] = {}
        # workflow_id → list of live listener callbacks
        self._listeners: Dict[str, List[EventListener]] = {}

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
        workflow_id = None
        if hasattr(state, "workflow") and hasattr(state.workflow, "id"):
            workflow_id = state.workflow.id
            self.store_event(workflow_id, event)
        logger.debug(
            "EventLogger | %s | %s",
            event_type.value,
            reason,
        )

        if workflow_id:
            for callback in list(self._listeners.get(workflow_id, [])):
                callback(event)

        return event

    # ------------------------------------------------------------------
    # Live streaming support
    # ------------------------------------------------------------------

    def add_listener(
        self,
        workflow_id: str,
        callback: EventListener,
    ) -> None:
        """Register a callback invoked (synchronously, on the caller's
        thread) each time an event is logged for *workflow_id*."""
        self._listeners.setdefault(workflow_id, []).append(callback)

    def remove_listener(
        self,
        workflow_id: str,
        callback: EventListener,
    ) -> None:
        callbacks = self._listeners.get(workflow_id)
        if not callbacks:
            return
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self._listeners.pop(workflow_id, None)

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
        *,
        failed: bool = False,
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.AGENT_COMPLETED,
            f"Agent '{agent_type}' completed.",
            {
                "node_id": node_id,
                "agent_name": agent_type,
                "confidence": confidence,
                "failed": failed,
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
        *,
        name: str = "",
        agent_type: str = "",
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.NODE_ADDED,
            "Node added.",
            {
                "node_id": node_id,
                "name": name,
                "agent_type": agent_type,
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
        *,
        name: str = "",
        agent_type: str = "",
    ) -> RuntimeEvent:

        return self.log(
            state,
            EventType.NODE_REPLACED,
            "Node replaced.",
            {
                "old_node": old_node,
                "new_node": new_node,
                "name": name,
                "agent_type": agent_type,
            },
        )