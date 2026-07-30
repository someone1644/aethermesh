import { useRuntime } from '../hooks/useRuntime'
import DecisionPanel from '../components/sidebar/DecisionPanel'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'

export default function PolicyInspector() {
  const { executionState, policyDecisions } = useRuntime()

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="font-mono text-sm uppercase tracking-wide text-[var(--color-text-muted)]">
        Policy Inspector
      </h1>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <ConfidenceMeter confidence={executionState.confidence} />
        <p className="mt-3 text-sm text-[var(--color-text-muted)]">
          Contradiction score: <span className="font-mono text-[var(--color-text)]">{executionState.contradiction_score.toFixed(2)}</span>
          {' · '}
          Repository found: <span className="font-mono text-[var(--color-text)]">{executionState.repository_found ? 'yes' : 'no'}</span>
        </p>
      </div>

      <div>
        <h2 className="mb-3 font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
          Triggered policies · {policyDecisions.length}
        </h2>
        <DecisionPanel decisions={policyDecisions} />
      </div>
    </div>
  )
}
