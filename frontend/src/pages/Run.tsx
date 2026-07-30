import { useMemo, useState } from 'react'
import { useRuntime } from '../hooks/useRuntime'
import { useRuntimeStore } from '../store/runtimeStore'
import StatusBadge from '../components/common/StatusBadge'
import FinalOutput from '../components/chat/FinalOutput'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'
import EventLog from '../components/sidebar/EventLog'
import AgentFlowDiagram from '../components/workflow/AgentFlowDiagram'
import { API_BASE, USE_MOCKS } from '../api/runtime'

export default function Run() {
  const { executionState, policyDecisions } = useRuntime()
  const patchExecutionState = useRuntimeStore((s) => s.patchExecutionState)
  const [approving, setApproving] = useState(false)

  const lastMutation = useMemo(
    () => [...policyDecisions].reverse().find((d) => d.action === 'replace'),
    [policyDecisions],
  )

  const mutationNote = lastMutation
    ? `↻ mutation: ${lastMutation.target_node} replaced by ${lastMutation.new_node} — ${lastMutation.reason}`
    : undefined

  const handleAction = async (action: 'approve' | 'abort') => {
    setApproving(true)
    const workflowId = executionState.workflow.id
    if (!USE_MOCKS && workflowId) {
      try {
        await fetch(`${API_BASE}/execute/${workflowId}/approve?action=${action}`, {
          method: 'POST',
        })
      } catch (err) {
        console.error('Failed to submit approval:', err)
      }
    }
    if (action === 'approve') {
      patchExecutionState({ status: 'running' })
    } else {
      patchExecutionState({ status: 'failed' })
    }
    setApproving(false)
  }

  const isPaused = executionState.status === 'paused_for_approval'

  return (
    <div className="flex h-screen flex-col">
      <div className="flex-1 overflow-y-auto pb-80">
        <div className="mx-auto max-w-7xl space-y-8 p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-lg font-semibold text-[var(--color-text)]">
                {executionState.task || 'No task running'}
              </h1>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">Live execution view</p>
            </div>
            <StatusBadge status={executionState.status} />
          </div>

          {/* HITL Intervention Modal Banner */}
          {isPaused && (
            <div className="rounded-lg border border-[var(--color-accent)] bg-[#FEF3E2] p-4 text-sm text-[#92400E]">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <span className="font-semibold uppercase tracking-wide">
                    Human Intervention Required
                  </span>
                  <p className="mt-0.5 text-xs text-[#B45309]">
                    Policy triggered a high-priority graph mutation. Review and approve to resume.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleAction('approve')}
                    disabled={approving}
                    className="rounded bg-[#D97706] px-3.5 py-1.5 font-mono text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                  >
                    Approve Mutation
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAction('abort')}
                    disabled={approving}
                    className="rounded border border-[#D97706] px-3 py-1.5 font-mono text-xs font-semibold text-[#92400E] hover:bg-white/40 disabled:opacity-50"
                  >
                    Abort Run
                  </button>
                </div>
              </div>
            </div>
          )}

          <AgentFlowDiagram nodes={executionState.workflow.nodes} mutationNote={mutationNote} />

          <div className="max-w-xs">
            <ConfidenceMeter confidence={executionState.confidence} />
          </div>

          <FinalOutput output={executionState.final_output} />
          <div className="h-48" />
        </div>
      </div>

      <EventLog events={executionState.events} />
    </div>
  )
}
