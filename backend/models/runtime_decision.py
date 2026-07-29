from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from models.node import WorkflowNode


class DecisionAction(str, Enum):
    NONE = "none"
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"


class RuntimeDecision(BaseModel):
    action: DecisionAction = DecisionAction.NONE

    target_node: Optional[str] = None

    new_node: Optional[WorkflowNode] = None

    reason: str = ""

    policy_name: str = ""

    priority: int = Field(default=0, ge=0)

    metadata: Dict[str, Any] = Field(default_factory=dict)