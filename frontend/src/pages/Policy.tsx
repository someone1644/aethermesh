import { useRuntime } from '../hooks/useRuntime'
import DecisionPanel from '../components/sidebar/DecisionPanel'
import { ConfidenceMeter } from '../components/sidebar/MetricsPanel'

export default function Policy() {
  const { executionState, policyDecisions } = useRuntime()

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Policy</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Runtime policies AetherMesh evaluates during execution. Once a task has run,
          this shows the decisions the policy engine actually triggered.
        </p>
      </div>

      {executionState.events.length > 0 && (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <ConfidenceMeter confidence={executionState.confidence} />
          <p className="mt-3 text-sm text-[var(--color-text-muted)]">
            Contradiction score:{' '}
            <span className="font-mono text-[var(--color-text)]">
              {executionState.contradiction_score.toFixed(2)}
            </span>
            {' · '}
            Repository found:{' '}
            <span className="font-mono text-[var(--color-text)]">
              {executionState.repository_found ? 'yes' : 'no'}
            </span>
            {' · '}
            Triggered policies:{' '}
            <span className="font-mono text-[var(--color-text)]">{policyDecisions.length}</span>
          </p>
        </div>
      )}

      <DecisionPanel decisions={policyDecisions} />
    </div>
  )
}
