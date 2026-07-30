# AetherMesh — Project Summary

*Self-contained context document for an AI agent with no repo access. Generated from direct inspection of the codebase — no pitch deck, spec, or README exists in this repository, so no hackathon/track/team metadata is included below.*

## 1. Project overview

AetherMesh is an adaptive runtime for multi-agent AI execution. It plans and runs a pipeline of specialized agents — planner, researcher, coder, reviewer, evaluator — against a user-supplied task, monitors execution quality live via a policy engine, and can mutate the workflow mid-run (add, remove, or replace a node) instead of failing outright when something looks wrong (low confidence, contradictory evidence, missing sources, timeout). Every runtime decision is logged as a structured, replayable event, so a completed or in-progress run can be reconstructed and audited step by step afterward. The frontend's own tagline (`frontend/src/pages/Dashboard.tsx`) states it as: *"An adaptive runtime that monitors multi-agent AI execution, detects failures, and safely adapts workflows while explaining every runtime decision through replayable audit logs."*

## 2. Architecture at a glance

**Execution flow** (`backend/runtime/engine.py`, `state_manager.py`, `decision_engine.py`, `policy_engine.py`, `mutation_engine.py`, `event_logger.py`):

`RuntimeEngine.execute()` loops over the `Workflow`'s nodes. For each node it: injects accumulated shared context from prior nodes → runs the agent → `StateManager.apply_agent_result()` updates confidence/final_output/metrics (final_output only updates from the `coder` agent specifically, so it isn't clobbered by a later non-artifact node) → `PolicyEngine.evaluate()` runs all registered policies against the current `ExecutionState` → `DecisionEngine.select()` picks the highest-priority triggered `RuntimeDecision` → `MutationEngine.apply()` mutates the live `Workflow` (add/remove/replace a node) → `EventLogger` records every step (agent start/complete, policy triggers, mutations, workflow start/complete) as a `RuntimeEvent`.

**Policies** (`backend/policies/`) — each reads `ExecutionState` only and returns a `RuntimeDecision`, never mutates state directly:
- `LowConfidencePolicy` — adds an extra researcher node if confidence < 0.4
- `MissingRepoPolicy` — adds a repository-search researcher node if `repository_found` is false
- `ContradictionPolicy` — adds a re-evaluation node if `contradiction_score` > 0.6
- `LowSourcesPolicy` — adds a source-gathering researcher node if `sources` < 3
- `ExecutionTimeoutPolicy` — removes the current node if `execution_time` exceeds a threshold (default 30s)

**Agents** (`backend/agents/`): `PlannerAgent` and `ResearcherAgent` call Gemini (`services/gemini_client.py` — retries 429s with exponential backoff, then trips a class-level cooldown so *all* agents skip Gemini until it clears, falling back to deterministic local text). `CoderAgent`, `ReviewerAgent`, `EvaluatorAgent` are fully local/deterministic — no Gemini calls at all, by design, to control API usage (~2-3 Gemini calls per workflow run: one combined workflow-planning call + planner + researcher).

**Workflow generation** (`backend/services/workflow_generator.py`): one combined Gemini call classifies the task's domain and artifact type and proposes the initial node list; falls back to a fixed 5-node default workflow (Planner → Researcher → Coder → Reviewer → Evaluator) on any parse/API failure.

**Live streaming**: `POST /execute/start` kicks off execution in a background asyncio task and returns immediately with the generated workflow. `GET /execute/{workflow_id}/stream` is a real per-workflow Server-Sent Events stream — `EventLogger` supports per-workflow-id listener callbacks, invoked synchronously the instant an event is logged (from the engine's worker thread, marshaled onto the event loop via `call_soon_threadsafe`); late subscribers get a catch-up replay of already-logged events first. The older `POST /execute` endpoint still exists as a blocking request/response call (used by the test suite).

**Tech stack**: Backend — FastAPI, Pydantic v2, `sse-starlette` for SSE, `google-genai` SDK for Gemini, `httpx`. Frontend — React 18 + TypeScript + Vite, Zustand (state store), React Router, `@xyflow/react` (React Flow, for the Workflow Graph page), Tailwind CSS v4, dayjs.

**Dependency mismatch**: `networkx==3.5` is pinned in `backend/requirements.txt` but as of this writing is not imported or used anywhere in the codebase — it's a declared-but-unused dependency.

## 3. Backend status

### Implemented endpoints (`backend/api/routes.py`)
| Method & path | Purpose |
|---|---|
| `GET /` | Health/info (`HealthResponse`) |
| `GET /health` | Simple health check |
| `POST /execute` | Blocking: runs a full workflow synchronously, returns final `ExecutionState` |
| `GET /replay/{workflow_id}` | Reconstructs and returns the recorded event timeline for a workflow id |
| `POST /execute/start` | Starts a workflow in the background; returns `{workflow_id, workflow}` immediately |
| `GET /execute/{workflow_id}/stream` | SSE stream of live events + state snapshots for a running/completed workflow |
| `GET /execute/{workflow_id}` | Poll the current/final `ExecutionState` for a background run |

### Key data shapes (Pydantic models, `backend/models/*.py`)

**`ExecutionState`** (`models/execution.py`):
```
task: str
status: ExecutionStatus            # "idle" | "running" | "completed" | "failed"
workflow: Workflow
confidence: float = 0.0
repository_found: bool = True
contradiction_score: float = 0.0
sources: int = 0
final_output: str = ""
events: list[RuntimeEvent] = []
metrics: ExecutionMetrics
```

**`ExecutionMetrics`**:
```
execution_time: float = 0.0
mutations: int = 0
completed_agents: int = 0
failed_agents: int = 0
confidence: float = 0.0
```

**`Workflow`** (`models/workflow.py`):
```
id: str                # uuid4
nodes: list[WorkflowNode] = []
edges: list[WorkflowEdge] = []
current_node: str | None = None
history: list[str] = []          # completed node ids, in order
```
(Also carries mutation methods: `add_node`, `add_edge`, `remove_node`, `replace_node`, `get_node`, `has_next`, `get_next_node`, `mark_running/completed/failed/ready`, `reset`.)

**`WorkflowEdge`**: `{ source: str, target: str }`

**`WorkflowNode`** (`models/node.py`):
```
id: str                # uuid4
name: str
agent_type: str        # "planner" | "researcher" | "coder" | "reviewer" | "evaluator"
status: NodeStatus      # "pending" | "ready" | "active" | "completed" | "failed" | "skipped"
metadata: dict[str, Any] = {}
```

**`RuntimeEvent`** (`models/event.py`):
```
id: str                # uuid4
timestamp: datetime     # UTC
event_type: EventType
reason: str
details: dict[str, Any] = {}
```
`EventType` enum values: `workflow_started`, `agent_started`, `agent_completed`, `node_added`, `node_removed`, `node_replaced`, `policy_triggered`, `workflow_completed`.

Notable `details` shapes per event type: `agent_started`/`agent_completed` carry `{node_id, agent_name, confidence?, failed?}`; `node_added`/`node_replaced` carry `{node_id, name, agent_type}` (`node_replaced` also has `old_node`/`new_node` ids); `policy_triggered` carries `{policy: <policy name>}`.

**`RuntimeDecision`** (`models/runtime_decision.py`):
```
action: DecisionAction = "none"   # "none" | "add" | "remove" | "replace"
target_node: str | None = None
new_node: WorkflowNode | None = None
reason: str = ""
policy_name: str = ""
priority: int = 0
metadata: dict[str, Any] = {}
```

**`AgentResult`** (`models/agent_result.py`):
```
answer: str
confidence: float
metadata: dict[str, Any] = {}
```

### Stubbed / gaps (explicit paths)
- No persistent run-history / list-runs endpoint — `GET /replay/{workflow_id}` requires already knowing the id; nothing enumerates past workflow ids.
- `_running_states` dict in `backend/api/routes.py` (backs `/execute/start` and its stream/poll endpoints) is in-memory only — lost on process restart, no persistence layer.
- `EventLogger._event_store` (`backend/runtime/event_logger.py`) is likewise in-memory only, same lifetime as the process.
- `networkx==3.5` dependency is unused.

## 4. Frontend status

### Routes (`frontend/src/App.tsx`)
| Path | Page | Shows |
|---|---|---|
| `/` | `Dashboard.tsx` | Static landing page with tagline + CTA to `/prompt` |
| `/prompt` | `Prompt.tsx` | Task input form, submits and navigates to `/run` |
| `/run` | `Run.tsx` | Live execution view: agent flow diagram, confidence meter, final output, docked event log |
| `/runs` | `PastRuns.tsx` | Table of past runs (**always mock data**, see below) |
| `/policy` | `Policy.tsx` | Live triggered policy decisions for the current run, falling back to a static reference of the 4 policy types when idle |
| `/logs` | `Logs.tsx` | Filterable table of all events for the current run |
| `/timeline` | `Timeline.tsx` | Vertical timeline of all events for the current run |
| `/graph` | `WorkflowGraph.tsx` | React Flow pannable/zoomable graph of the current workflow |
| `/replay` | `Replay.tsx` | Scrubbable playback of a completed run's events over its final workflow |
| `/about` | `About.tsx` | Static about page |

### Mock vs. real data — exact swap points
- `frontend/.env` sets `VITE_USE_MOCKS=false` (currently real mode).
- `frontend/src/api/runtime.ts` exposes `USE_MOCKS` (`import.meta.env.VITE_USE_MOCKS !== 'false'` — defaults to mock unless explicitly disabled) and `API_BASE`.
- The actual branch point is `frontend/src/hooks/useEvents.ts` (`simulateLiveRun`): in real mode it calls `frontend/src/api/client.ts#startTask` (`POST /execute/start`) then subscribes via `frontend/src/api/events.ts#subscribeToExecution` (`EventSource` against `GET /execute/{id}/stream`), applying each event to the Zustand store (`frontend/src/store/runtimeStore.ts`) as it arrives, paced with a minimum ~700ms display step per event (queue/drain loop) so bursty backend events remain individually visible. In mock mode it replays `frontend/src/mocks/executionState.ts#mockEventStream` via `subscribeToEvents` on a fixed interval.
- Workflow folding from events (`frontend/src/lib/workflowEvents.ts#applyEventToWorkflow`) is the shared logic behind both live real-mode updates and the Replay page.
- `frontend/src/pages/PastRuns.tsx` unconditionally imports and displays `pastRuns` from `mocks/executionState.ts` — there is no backend list-runs endpoint to back it, so it never reflects real data regardless of `USE_MOCKS`.

### Known gaps / pending decisions
- `PastRuns` page has no real backend — needs a persistence/list-runs endpoint to become real.
- No persistence across a full browser reload: the Zustand store's initial value is the mock `completedExecutionState` fixture, so refreshing mid-run or after a run loses the real result (no localStorage, no re-fetch-by-id).
- Replay reconstruction (`frontend/src/lib/workflowEvents.ts#buildReplaySkeleton`) seeds from the *final* workflow snapshot with all statuses reset — nodes removed mid-run won't appear in earlier replay frames (accepted simplification given current event payload richness).
- Live event pacing (700ms minimum step) is a deliberate readability tradeoff, explicitly requested — status changes are visually smoothed, not instant-on-arrival.

## 5. Design / theme decisions

Source: `frontend/src/index.css`, `frontend/src/components/`.

**Palette** — monochrome, defined as CSS custom properties in a Tailwind v4 `@theme` block:
- `--color-bg: #ffffff`, `--color-surface: #f7f7f7`, `--color-surface-hover: #ededed`, `--color-border: #e5e5e5`
- `--color-text: #1d1d1d`, `--color-text-muted: #6b6b6b`
- `--color-primary: #1d1d1d`, `--color-primary-soft: #ededed`
- `--color-accent` / `--color-accent-soft` are aliased to the same primary tokens (kept for older components)
- Status colors: pending `#9ca3af` (gray), ready `#6b6b6b` (darker gray), active `#d97706` (amber), completed `#1e8e3e` (green), failed `#d93025` (red), skipped `#9ca3af` (gray, dashed)

**Typography**: `font-mono: "JetBrains Mono", "Fira Code", ui-monospace, ...` for labels, status badges, event logs, and anything data-like; system sans-serif for body copy and headings.

**Layout conventions**:
- Fixed 224px (`w-56`) left sidebar (`Header.tsx`) with icon + label nav items, active-route highlighting via `NavLink`.
- Terminal-style docked event log (`components/sidebar/EventLog.tsx`): `fixed inset-x-0 bottom-0 left-56`, dark `#111214` background regardless of the otherwise-light theme, collapsed state peeks the last 4 lines, expanded state is a scrollable 380px panel with auto-scroll-to-latest and a "jump to latest" affordance when scrolled up.
- Agent flow diagram (`components/workflow/AgentFlowDiagram.tsx`): horizontal row of rounded cards (`rounded-[10px]`), each with a pill-shaped status badge overlapping the top-left border, connected by animated SVG bezier connectors (`components/workflow/Connector`). A connector only shows the "flowing" highlighted state (`connector-flow` dashed animation, amber) when the node immediately to its right is currently `active` — tracks the live execution transition, not a static style.
- `node-pulse` CSS animation (opacity 1 → 0.55 → 1, 1.4s loop) on the status dot / whole card for `active` status.
- Full graph views (`WorkflowCanvas.tsx`, used by `WorkflowGraph.tsx` and `Replay.tsx`) use React Flow instead of the custom flow diagram — dark dotted-background canvas, minimap, pan/zoom controls, for a more general/branching graph view rather than the strictly-linear flow diagram.

## 6. Open questions / next steps

- **Run history persistence**: no backend store or list-runs endpoint exists; `PastRuns` is fully mocked until one is built.
- **`networkx` dependency**: pinned but unused — decide whether to implement graph-based workflow logic with it (e.g. for branching workflows, cycle detection on mutations) or drop it from `requirements.txt`.
- **In-memory-only state**: both `EventLogger`'s event store and `routes.py`'s `_running_states` are lost on backend restart — fine for a single-process demo, not production-durable.
- **SSE reconnect semantics**: a subscriber that disconnects mid-stream and reconnects gets a catch-up replay of already-logged events, but there's no explicit resume-from-offset protocol; correctness relies on `_running_states` still holding the workflow.
- **Live event pacing** (700ms/step) trades off real-time accuracy for readability by explicit request — worth revisiting if this becomes a demo-critical detail vs. a genuine UX preference.
