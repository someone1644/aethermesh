import { useCallback } from 'react'
import { useRuntimeStore } from '../store/runtimeStore'
import { subscribeToEvents } from '../api/events'
import { completedExecutionState } from '../mocks/executionState'
import { initialWorkflow } from '../lib/workflowEvents'

/** Drives the mock live-run simulation: resets to an all-pending workflow, then replays events over time. */
export function useEvents() {
  const setExecutionState = useRuntimeStore((s) => s.setExecutionState)
  const appendEvent = useRuntimeStore((s) => s.appendEvent)
  const setLive = useRuntimeStore((s) => s.setLive)

  const simulateLiveRun = useCallback(
    (task?: string) => {
      setExecutionState({
        ...completedExecutionState,
        task: task ?? completedExecutionState.task,
        status: 'running',
        confidence: 0,
        final_output: '',
        workflow: initialWorkflow,
        events: [],
        metrics: { execution_time: 0, mutations: 0, completed_agents: 0, failed_agents: 0, confidence: 0 },
      })
      setLive(true)

      const unsubscribe = subscribeToEvents((event) => {
        appendEvent(event)
        if (event.event_type === 'workflow_completed') {
          setExecutionState({ ...completedExecutionState, task: task ?? completedExecutionState.task })
          setLive(false)
          unsubscribe()
        }
      })
    },
    [setExecutionState, appendEvent, setLive],
  )

  return { simulateLiveRun }
}
