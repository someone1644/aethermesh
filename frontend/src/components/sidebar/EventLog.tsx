import { useEffect, useRef, useState } from 'react'
import dayjs from 'dayjs'
import type { EventType, RuntimeEvent } from '../../types/event'

const EVENT_COLOR: Record<EventType, string> = {
  workflow_started: '#9CA3AF',
  agent_started: '#9CA3AF',
  agent_completed: '#4ADE80',
  workflow_completed: '#4ADE80',
  node_added: '#9CA3AF',
  node_removed: '#F87171',
  node_replaced: '#FBBF24',
  policy_triggered: '#FBBF24',
}

function LogLine({ event }: { event: RuntimeEvent }) {
  return (
    <div className="flex gap-3 py-0.5">
      <span className="shrink-0 text-gray-500">{dayjs(event.timestamp).format('HH:mm:ss')}</span>
      <span className="shrink-0" style={{ color: EVENT_COLOR[event.event_type] }}>
        [{event.event_type}]
      </span>
      <span className="text-gray-200">{event.reason}</span>
    </div>
  )
}

/** VS Code-terminal-style docked event log. Lives only on the Run page. */
export default function EventLog({ events }: { events: RuntimeEvent[] }) {
  const [expanded, setExpanded] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!expanded || !autoScroll || !scrollRef.current) return
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [events, expanded, autoScroll])

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24
    setAutoScroll(atBottom)
  }

  const jumpToLatest = () => {
    setAutoScroll(true)
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }

  const peekEvents = events.slice(-4)

  return (
    <div className="fixed inset-x-0 bottom-0 left-56 z-10 bg-[var(--color-bg)]">
      {/* Matches the flow diagram container's max-width + padding above so the panel's edges line up. */}
      <div className="mx-auto max-w-7xl px-8">
        <div className="overflow-hidden rounded-t-lg border border-b-0 border-[var(--color-border)] bg-[#111214] text-gray-100">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2 font-mono text-xs uppercase tracking-wide text-gray-300 hover:bg-white/5"
          >
            <span>event log · {events.length}</span>
            <span aria-hidden="true">{expanded ? '⌄' : '⌃'}</span>
          </button>

          {expanded ? (
            <div className="relative">
              <div
                ref={scrollRef}
                onScroll={handleScroll}
                className="h-[380px] overflow-y-auto border-t border-white/10 px-4 py-2 font-mono text-xs leading-relaxed"
              >
                {events.length === 0 && <div className="text-gray-500">waiting for events…</div>}
                {events.map((e) => (
                  <LogLine key={e.id} event={e} />
                ))}
              </div>
              {!autoScroll && (
                <button
                  type="button"
                  onClick={jumpToLatest}
                  className="absolute bottom-3 right-4 rounded-full bg-white/10 px-3 py-1 text-[10px] text-gray-200 hover:bg-white/20"
                >
                  jump to latest ↓
                </button>
              )}
            </div>
          ) : (
            <div className="h-28 overflow-hidden border-t border-white/10 px-4 py-2 font-mono text-xs leading-relaxed">
              {peekEvents.length === 0 && <div className="text-gray-500">waiting for events…</div>}
              {peekEvents.map((e) => (
                <LogLine key={e.id} event={e} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
