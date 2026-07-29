from __future__ import annotations
from typing import Any, Dict
from pydantic import BaseModel, Field
class AgentResult(BaseModel):
    answer: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)