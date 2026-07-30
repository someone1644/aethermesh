import { API_BASE, USE_MOCKS } from './runtime'
import { runningExecutionState } from '../mocks/executionState'
import type { ExecutionState } from '../types/runtime'

export async function getHealth(): Promise<{ status: string; app: string; version: string }> {
  if (USE_MOCKS) return { status: 'healthy', app: 'AetherMesh Runtime', version: '1.0.0' }
  return fetch(`${API_BASE}/health`).then((res) => res.json())
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
