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
      <div className="max-w-xl text-center">
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">What should AetherMesh work on?</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Describe a task. AetherMesh will plan, execute, and adapt the workflow as it runs.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-xl">
        <div className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-white px-4 py-3 shadow-sm focus-within:border-[var(--color-text)]">
          <input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder={PLACEHOLDERS[placeholderIndex]}
            disabled={isLive}
            className="flex-1 bg-transparent text-sm text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-muted)] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLive || !task.trim()}
            className="rounded-md bg-[var(--color-primary)] px-4 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
          >
            {isLive ? 'Running…' : 'Run'}
          </button>
        </div>
      </form>

      <div className="grid w-full max-w-2xl grid-cols-3 gap-2.5">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => start(s)}
            disabled={isLive}
            className="rounded-lg border border-[var(--color-border)] px-3.5 py-3.5 text-left text-xs text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
