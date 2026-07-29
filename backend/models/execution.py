from __future__ import annotations
from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from models.event import RuntimeEvent
from models.workflow import Workflow
class ExecutionStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
class ExecutionMetrics(BaseModel):
    execution_time: float = 0.0
    mutations: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    confidence: float = 0.0
class ExecutionState(BaseModel):
    task: str
    status: ExecutionStatus = ExecutionStatus.IDLE
    workflow: Workflow = Field(default_factory=Workflow)
    confidence: float = 0.0
    repository_found: bool = True
    contradiction_score: float = 0.0
    sources: int = 0
    final_output: str = ""
    events: List[RuntimeEvent] = Field(default_factory=list)
    metrics: ExecutionMetrics = Field(
        default_factory=ExecutionMetrics
    )
    def add_event(self, event: RuntimeEvent):
        self.events.append(event)