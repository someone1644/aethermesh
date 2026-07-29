from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
class EventType(str, Enum):
    WORKFLOW_STARTED = "workflow_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    NODE_REPLACED = "node_replaced"
    POLICY_TRIGGERED = "policy_triggered"
    WORKFLOW_COMPLETED = "workflow_completed"
class RuntimeEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)