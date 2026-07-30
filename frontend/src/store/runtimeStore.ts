import { create } from 'zustand'
import type { ExecutionState } from '../types/runtime'
import type { RuntimeEvent } from '../types/event'
import { idleExecutionState } from '../mocks/executionState'
import { applyEventToWorkflow } from '../lib/workflowEvents'

interface RuntimeStore {
  executionState: ExecutionState
  isLive: boolean
  setExecutionState: (state: ExecutionState) => void
  patchExecutionState: (patch: Partial<ExecutionState>) => void
  appendEvent: (event: RuntimeEvent) => void
  setLive: (live: boolean) => void
}

export const useRuntimeStore = create<RuntimeStore>((set) => ({
  executionState: idleExecutionState,
  isLive: false,
  setExecutionState: (state) => set({ executionState: state }),
  patchExecutionState: (patch) =>
    set((s) => ({ executionState: { ...s.executionState, ...patch } })),
  appendEvent: (event) =>
    set((s) => ({
      executionState: {
        ...s.executionState,
        events: [...s.executionState.events, event],
        workflow: applyEventToWorkflow(s.executionState.workflow, event),
      },
    })),
  setLive: (live) => set({ isLive: live }),
}))
