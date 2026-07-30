import type { ExecutionMetrics } from '../../types/runtime'

function confidenceColor(confidence: number): string {
  if (confidence < 0.5) return '#f87171'
  if (confidence < 0.8) return '#fbbf24'
  return '#34d399'
}

function confidenceGlow(confidence: number): string {
  if (confidence < 0.5) return 'shadow-red-500/10'
  if (confidence < 0.8) return 'shadow-amber-500/10'
  return 'shadow-emerald-500/10'
}

export function ConfidenceMeter({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color = confidenceColor(confidence)

  return (
    <div>
      <div className="mb-2 flex items-center justify-between font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
        <span>Confidence</span>
        <span className="text-sm font-semibold" style={{ color }}>{pct}%</span>
      </div>
      <div className={`h-2 w-full overflow-hidden rounded-full bg-[var(--color-surface-hover)] shadow-inner ${confidenceGlow(confidence)}`}>
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}, ${color}dd)`,
            boxShadow: `0 0 12px ${color}40`,
          }}
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
    <div className="space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 animate-fade-in-up">
      <ConfidenceMeter confidence={confidence} />
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-t border-[var(--color-border)] pt-4 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex flex-col gap-0.5">
            <dt className="text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">{label}</dt>
            <dd className="font-mono text-sm text-[var(--color-text)]">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
