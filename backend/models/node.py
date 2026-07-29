from __future__ import annotations
from enum import Enum
from typing import Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
class NodeStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
class WorkflowNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    agent_type: str
    status: NodeStatus = NodeStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)