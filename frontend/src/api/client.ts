import { API_BASE, USE_MOCKS } from './runtime'
import { runningExecutionState } from '../mocks/executionState'
import type { ExecutionState } from '../types/runtime'
import type { Workflow } from '../types/workflow'

export async function getExecutionState(): Promise<ExecutionState> {
  if (USE_MOCKS) return runningExecutionState
  // When the backend exposes it, swap the line above for:
  return fetch(`${API_BASE}/execute`).then((res) => res.json())
}

export async function submitTask(task: string): Promise<ExecutionState> {
  if (USE_MOCKS) return { ...runningExecutionState, task }
  const res = await fetch(`${API_BASE}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || `Execution request failed with status ${res.status}`)
  }
  return res.json()
}

/** Kicks off a background execution; returns immediately so the caller can subscribe to its live stream. */
export async function startTask(task: string): Promise<{ workflow_id: string; workflow: Workflow }> {
  const res = await fetch(`${API_BASE}/execute/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || `Execution request failed with status ${res.status}`)
  }
  return res.json()
}
