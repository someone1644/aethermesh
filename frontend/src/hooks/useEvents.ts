import { useCallback } from 'react'
import { useRuntimeStore } from '../store/runtimeStore'
import { subscribeToEvents, subscribeToExecution, type ExecutionStreamPayload } from '../api/events'
import { startTask } from '../api/client'
import { USE_MOCKS } from '../api/runtime'
import { completedExecutionState } from '../mocks/executionState'
import { initialWorkflow } from '../lib/workflowEvents'
import { normalizeStatus } from '../types/runtime'

/** Minimum time each live event stays the "current" one before the next is applied.
 * The backend can legitimately log several events within milliseconds of each
 * other (e.g. a policy firing right as an agent completes), and a fast local
 * fallback response can make a node's active window near-instant. Without this,
 * those arrive faster than a human can perceive. This paces *display* only —
 * it never delays picking up new events that already arrived, so a genuinely
 * slow run (real Gemini calls) is never held back. */
const LIVE_STEP_MS = 700

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Drives execution: streams a real run live in real mode, or replays mock events in mock mode. */
export function useEvents() {
  const setExecutionState = useRuntimeStore((s) => s.setExecutionState)
  const patchExecutionState = useRuntimeStore((s) => s.patchExecutionState)
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
          const { workflow_id, workflow } = await startTask(targetTask)
          // Seed with the real backend-generated workflow (real node ids) so
          // live events — which reference those same ids — fold in correctly.
          patchExecutionState({ workflow })

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

          // Events are queued as they arrive (true live order, no waiting for
          // the run to finish) but drained one at a time with a minimum step
          // duration, so a burst of backend events still renders as a visible
          // sequence rather than jumping several log entries at once.
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
    [setExecutionState, patchExecutionState, appendEvent, setLive],
  )

  return { simulateLiveRun }
}
