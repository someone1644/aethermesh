import { useRuntime } from '../hooks/useRuntime'
import WorkflowCanvas from '../components/workflow/WorkflowCanvas'
import Legend from '../components/workflow/Legend'

export default function WorkflowGraph() {
  const { executionState } = useRuntime()

  return (
    <div className="flex h-[calc(100vh-88px)] flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-mono text-sm uppercase tracking-wide text-[var(--color-text-muted)]">
          Workflow Graph
        </h1>
        <Legend />
      </div>
      <div className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <WorkflowCanvas workflow={executionState.workflow} />
      </div>
    </div>
  )
}
