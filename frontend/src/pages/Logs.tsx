import { useState } from 'react'
import dayjs from 'dayjs'
import { useRuntime } from '../hooks/useRuntime'
import type { EventType } from '../types/event'

const EVENT_TYPES: EventType[] = [
  'workflow_started',
  'agent_started',
  'agent_completed',
  'node_added',
  'node_removed',
  'node_replaced',
  'policy_triggered',
  'workflow_completed',
]

export default function Logs() {
  const { executionState } = useRuntime()
  const [filter, setFilter] = useState<EventType | 'all'>('all')

  const rows =
    filter === 'all'
      ? executionState.events
      : executionState.events.filter((e) => e.event_type === filter)

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-mono text-sm uppercase tracking-wide text-[var(--color-text-muted)]">Logs</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as EventType | 'all')}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 font-mono text-xs text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
        >
          <option value="all">all events</option>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto rounded-lg border border-[var(--color-border)]">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)] font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Event</th>
              <th className="px-3 py-2">Reason</th>
              <th className="px-3 py-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((event) => (
              <tr key={event.id} className="border-b border-[var(--color-border)] last:border-0">
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs text-[var(--color-text-muted)]">
                  {dayjs(event.timestamp).format('HH:mm:ss.SSS')}
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs text-[var(--color-text)]">
                  {event.event_type}
                </td>
                <td className="px-3 py-2 text-[var(--color-text)]">{event.reason}</td>
                <td className="px-3 py-2 font-mono text-xs text-[var(--color-text-muted)]">
                  {Object.keys(event.details).length > 0 ? JSON.stringify(event.details) : '—'}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">
                  No events match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
