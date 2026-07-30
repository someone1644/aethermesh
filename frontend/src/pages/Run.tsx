import { useMemo } from 'react'
import { useRuntime } from '../hooks/useRuntime'
import StatusBadge from '../components/common/StatusBadge'
import FinalOutput from '../components/chat/FinalOutput'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'
import EventLog from '../components/sidebar/EventLog'
import AgentFlowDiagram from '../components/workflow/AgentFlowDiagram'
import Loader from '../components/common/Loader'

export default function Run() {
  const { executionState, isLive, policyDecisions } = useRuntime()

  const lastMutation = useMemo(
    () => [...policyDecisions].reverse().find((d) => d.action === 'replace'),
    [policyDecisions],
  )

  const mutationNote = lastMutation
    ? `↻ mutation: ${lastMutation.target_node} replaced by ${lastMutation.new_node} — ${lastMutation.reason}`
    : undefined

  return (
    <div className="flex h-screen flex-col">
      <div className="flex-1 overflow-y-auto pb-44">
        <div className="mx-auto max-w-7xl space-y-8 p-8">
          <div className="flex items-start justify-between gap-4 animate-fade-in-down">
            <div>
              <h1 className="text-lg font-semibold text-[var(--color-text)]">
                {executionState.task || 'No task running'}
              </h1>
              <div className="mt-1 flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
                <span>Live execution view</span>
                {isLive && <Loader label="Processing…" />}
              </div>
            </div>
            <StatusBadge status={executionState.status} />
          </div>

          <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <AgentFlowDiagram nodes={executionState.workflow.nodes} mutationNote={mutationNote} />
          </div>

          <div className="max-w-xs animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            <ConfidenceMeter confidence={executionState.confidence} />
          </div>

          <div className="animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
            <FinalOutput output={executionState.final_output} />
          </div>
        </div>
      </div>

      <EventLog events={executionState.events} />
    </div>
  )
}
