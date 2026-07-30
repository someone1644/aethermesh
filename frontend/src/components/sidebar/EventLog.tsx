import { useEffect, useRef, useState } from 'react'
import dayjs from 'dayjs'
import type { EventType, RuntimeEvent } from '../../types/event'

const EVENT_COLOR: Record<EventType, string> = {
  workflow_started: '#71717a',
  agent_started: '#6366f1',
  agent_completed: '#34d399',
  workflow_completed: '#34d399',
  node_added: '#22d3ee',
  node_removed: '#f87171',
  node_replaced: '#fbbf24',
  policy_triggered: '#f59e0b',
}

function LogLine({ event }: { event: RuntimeEvent }) {
  return (
    <div className="flex gap-3 py-0.5 animate-fade-in">
      <span className="shrink-0 text-[var(--color-text-faint)]">{dayjs(event.timestamp).format('HH:mm:ss')}</span>
      <span
        className="shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px] uppercase"
        style={{ color: EVENT_COLOR[event.event_type], backgroundColor: `${EVENT_COLOR[event.event_type]}12` }}
      >
        {event.event_type}
      </span>
      <span className="text-[var(--color-text-muted)]">{event.reason}</span>
    </div>
  )
}

/** VS Code-terminal-style docked event log. Lives only on the Run page. */
export default function EventLog({ events, inline }: { events: RuntimeEvent[]; inline?: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (inline) {
      if (!autoScroll || !scrollRef.current) return
    } else {
      if (!expanded || !autoScroll || !scrollRef.current) return
    }
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [events, expanded, autoScroll, inline])

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

  // Inline mode — no fixed positioning, just a simple scrollable log
  if (inline) {
    return (
      <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[#0c0d12]">
        <div className="flex items-center justify-between border-b border-white/5 px-4 py-2 font-mono text-xs uppercase tracking-wide text-[var(--color-text-faint)]">
          <span>event log · {events.length}</span>
        </div>
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="relative h-[280px] overflow-y-auto px-4 py-2 font-mono text-xs leading-relaxed"
        >
          {events.length === 0 && <div className="text-[var(--color-text-faint)]">waiting for events…</div>}
          {events.map((e) => (
            <LogLine key={e.id} event={e} />
          ))}
          {!autoScroll && (
            <button
              type="button"
              onClick={jumpToLatest}
              className="sticky bottom-1 float-right rounded-full bg-white/10 px-3 py-1 text-[10px] text-[var(--color-text-muted)] hover:bg-white/15"
            >
              jump to latest ↓
            </button>
          )}
        </div>
      </div>
    )
  }

  // Fixed-bottom mode (used on Run page)
  const peekEvents = events.slice(-4)

  return (
    <div className="fixed inset-x-0 bottom-0 left-56 z-10">
      <div className="mx-auto max-w-7xl px-8">
        <div className="overflow-hidden rounded-t-xl border border-b-0 border-[var(--color-border)] bg-[#0c0d12] shadow-2xl shadow-black/40">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2.5 font-mono text-xs uppercase tracking-wide text-[var(--color-text-faint)] hover:bg-white/[0.02] transition-colors"
          >
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-primary)] animate-pulse" />
              event log · {events.length}
            </span>
            <span aria-hidden="true" className="text-base">{expanded ? '⌄' : '⌃'}</span>
          </button>

          {expanded ? (
            <div className="relative">
              <div
                ref={scrollRef}
                onScroll={handleScroll}
                className="h-[380px] overflow-y-auto border-t border-white/5 px-4 py-2 font-mono text-xs leading-relaxed"
              >
                {events.length === 0 && <div className="text-[var(--color-text-faint)]">waiting for events…</div>}
                {events.map((e) => (
                  <LogLine key={e.id} event={e} />
                ))}
              </div>
              {!autoScroll && (
                <button
                  type="button"
                  onClick={jumpToLatest}
                  className="absolute bottom-3 right-4 rounded-full bg-white/10 px-3 py-1 text-[10px] text-[var(--color-text-muted)] hover:bg-white/15"
                >
                  jump to latest ↓
                </button>
              )}
            </div>
          ) : (
            <div className="h-28 overflow-hidden border-t border-white/5 px-4 py-2 font-mono text-xs leading-relaxed">
              {peekEvents.length === 0 && <div className="text-[var(--color-text-faint)]">waiting for events…</div>}
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
