import type { ExecutionMetrics } from '../../types/runtime'

function confidenceColor(confidence: number): string {
  if (confidence < 0.5) return 'var(--color-status-failed)'
  if (confidence < 0.8) return '#D97706'
  return 'var(--color-status-completed)'
}

export function ConfidenceMeter({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color = confidenceColor(confidence)

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
        <span>Confidence</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-[var(--color-border)]">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}

export default function MetricsPanel({
  confidence,
  metrics,
  contradictionScore,
  repositoryFound,
  sources,
}: {
  confidence: number
  metrics: ExecutionMetrics
  contradictionScore: number
  repositoryFound: boolean
  sources: number
}) {
  const rows: [string, string][] = [
    ['Execution time', `${metrics.execution_time.toFixed(1)}s`],
    ['Mutations', String(metrics.mutations)],
    ['Completed agents', String(metrics.completed_agents)],
    ['Failed agents', String(metrics.failed_agents)],
    ['Contradiction score', contradictionScore.toFixed(2)],
    ['Repository found', repositoryFound ? 'yes' : 'no'],
    ['Sources', String(sources)],
  ]

  return (
    <div className="space-y-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <ConfidenceMeter confidence={confidence} />
      <dl className="grid grid-cols-2 gap-x-3 gap-y-2 border-t border-[var(--color-border)] pt-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex flex-col">
            <dt className="text-xs text-[var(--color-text-muted)]">{label}</dt>
            <dd className="font-mono text-[var(--color-text)]">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
