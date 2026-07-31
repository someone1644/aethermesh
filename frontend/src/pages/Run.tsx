import { useMemo, useState } from 'react'
import { useRuntime } from '../hooks/useRuntime'
import { useRuntimeStore } from '../store/runtimeStore'
import StatusBadge from '../components/common/StatusBadge'
import FinalOutput from '../components/chat/FinalOutput'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'
import EventLog from '../components/sidebar/EventLog'
import PolicyTriggerChip from '../components/sidebar/PolicyTriggerChip'
import AgentIdentityCard from '../components/sidebar/AgentIdentityCard'
import WorkflowCanvas from '../components/workflow/WorkflowCanvas'
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

  // Result panel only makes sense once the final producing step is queued
  // up to run — before that there's nothing to show it for.
  const nodes = executionState.workflow.nodes
  const lastNode = nodes[nodes.length - 1]
  const showResultPanel = lastNode
    ? ['ready', 'active', 'completed', 'failed'].includes(lastNode.status)
    : false

  return (
    <div className="flex h-screen">
      {/* LEFT COLUMN — diagram, confidence, event log */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
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

            {/* Relative anchor so the expanded event log can overlay the diagram exactly. */}
            <div className="relative">
              <div className="h-[360px] w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2 shadow-sm">
                <WorkflowCanvas workflow={executionState.workflow} />
                {mutationNote && <p className="p-3 font-mono text-xs text-[#B45309]">{mutationNote}</p>}
              </div>

              <div className="mt-8 flex items-start gap-8">
                <div className="flex-1">
                  <ConfidenceMeter confidence={executionState.confidence} />
                </div>
                <div className="w-56 shrink-0">
                  <PolicyTriggerChip events={executionState.events} />
                </div>
              </div>

              <div className="mt-8">
                <EventLog events={executionState.events} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — agent identity + result, shown only once the final step is underway */}
      {showResultPanel && (
        <aside className="w-[320px] shrink-0 space-y-4 overflow-y-auto border-l border-[var(--color-border)] bg-[var(--color-bg)] px-4 pb-4 pt-8">
          <AgentIdentityCard />
          <FinalOutput output={executionState.final_output} />
        </aside>
      )}
    </div>
  )
}
