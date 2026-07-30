import { API_BASE } from './runtime'
import { mockEventStream } from '../mocks/executionState'
import type { RuntimeEvent } from '../types/event'

/** Replays the mock event fixture on an interval so mock mode feels live. */
export function subscribeToEvents(
  onEvent: (event: RuntimeEvent) => void,
  intervalMs = 1200,
): () => void {
  let i = 0
  const timer = setInterval(() => {
    if (i >= mockEventStream.length) {
      clearInterval(timer)
      return
    }
    onEvent(mockEventStream[i])
    i += 1
  }, intervalMs)
  return () => clearInterval(timer)
}

export interface ExecutionStreamState {
  status: string
  confidence: number
  final_output: string
  repository_found: boolean
  contradiction_score: number
  sources: number
  metrics: {
    execution_time: number
    mutations: number
    completed_agents: number
    failed_agents: number
    confidence: number
  }
}

export interface ExecutionStreamPayload {
  event: RuntimeEvent
  state: ExecutionStreamState
}

/**
 * Subscribes to the live SSE stream for a workflow started via
 * POST /execute/start. Calls onPayload for every event (including any
 * already logged before the stream connected), then onDone once the
 * stream closes (workflow_completed, or a connection error).
 */
export function subscribeToExecution(
  workflowId: string,
  onPayload: (payload: ExecutionStreamPayload) => void,
  onDone: () => void,
): () => void {
  const source = new EventSource(`${API_BASE}/execute/${workflowId}/stream`)
  let done = false
  const finish = () => {
    if (done) return
    done = true
    source.close()
    onDone()
  }
  source.onmessage = (msg) => {
    const payload = JSON.parse(msg.data) as ExecutionStreamPayload
    onPayload(payload)
    if (payload.event.event_type === 'workflow_completed') finish()
  }
  source.onerror = () => finish()
  return finish
}
