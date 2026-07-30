import type { Workflow } from './workflow'
import type { RuntimeEvent } from './event'

export type ExecutionStatus = 'idle' | 'running' | 'completed' | 'failed' | 'paused_for_approval'

/** Backend serializes lowercase ("running"); tolerate any casing at the API boundary. */
export function normalizeStatus(raw: string): ExecutionStatus {
  const lower = raw.toLowerCase()
  if (lower === 'idle' || lower === 'running' || lower === 'completed' || lower === 'failed' || lower === 'paused_for_approval') {
    return lower
  }
  return 'idle'
}

export interface ExecutionMetrics {
  execution_time: number
  mutations: number
  completed_agents: number
  failed_agents: number
  confidence: number
}

export interface ExecutionState {
  task: string
  status: ExecutionStatus
  workflow: Workflow
  confidence: number
  repository_found: boolean
  contradiction_score: number
  sources: number
  final_output: string
  events: RuntimeEvent[]
  metrics: ExecutionMetrics
}

export type DecisionAction = 'none' | 'add' | 'remove' | 'replace'

export interface RuntimeDecision {
  action: DecisionAction
  target_node: string | null
  new_node: string | null
  reason: string
  policy_name: string
  priority: number
  metadata: Record<string, unknown>
}
