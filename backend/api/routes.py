from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.schemas import HealthResponse, TaskRequest
from config import settings
from models.execution import ExecutionState
from runtime.engine import RuntimeEngine
from runtime.policy_engine import PolicyEngine
from runtime.replay import ReplayReader
from services.bootstrap import (
    event_logger,
    gemini_client,
    registry,
    workflow_generator,
)
from policies import (
    LowConfidencePolicy,
    MissingRepoPolicy,
    ContradictionPolicy,
    LowSourcesPolicy,
    ExecutionTimeoutPolicy,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# -----------------------------------------------------------------------
# Health / info
# -----------------------------------------------------------------------


@router.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="running",
        version=settings.VERSION,
    )


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
    }


# -----------------------------------------------------------------------
# Execution
# -----------------------------------------------------------------------


@router.post("/execute")
async def execute_task(body: TaskRequest):
    """
    Accept a task, generate a workflow, run the runtime engine,
    and return the final ExecutionState as JSON.
    """
    task = body.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task must not be empty.")

    try:
        # 1. Generate workflow
        workflow = workflow_generator.generate(task)

        # 2. Build execution state
        state = ExecutionState(task=task, workflow=workflow)

        # 3. Assemble policy engine with all registered policies
        policy_engine = PolicyEngine(
            policies=[
                LowConfidencePolicy(),
                MissingRepoPolicy(),
                ContradictionPolicy(),
                LowSourcesPolicy(),
                ExecutionTimeoutPolicy(),
            ]
        )

        # 4. Build runtime engine with shared event logger
        engine = RuntimeEngine(
            policy_engine=policy_engine,
            registry=registry,
            event_logger=event_logger,
        )

        # 5. Execute (synchronous — runs in the event loop thread)
        result = await asyncio.to_thread(engine.execute, state)

        # 6. Return serialized ExecutionState
        return result.model_dump(mode="json")

    except Exception as exc:
        logger.exception("Execution failed for task=%r", task)
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {exc}",
        ) from exc


# -----------------------------------------------------------------------
# Replay
# -----------------------------------------------------------------------


@router.get("/replay/{workflow_id}")
async def get_replay(workflow_id: str):
    """
    Reconstruct and return execution replay steps for workflow_id.
    """
    try:
        reader = ReplayReader(event_logger)
        replay = reader.reconstruct(workflow_id)
        return {
            "workflow_id": replay.workflow_id,
            "steps": [
                {
                    "timestamp": step.timestamp.isoformat()
                    if step.timestamp and hasattr(step.timestamp, "isoformat")
                    else str(step.timestamp),
                    "node_id": step.node_id,
                    "agent_name": step.agent_name,
                    "event_type": step.event_type,
                    "payload": step.payload,
                }
                for step in replay.steps
            ],
        }
    except Exception as exc:
        logger.exception("Replay failed for workflow_id=%r", workflow_id)
        raise HTTPException(
            status_code=500,
            detail=f"Replay reconstruction failed: {exc}",
        ) from exc


# -----------------------------------------------------------------------
# SSE event stream
# -----------------------------------------------------------------------


@router.get("/events/stream")
async def event_stream():
    """
    Server-Sent Events endpoint.
    Streams runtime events to the frontend for live visualization.
    Subscribes to the shared EventLogger's broadcast queue.
    """

    async def _generate() -> AsyncGenerator[dict, None]:
        # Send initial connected message
        yield {"data": json.dumps({"event_type": "connected", "reason": "SSE stream ready"})}

        # Subscribe to live event broadcasts
        queue = event_logger.subscribe()
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "data": json.dumps(event.model_dump(mode="json"))
                    }
                except asyncio.TimeoutError:
                    # Send keepalive to prevent connection timeout
                    yield {"data": json.dumps({"event_type": "keepalive", "reason": "connection alive"})}
        except asyncio.CancelledError:
            pass
        finally:
            event_logger.unsubscribe(queue)

    return EventSourceResponse(_generate())