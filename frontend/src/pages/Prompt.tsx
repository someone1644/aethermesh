import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useEvents } from '../hooks/useEvents'
import { useRuntime } from '../hooks/useRuntime'

const PLACEHOLDERS = [
  'Diagnose a failing CI pipeline…',
  "Summarize last quarter's incident postmortems…",
  'Investigate contradictory evidence in a document…',
  'Patch a flaky test suite…',
]

const SUGGESTIONS = [
  'Diagnose the failing checkout-service CI pipeline',
  'Summarize Q2 incident postmortems into one report',
  'Investigate contradictory evidence in refund-policy docs',
  'Find and fix the flakiest test in the suite',
  "Audit last week's failed deploys for root cause",
  'Draft a rollback plan for the payments service',
  'Trace a memory leak in the ingestion service',
  'Reconcile mismatched inventory counts across warehouses',
  'Explain why the nightly ETL job silently dropped rows',
  'Compare two API response schemas for breaking changes',
  'Identify the root cause of a spike in 5xx errors',
  'Validate a database migration against staging data',
]

export default function Prompt() {
  const [task, setTask] = useState('')
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const { simulateLiveRun } = useEvents()
  const { isLive } = useRuntime()
  const navigate = useNavigate()

  useEffect(() => {
    if (task) return undefined
    const timer = setInterval(() => setPlaceholderIndex((i) => (i + 1) % PLACEHOLDERS.length), 2600)
    return () => clearInterval(timer)
  }, [task])

  const start = (value: string) => {
    if (!value.trim() || isLive) return
    simulateLiveRun(value.trim())
    navigate('/run')
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    start(task)
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-6">
      {/* Decorative orb */}
      <div className="pointer-events-none absolute top-1/4 left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-indigo-500/[0.04] blur-3xl" />

      <div className="relative z-10 max-w-xl text-center animate-fade-in-up">
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">What should AetherMesh work on?</h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Describe a task. AetherMesh will plan, execute, and adapt the workflow as it runs.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative z-10 w-full max-w-xl animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <div className="glass flex items-center gap-2 rounded-2xl px-5 py-4 shadow-xl shadow-black/20 focus-within:border-[var(--color-primary)] transition-colors">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5" className="shrink-0 text-[var(--color-text-faint)]">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder={PLACEHOLDERS[placeholderIndex]}
            disabled={isLive}
            className="flex-1 bg-transparent text-sm text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-faint)] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLive || !task.trim()}
            className="rounded-xl btn-primary px-5 py-2 text-sm font-medium"
          >
            {isLive ? 'Running…' : 'Run →'}
          </button>
        </div>
      </form>

      <div className="relative z-10 grid w-full max-w-2xl grid-cols-2 gap-2.5 sm:grid-cols-3 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
        {SUGGESTIONS.map((s, i) => (
          <button
            key={s}
            type="button"
            onClick={() => start(s)}
            disabled={isLive}
            className={`group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-3.5 text-left text-xs text-[var(--color-text-muted)] card-hover disabled:opacity-40 animate-fade-in-up stagger-${i + 1}`}
          >
            <span className="transition-colors group-hover:text-[var(--color-text)]">{s}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
