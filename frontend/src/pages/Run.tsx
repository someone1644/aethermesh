import { useMemo } from 'react'
import { useRuntime } from '../hooks/useRuntime'
import StatusBadge from '../components/common/StatusBadge'
import FinalOutput from '../components/chat/FinalOutput'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'
import EventLog from '../components/sidebar/EventLog'
import AgentFlowDiagram from '../components/workflow/AgentFlowDiagram'

export default function Run() {
  const { executionState, policyDecisions } = useRuntime()

  const lastMutation = useMemo(
    () => [...policyDecisions].reverse().find((d) => d.action === 'replace'),
    [policyDecisions],
  )

  const mutationNote = lastMutation
    ? `↻ mutation: ${lastMutation.target_node} replaced by ${lastMutation.new_node} — ${lastMutation.reason}`
    : undefined

  return (
    <div className="flex h-screen flex-col">
      <div className="flex-1 overflow-y-auto pb-14">
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

          <AgentFlowDiagram nodes={executionState.workflow.nodes} mutationNote={mutationNote} />

          <div className="max-w-xs">
            <ConfidenceMeter confidence={executionState.confidence} />
          </div>

          <FinalOutput output={executionState.final_output} />
        </div>
      </div>

      <EventLog events={executionState.events} />
    </div>
  )
}
