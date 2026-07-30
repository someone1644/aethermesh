import type { ExecutionState } from '../types/runtime'

export interface PastRunItem {
  summary: {
    id: string
    task: string
    status: ExecutionState['status']
    confidence: number
    mutations: number
    startedAt: string
  }
  state: ExecutionState
}

const STORAGE_KEY = 'aethermesh_past_runs_v1'

export function getLocalPastRuns(): PastRunItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw)
  } catch {
    return []
  }
}

export function savePastRun(state: ExecutionState): void {
  if (!state.task) return
  try {
    const runs = getLocalPastRuns()
    const id = state.workflow?.id || `run-${Date.now()}`
    const newItem: PastRunItem = {
      summary: {
        id,
        task: state.task,
        status: state.status,
        confidence: state.confidence,
        mutations: state.metrics?.mutations || 0,
        startedAt: state.events?.[0]?.timestamp || new Date().toISOString(),
      },
      state: { ...state, workflow: { ...state.workflow, id } },
    }

    // Prepend new run and deduplicate by id
    const filtered = runs.filter((r) => r.summary.id !== id && r.summary.task !== state.task)
    const updated = [newItem, ...filtered]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch (err) {
    console.error('Failed to save run to localStorage:', err)
  }
}
