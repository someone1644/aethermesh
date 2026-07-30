import { useCallback } from 'react'
import { useRuntimeStore } from '../store/runtimeStore'
import { subscribeToEvents, subscribeToExecution, type ExecutionStreamPayload } from '../api/events'
import { startTask } from '../api/client'
import { USE_MOCKS } from '../api/runtime'
import { completedExecutionState } from '../mocks/executionState'
import { initialWorkflow } from '../lib/workflowEvents'
import { normalizeStatus } from '../types/runtime'
import { savePastRun } from '../lib/pastRunsStore'

const LIVE_STEP_MS = 700

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function useEvents() {
  const setExecutionState = useRuntimeStore((s) => s.setExecutionState)
  const patchExecutionState = useRuntimeStore((s) => s.patchExecutionState)
  const appendEvent = useRuntimeStore((s) => s.appendEvent)
  const setLive = useRuntimeStore((s) => s.setLive)

  const simulateLiveRun = useCallback(
    async (task?: string) => {
      const targetTask = task ?? completedExecutionState.task
      setExecutionState({
        task: targetTask,
        status: 'running',
        confidence: 0,
        repository_found: true,
        contradiction_score: 0,
        sources: 0,
        final_output: '',
        workflow: initialWorkflow,
        events: [],
        metrics: { execution_time: 0, mutations: 0, completed_agents: 0, failed_agents: 0, confidence: 0 },
      })
      setLive(true)

      if (!USE_MOCKS) {
        try {
          const { workflow_id, workflow } = await startTask(targetTask)
          patchExecutionState({ workflow: { ...workflow, id: workflow_id } })

          const applyPayload = (payload: ExecutionStreamPayload) => {
            appendEvent(payload.event)
            patchExecutionState({
              status: normalizeStatus(payload.state.status),
              confidence: payload.state.confidence,
              final_output: payload.state.final_output,
              repository_found: payload.state.repository_found,
              contradiction_score: payload.state.contradiction_score,
              sources: payload.state.sources,
              metrics: payload.state.metrics,
            })
          }

          await new Promise<void>((resolve) => {
            const queue: ExecutionStreamPayload[] = []
            let draining = false
            let streamDone = false

            const drain = async () => {
              if (draining) return
              draining = true
              while (queue.length > 0) {
                const payload = queue.shift()!
                applyPayload(payload)
                if (payload.event.event_type === 'workflow_completed') {
                  draining = false
                  resolve()
                  return
                }
                await sleep(LIVE_STEP_MS)
              }
              draining = false
              if (streamDone) resolve()
            }

            subscribeToExecution(
              workflow_id,
              (payload) => {
                queue.push(payload)
                void drain()
              },
              () => {
                streamDone = true
                void drain()
              },
            )
          })
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Task execution failed.'
          patchExecutionState({ status: 'failed', final_output: message })
        } finally {
          setLive(false)
          // Save current state to local past runs store
          const latestState = useRuntimeStore.getState().executionState
          savePastRun(latestState)
        }
        return
      }

      // Mock Mode
      const unsubscribe = subscribeToEvents((event) => {
        appendEvent(event)
        if (event.event_type === 'workflow_completed') {
          patchExecutionState({ status: 'completed' })
          setLive(false)
          unsubscribe()

          // Save completed run to past runs store
          const latestState = useRuntimeStore.getState().executionState
          savePastRun(latestState)
        }
      })
    },
    [setExecutionState, patchExecutionState, appendEvent, setLive],
  )

  return { simulateLiveRun }
}
