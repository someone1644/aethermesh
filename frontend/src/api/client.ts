import { API_BASE, USE_MOCKS } from './runtime'
import { runningExecutionState } from '../mocks/executionState'
import type { ExecutionState } from '../types/runtime'

export async function getExecutionState(): Promise<ExecutionState> {
  if (USE_MOCKS) return runningExecutionState
  // When the backend exposes it, swap the line above for:
  return fetch(`${API_BASE}/execute`).then((res) => res.json())
}

export async function submitTask(task: string): Promise<ExecutionState> {
  if (USE_MOCKS) return { ...runningExecutionState, task }
  return fetch(`${API_BASE}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  }).then((res) => res.json())
}
