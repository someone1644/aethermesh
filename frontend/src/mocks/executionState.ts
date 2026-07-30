import type { ExecutionState, ExecutionStatus } from '../types/runtime'
import type { RuntimeEvent } from '../types/event'
import { foldEvents } from '../lib/workflowEvents'

function event(
  id: string,
  timestamp: string,
  event_type: RuntimeEvent['event_type'],
  reason: string,
  details: Record<string, unknown> = {},
): RuntimeEvent {
  return { id, timestamp, event_type, reason, details }
}

// --- Scenario 1: checkout-service CI fix — completed, one low-confidence mutation ---

export const CHECKOUT_EVENTS: RuntimeEvent[] = [
  event('evt-01', '2026-07-30T09:00:00.000000', 'workflow_started', 'Workflow execution started.'),
  event('evt-02', '2026-07-30T09:00:02.000000', 'agent_started', 'Planner started.', { node_id: 'planner-1' }),
  event('evt-03', '2026-07-30T09:00:05.000000', 'agent_completed', 'Planner completed.', { node_id: 'planner-1', confidence: 1.0 }),
  event('evt-04', '2026-07-30T09:00:06.000000', 'agent_started', 'Researcher started.', { node_id: 'researcher-1' }),
  event('evt-05', '2026-07-30T09:00:11.000000', 'policy_triggered', 'Researcher confidence 0.42 fell below the 0.6 threshold.', { policy: 'low_confidence_policy' }),
  event('evt-06', '2026-07-30T09:00:11.500000', 'node_replaced', 'Node replaced.', { old_node: 'researcher-1', new_node: 'researcher-2' }),
  event('evt-07', '2026-07-30T09:00:12.000000', 'agent_started', 'Researcher (retry) started.', { node_id: 'researcher-2' }),
  event('evt-08', '2026-07-30T09:00:17.000000', 'agent_completed', 'Researcher (retry) completed.', { node_id: 'researcher-2', confidence: 0.88, sources: 5 }),
  event('evt-09', '2026-07-30T09:00:18.000000', 'agent_started', 'Coder started.', { node_id: 'coder-1' }),
  event('evt-10', '2026-07-30T09:00:24.000000', 'agent_completed', 'Coder completed.', { node_id: 'coder-1', confidence: 0.93 }),
  event('evt-11', '2026-07-30T09:00:25.000000', 'agent_started', 'Reviewer started.', { node_id: 'reviewer-1' }),
  event('evt-12', '2026-07-30T09:00:29.000000', 'agent_completed', 'Reviewer completed.', { node_id: 'reviewer-1', confidence: 0.96 }),
  event('evt-13', '2026-07-30T09:00:30.000000', 'agent_started', 'Evaluator started.', { node_id: 'evaluator-1' }),
  event('evt-14', '2026-07-30T09:00:34.000000', 'agent_completed', 'Evaluator completed.', { node_id: 'evaluator-1', confidence: 0.82 }),
  event('evt-15', '2026-07-30T09:00:34.500000', 'workflow_completed', 'Workflow execution completed.'),
]

export const completedExecutionState: ExecutionState = {
  task: 'Diagnose the failing checkout-service CI pipeline and ship a fix',
  status: 'completed',
  workflow: foldEvents(CHECKOUT_EVENTS),
  confidence: 0.82,
  repository_found: true,
  contradiction_score: 0.08,
  sources: 5,
  final_output:
    'Root cause: the checkout-service CI pipeline was pinned to a deprecated Node 16 image, causing native module builds to fail intermittently. Patched the workflow to Node 20, pinned the lockfile, and re-ran the suite 3x with no flakes.',
  events: CHECKOUT_EVENTS,
  metrics: {
    execution_time: 34.5,
    mutations: 1,
    completed_agents: 5,
    failed_agents: 0,
    confidence: 0.82,
  },
}

export const runningExecutionState: ExecutionState = {
  ...completedExecutionState,
  status: 'running',
  confidence: 0.88,
  final_output: '',
  events: CHECKOUT_EVENTS.slice(0, 9),
  workflow: foldEvents(CHECKOUT_EVENTS.slice(0, 9)),
  metrics: {
    execution_time: 18.0,
    mutations: 1,
    completed_agents: 2,
    failed_agents: 0,
    confidence: 0.88,
  },
}

/** Replayed by the mock live-run ticker, regardless of what task text the user typed. */
export const mockEventStream: RuntimeEvent[] = CHECKOUT_EVENTS

// --- Scenario 2: refund-policy contradiction — aborted, no mutation applied in time ---

const CONTRADICTION_EVENTS: RuntimeEvent[] = [
  event('cevt-01', '2026-07-29T14:02:00.000000', 'workflow_started', 'Workflow execution started.'),
  event('cevt-02', '2026-07-29T14:02:01.000000', 'agent_started', 'Planner started.', { node_id: 'planner-1' }),
  event('cevt-03', '2026-07-29T14:02:04.000000', 'agent_completed', 'Planner completed.', { node_id: 'planner-1', confidence: 1.0 }),
  event('cevt-04', '2026-07-29T14:02:05.000000', 'agent_started', 'Researcher started.', { node_id: 'researcher-1' }),
  event('cevt-05', '2026-07-29T14:02:10.000000', 'agent_completed', 'Researcher completed.', { node_id: 'researcher-1', confidence: 0.58, sources: 3 }),
  event('cevt-06', '2026-07-29T14:02:12.000000', 'policy_triggered', 'Contradiction score 0.62 exceeded the 0.5 threshold.', { policy: 'contradiction_policy' }),
  event('cevt-07', '2026-07-29T14:02:13.000000', 'agent_started', 'Coder started.', { node_id: 'coder-1' }),
  event('cevt-08', '2026-07-29T14:02:20.000000', 'agent_completed', 'Coder could not reconcile conflicting refund-policy sources.', { node_id: 'coder-1', confidence: 0.31, failed: true }),
]

const failedExecutionState: ExecutionState = {
  task: 'Investigate contradictory evidence in refund-policy documentation',
  status: 'failed',
  workflow: foldEvents(CONTRADICTION_EVENTS),
  confidence: 0.31,
  repository_found: true,
  contradiction_score: 0.62,
  sources: 3,
  final_output: '',
  events: CONTRADICTION_EVENTS,
  metrics: {
    execution_time: 20.0,
    mutations: 0,
    completed_agents: 2,
    failed_agents: 1,
    confidence: 0.31,
  },
}

// --- Scenario 3: Q2 postmortem report — completed, no mutation ---

const REPORT_EVENTS: RuntimeEvent[] = [
  event('revt-01', '2026-07-28T11:15:00.000000', 'workflow_started', 'Workflow execution started.'),
  event('revt-02', '2026-07-28T11:15:02.000000', 'agent_started', 'Planner started.', { node_id: 'planner-1' }),
  event('revt-03', '2026-07-28T11:15:05.000000', 'agent_completed', 'Planner completed.', { node_id: 'planner-1', confidence: 1.0 }),
  event('revt-04', '2026-07-28T11:15:06.000000', 'agent_started', 'Researcher started.', { node_id: 'researcher-1' }),
  event('revt-05', '2026-07-28T11:15:12.000000', 'agent_completed', 'Researcher completed.', { node_id: 'researcher-1', confidence: 0.91, sources: 6 }),
  event('revt-06', '2026-07-28T11:15:13.000000', 'agent_started', 'Coder started.', { node_id: 'coder-1' }),
  event('revt-07', '2026-07-28T11:15:19.000000', 'agent_completed', 'Coder completed.', { node_id: 'coder-1', confidence: 0.95 }),
  event('revt-08', '2026-07-28T11:15:20.000000', 'agent_started', 'Reviewer started.', { node_id: 'reviewer-1' }),
  event('revt-09', '2026-07-28T11:15:24.000000', 'agent_completed', 'Reviewer completed.', { node_id: 'reviewer-1', confidence: 0.96 }),
  event('revt-10', '2026-07-28T11:15:25.000000', 'agent_started', 'Evaluator started.', { node_id: 'evaluator-1' }),
  event('revt-11', '2026-07-28T11:15:29.000000', 'agent_completed', 'Evaluator completed.', { node_id: 'evaluator-1', confidence: 0.94 }),
  event('revt-12', '2026-07-28T11:15:29.500000', 'workflow_completed', 'Workflow execution completed.'),
]

const reportExecutionState: ExecutionState = {
  task: 'Summarize Q2 incident postmortems into a single report',
  status: 'completed',
  workflow: foldEvents(REPORT_EVENTS),
  confidence: 0.94,
  repository_found: true,
  contradiction_score: 0.05,
  sources: 6,
  final_output:
    'Compiled 6 Q2 incident postmortems into a single report highlighting recurring root causes (config drift, alert fatigue) and 4 recommended guardrails.',
  events: REPORT_EVENTS,
  metrics: {
    execution_time: 29.5,
    mutations: 0,
    completed_agents: 5,
    failed_agents: 0,
    confidence: 0.94,
  },
}

export interface PastRunSummary {
  id: string
  task: string
  status: ExecutionStatus
  confidence: number
  mutations: number
  startedAt: string
}

export const pastRuns: { summary: PastRunSummary; state: ExecutionState }[] = [
  {
    summary: {
      id: 'run-1',
      task: completedExecutionState.task,
      status: 'completed',
      confidence: completedExecutionState.confidence,
      mutations: completedExecutionState.metrics.mutations,
      startedAt: '2026-07-30T09:00:00.000000',
    },
    state: completedExecutionState,
  },
  {
    summary: {
      id: 'run-2',
      task: failedExecutionState.task,
      status: 'failed',
      confidence: failedExecutionState.confidence,
      mutations: failedExecutionState.metrics.mutations,
      startedAt: '2026-07-29T14:02:00.000000',
    },
    state: failedExecutionState,
  },
  {
    summary: {
      id: 'run-3',
      task: reportExecutionState.task,
      status: 'completed',
      confidence: reportExecutionState.confidence,
      mutations: reportExecutionState.metrics.mutations,
      startedAt: '2026-07-28T11:15:00.000000',
    },
    state: reportExecutionState,
  },
]
