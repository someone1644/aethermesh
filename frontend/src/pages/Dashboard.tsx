import { Link } from 'react-router-dom'
import { useRuntime } from '../hooks/useRuntime'

export default function Dashboard() {
  const { executionState } = useRuntime()
  const m = executionState.metrics

  const stats = [
    { label: 'Agents completed', value: String(m.completed_agents), color: '#34d399' },
    { label: 'Mutations', value: String(m.mutations), color: '#fbbf24' },
    { label: 'Confidence', value: `${Math.round(executionState.confidence * 100)}%`, color: '#6366f1' },
    { label: 'Exec time', value: `${m.execution_time.toFixed(1)}s`, color: '#22d3ee' },
  ]

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-10 px-6 py-16">
      {/* Decorative gradient orbs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 left-1/4 h-96 w-96 rounded-full bg-indigo-500/5 blur-3xl animate-float" />
        <div className="absolute -bottom-32 right-1/4 h-96 w-96 rounded-full bg-cyan-500/5 blur-3xl animate-float" style={{ animationDelay: '1.5s' }} />
      </div>

      {/* Hero */}
      <div className="relative z-10 max-w-2xl text-center animate-fade-in-up">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-400 shadow-xl shadow-indigo-500/20 animate-float">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold tracking-tight gradient-text sm:text-5xl">
          AetherMesh
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-[var(--color-text-muted)]">
          An adaptive runtime that monitors multi-agent AI execution, detects failures, and safely
          adapts workflows while explaining every runtime decision through replayable audit logs.
        </p>
      </div>

      {/* Stats grid */}
      <div className="relative z-10 grid w-full max-w-2xl grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
        {stats.map((s, i) => (
          <div
            key={s.label}
            className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 card-hover animate-fade-in-up stagger-${i + 1}`}
          >
            <div className="text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">{s.label}</div>
            <div className="mt-1 text-2xl font-bold font-mono" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className="relative z-10 flex gap-3 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
        <Link
          to="/prompt"
          className="rounded-xl btn-primary px-6 py-3 text-sm font-medium shadow-lg shadow-indigo-500/20"
        >
          New task →
        </Link>
        <Link
          to="/runs"
          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 text-sm font-medium text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]"
        >
          Past runs
        </Link>
      </div>

      {/* Last task banner */}
      {executionState.task && (
        <div className="relative z-10 w-full max-w-2xl animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
            <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-[var(--color-text-faint)]">Last task</div>
            <p className="text-sm text-[var(--color-text)]">{executionState.task}</p>
          </div>
        </div>
      )}
    </div>
  )
}
