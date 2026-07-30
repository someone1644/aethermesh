import dayjs from 'dayjs'
import { useRuntime } from '../hooks/useRuntime'
import type { EventType } from '../types/event'

const EVENT_COLOR: Record<EventType, string> = {
  workflow_started: 'bg-gray-400',
  workflow_completed: 'bg-emerald-400',
  agent_started: 'bg-sky-400',
  agent_completed: 'bg-emerald-400',
  node_added: 'bg-sky-400',
  node_removed: 'bg-red-400',
  node_replaced: 'bg-[var(--color-accent)]',
  policy_triggered: 'bg-amber-400',
}

export default function Timeline() {
  const { executionState } = useRuntime()
  const events = executionState.events

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="font-mono text-sm uppercase tracking-wide text-[var(--color-text-muted)]">
        Execution Timeline
      </h1>

      {events.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[var(--color-border)] p-4 text-sm text-[var(--color-text-muted)]">
          No events yet.
        </div>
      ) : (
        <ol className="relative space-y-6 border-l border-[var(--color-border)] pl-6">
          {events.map((event) => (
            <li key={event.id} className="relative">
              <span
                className={`absolute -left-[29px] top-1 h-3 w-3 rounded-full ring-4 ring-[var(--color-bg)] ${EVENT_COLOR[event.event_type]}`}
              />
              <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
                  {event.event_type.replace(/_/g, ' ')}
                </span>
                <span className="font-mono text-xs text-[var(--color-text-muted)]">
                  {dayjs(event.timestamp).format('HH:mm:ss.SSS')}
                </span>
              </div>
              <p className="mt-1 text-sm text-[var(--color-text)]">{event.reason}</p>
              {Object.keys(event.details).length > 0 && (
                <pre className="mt-2 overflow-x-auto rounded-md bg-[var(--color-surface)] p-2 font-mono text-xs text-[var(--color-text-muted)]">
                  {JSON.stringify(event.details, null, 2)}
                </pre>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
