from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.schemas import HealthResponse, TaskRequest
from config import settings
from models.event import EventType, RuntimeEvent
from models.execution import ExecutionState, ExecutionStatus
from runtime.engine import RuntimeEngine
from runtime.policy_engine import PolicyEngine
from runtime.replay import ReplayReader
from runtime.workflow_graph import to_node_link_data
from database import save_run, get_all_runs, get_run_by_id
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

# In-memory registry of executions started via /execute/start, keyed by
# workflow_id, so /execute/{id}/stream and /execute/{id} can find them.
# Same lifetime tradeoff as EventLogger's in-memory store: fine for a
# single-process dev/demo deployment, not meant to survive a restart.
_running_states: dict[str, ExecutionState] = {}


def _build_policy_engine() -> PolicyEngine:
    return PolicyEngine(
        policies=[
            LowConfidencePolicy(),
            MissingRepoPolicy(),
            ContradictionPolicy(),
            LowSourcesPolicy(),
            ExecutionTimeoutPolicy(),
        ]
    )


def _state_snapshot(state: ExecutionState) -> dict:
    return {
        "status": state.status.value,
        "confidence": state.confidence,
        "final_output": state.final_output,
        "repository_found": state.repository_found,
        "contradiction_score": state.contradiction_score,
        "sources": state.sources,
        "metrics": state.metrics.model_dump(mode="json"),
    }


def _stream_payload(event: RuntimeEvent, state: ExecutionState) -> dict:
    return {
        "event": event.model_dump(mode="json"),
        "state": _state_snapshot(state),
    }

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
        policy_engine = _build_policy_engine()

        # 4. Build runtime engine with shared event logger
        engine = RuntimeEngine(
            policy_engine=policy_engine,
            registry=registry,
            event_logger=event_logger,
        )

        # 5. Execute (synchronous — runs in the event loop thread)
        result = await asyncio.to_thread(engine.execute, state)

        # Save run to SQLite database
        try:
            save_run(result.workflow.id, result.model_dump(mode="json"))
        except Exception:
            logger.exception("Failed to save run to SQLite database.")

        # 6. Return serialized ExecutionState
        return result.model_dump(mode="json")

    except Exception as exc:
        logger.exception("Execution failed for task=%r", task)
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {exc}",
        ) from exc


@router.get("/history")
async def get_history():
    """
    Fetch all historical execution runs saved in SQLite database.
    """
    try:
        return get_all_runs()
    except Exception as exc:
        logger.exception("Failed to fetch history from SQLite.")
        return []


@router.post("/execute/{workflow_id}/approve")
async def approve_mutation(workflow_id: str, action: str = "approve"):
    """
    Human-in-the-Loop (HITL) approval endpoint to resume a paused execution.
    """
    state = _running_states.get(workflow_id)
    if not state:
        # Check SQLite DB
        db_state = get_run_by_id(workflow_id)
        if not db_state:
            raise HTTPException(status_code=404, detail="Workflow not found.")
        return {"status": "ok", "message": f"Action {action!r} processed for workflow {workflow_id}."}

    if state.status == ExecutionStatus.PAUSED_FOR_APPROVAL:
        state.status = ExecutionStatus.RUNNING
        event_logger.log(state, EventType.POLICY_TRIGGERED, f"Human operator approved action: {action}")
        save_run(workflow_id, state.model_dump(mode="json"))
        return {"status": "approved", "workflow_id": workflow_id}

    return {"status": "ok", "message": f"Workflow is currently in status {state.status.value!r}."}


# -----------------------------------------------------------------------
# Replay
# -----------------------------------------------------------------------


@router.get("/replay/{workflow_id}")
async def get_replay(workflow_id: str):
    """
    Reconstruct and return execution replay steps for workflow_id.
    """
    try:
        # First check SQLite DB
        db_state = get_run_by_id(workflow_id)
        if db_state and "events" in db_state:
            return {
                "workflow_id": workflow_id,
                "steps": [
                    {
                        "timestamp": evt.get("timestamp", ""),
                        "node_id": evt.get("details", {}).get("node_id", ""),
                        "agent_name": evt.get("details", {}).get("agent_name", ""),
                        "event_type": evt.get("event_type", ""),
                        "payload": evt.get("details", {}),
                    }
                    for evt in db_state["events"]
                ],
            }

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
# Workflow graph
# -----------------------------------------------------------------------


@router.get("/workflow/{workflow_id}/graph")
async def get_workflow_graph(workflow_id: str):
    """
    Node-link representation (networkx.node_link_data) of a workflow's
    graph, built from the same Workflow.nodes/edges the runtime itself
    executes against — so this stays consistent with actual execution
    order by construction rather than being a separately-maintained view.
    """
    state = _running_states.get(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown workflow_id.")
    return to_node_link_data(state.workflow)


# -----------------------------------------------------------------------
# Live execution (start + SSE stream)
# -----------------------------------------------------------------------


@router.post("/execute/start")
async def start_execute(body: TaskRequest):
    """
    Generate a workflow and kick off execution in the background,
    returning immediately with the workflow_id and initial (all-pending)
    workflow so the caller can seed a live view before subscribing to
    /execute/{workflow_id}/stream.
    """
    task = body.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task must not be empty.")

    workflow = workflow_generator.generate(task)
    state = ExecutionState(task=task, workflow=workflow)
    _running_states[workflow.id] = state

    engine = RuntimeEngine(
        policy_engine=_build_policy_engine(),
        registry=registry,
        event_logger=event_logger,
    )

    async def _run() -> None:
        try:
            await asyncio.to_thread(engine.execute, state)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Background execution failed for workflow_id=%r", workflow.id
            )
            state.status = ExecutionStatus.FAILED
            state.final_output = state.final_output or f"Execution failed: {exc}"
            event_logger.log(
                state,
                EventType.WORKFLOW_COMPLETED,
                "Workflow execution failed.",
            )

    asyncio.create_task(_run())

    return {
        "workflow_id": workflow.id,
        "workflow": workflow.model_dump(mode="json"),
    }


@router.get("/execute/{workflow_id}/stream")
async def stream_execute(workflow_id: str):
    """
    Server-Sent Events endpoint for an execution started via /execute/start.
    Replays any events already logged, then streams new ones live until
    workflow_completed, at which point the stream closes.
    """
    state = _running_states.get(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown workflow_id.")

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def on_event(event: RuntimeEvent) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, _stream_payload(event, state))

    # Register the listener BEFORE snapshotting state.events. Doing it the
    # other way round leaves a gap where an event logged between the
    # snapshot and registration is neither in the snapshot nor delivered
    # live — silently dropped (this is what was swallowing the first
    # agent_started event, making nodes appear to jump straight from
    # pending to completed). Registering first can instead double-deliver
    # an event logged in that same narrow window, so de-dupe by id below.
    event_logger.add_listener(workflow_id, on_event)
    caught_up = list(state.events)
    seen_ids = {event.id for event in caught_up}

    async def _generate() -> AsyncGenerator[dict, None]:
        try:
            for event in caught_up:
                yield {"data": json.dumps(_stream_payload(event, state))}
                if event.event_type == EventType.WORKFLOW_COMPLETED:
                    return

            while True:
                payload = await queue.get()
                if payload["event"]["id"] in seen_ids:
                    continue
                yield {"data": json.dumps(payload)}
                if payload["event"]["event_type"] == EventType.WORKFLOW_COMPLETED.value:
                    break
        finally:
            event_logger.remove_listener(workflow_id, on_event)

    return EventSourceResponse(_generate())


@router.get("/execute/{workflow_id}")
async def get_execute_state(workflow_id: str):
    """Poll the current (or final) ExecutionState for a background run."""
    state = _running_states.get(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown workflow_id.")
    return state.model_dump(mode="json")
