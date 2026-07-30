import { useCallback } from 'react'
import { useRuntimeStore } from '../store/runtimeStore'
import { subscribeToEvents } from '../api/events'
import { submitTask } from '../api/client'
import { USE_MOCKS } from '../api/runtime'
import { completedExecutionState } from '../mocks/executionState'
import { initialWorkflow } from '../lib/workflowEvents'

/** Drives execution: calls submitTask in real mode, or replays mock events in mock mode. */
export function useEvents() {
  const setExecutionState = useRuntimeStore((s) => s.setExecutionState)
  const appendEvent = useRuntimeStore((s) => s.appendEvent)
  const setLive = useRuntimeStore((s) => s.setLive)

  const simulateLiveRun = useCallback(
    async (task?: string) => {
      const targetTask = task ?? completedExecutionState.task
      setExecutionState({
        ...completedExecutionState,
        task: targetTask,
        status: 'running',
        confidence: 0,
        final_output: '',
        workflow: initialWorkflow,
        events: [],
        metrics: { execution_time: 0, mutations: 0, completed_agents: 0, failed_agents: 0, confidence: 0 },
      })
      setLive(true)

      if (!USE_MOCKS) {
        try {
          const result = await submitTask(targetTask)
          setExecutionState(result)
        } catch (err: any) {
          setExecutionState({
            ...completedExecutionState,
            task: targetTask,
            status: 'failed',
            final_output: err?.message || 'Task execution failed.',
          })
        } finally {
          setLive(false)
        }
        return
      }

      const unsubscribe = subscribeToEvents((event) => {
        appendEvent(event)
        if (event.event_type === 'workflow_completed') {
          setExecutionState({ ...completedExecutionState, task: targetTask })
          setLive(false)
          unsubscribe()
        }
      })
    },
    [setExecutionState, appendEvent, setLive],
  )

  return { simulateLiveRun }
}
