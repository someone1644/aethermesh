import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { pastRuns as mockPastRuns } from '../mocks/executionState'
import { useRuntimeStore } from '../store/runtimeStore'
import { API_BASE, USE_MOCKS } from '../api/runtime'
import { getLocalPastRuns, clearLocalPastRuns, deletePastRun } from '../lib/pastRunsStore'
import type { ExecutionState } from '../types/runtime'

const STATUS_DOT: Record<string, string> = {
  completed: '#1E8E3E',
  failed: '#D93025',
  running: '#D97706',
  idle: '#9CA3AF',
  paused_for_approval: '#D97706',
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="text-xs text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-[var(--color-text)]">{value}</div>
    </div>
  )
}

export default function PastRuns() {
  const navigate = useNavigate()
  const setExecutionState = useRuntimeStore((s) => s.setExecutionState)
  const [query, setQuery] = useState('')
  const [runs, setRuns] = useState<{ summary: any; state: ExecutionState }[]>([])

  useEffect(() => {
    const localRuns = getLocalPastRuns()

    if (USE_MOCKS) {
      const merged = [...localRuns, ...mockPastRuns]
      const deduped = merged.filter((item, index, self) =>
        index === self.findIndex((t) => t.summary.id === item.summary.id)
      )
      setRuns(deduped)
      return
    }

    fetch(`${API_BASE}/history`)
      .then((res) => res.json())
      .then((data) => {
        const backendRuns = Array.isArray(data) ? data : []
        const merged = [...localRuns, ...backendRuns, ...mockPastRuns]
        const deduped = merged.filter((item, index, self) =>
          index === self.findIndex((t) => t.summary.id === item.summary.id || t.summary.task === item.summary.task)
        )
        setRuns(deduped)
      })
      .catch(() => {
        const merged = [...localRuns, ...mockPastRuns]
        setRuns(merged)
      })
  }, [])

  const filtered = useMemo(
    () => runs.filter((r) => r.summary.task.toLowerCase().includes(query.toLowerCase())),
    [query, runs],
  )

  const total = runs.length
  const completed = runs.filter((r) => r.summary.status === 'completed').length
  const failed = runs.filter((r) => r.summary.status === 'failed').length
  const avgConfidence = total ? runs.reduce((sum, r) => sum + (r.summary.confidence || 0), 0) / total : 0

  const openRun = (id: string) => {
    const run = runs.find((r) => r.summary.id === id)
    if (!run) return
    setExecutionState(run.state)
    navigate('/run')
  }

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all local execution history?')) {
      clearLocalPastRuns()
      setRuns([])
    }
  }

  const handleDeleteRun = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    deletePastRun(id)
    setRuns((prev) => prev.filter((r) => r.summary.id !== id))
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Past Runs</h1>
        {runs.length > 0 && (
          <button
            type="button"
            onClick={handleClearHistory}
            className="rounded border border-[var(--color-status-failed)] px-3 py-1.5 font-mono text-xs font-medium text-[var(--color-status-failed)] hover:bg-[#FDECEA]"
          >
            Clear History
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total runs" value={total ? String(total) : '-'} />
        <StatTile label="Completed" value={total ? String(completed) : '-'} />
        <StatTile label="Failed" value={total ? String(failed) : '-'} />
        <StatTile label="Avg confidence" value={total ? `${Math.round(avgConfidence * 100)}%` : '-'} />
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for a task…"
        className="w-full max-w-sm rounded-md border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-text)] focus:outline-none"
      />

      <div className="overflow-x-auto rounded-lg border border-[var(--color-border)]">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)] font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
              <th className="px-4 py-2.5">Task</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5">Confidence</th>
              <th className="px-4 py-2.5">Mutations</th>
              <th className="px-4 py-2.5">Started</th>
              <th className="px-4 py-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr
                key={r.summary.id}
                onClick={() => openRun(r.summary.id)}
                className="cursor-pointer border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-hover)]"
              >
                <td className="px-4 py-2.5 text-[var(--color-text)]">{r.summary.task}</td>
                <td className="px-4 py-2.5">
                  <span className="inline-flex items-center gap-1.5 font-mono text-xs uppercase text-[var(--color-text-muted)]">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: STATUS_DOT[r.summary.status] ?? '#9CA3AF' }}
                    />
                    {r.summary.status}
                  </span>
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-[var(--color-text)]">
                  {Math.round((r.summary.confidence || 0) * 100)}%
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-[var(--color-text)]">{r.summary.mutations || 0}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-[var(--color-text-muted)]">
                  {r.summary.startedAt ? dayjs(r.summary.startedAt).format('MMM D, HH:mm') : '—'}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button
                    type="button"
                    onClick={(e) => handleDeleteRun(e, r.summary.id)}
                    className="font-mono text-xs text-[var(--color-status-failed)] opacity-80 hover:opacity-100 hover:underline"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-[var(--color-text-muted)]">
                  No past runs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
