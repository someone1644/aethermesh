from __future__ import annotations

from models.event import (
    EventType,
    RuntimeEvent,
)
from models.execution import ExecutionState


class EventLogger:

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

        return event

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