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
    <>
      {/* Docked bar — always mounted, even while expanded, so it keeps
          reserving its own layout space. That keeps the parent diagram
          wrapper's height constant, which the expanded overlay below
          depends on to inset its bottom edge correctly. */}
      <div className="overflow-hidden rounded-t-lg border border-b-0 border-[var(--color-border)] bg-[#111214] text-gray-100">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-2 font-mono text-xs uppercase tracking-wide text-gray-300 hover:bg-white/5"
        >
          <span>event log · {events.length}</span>
          <span aria-hidden="true">⌃</span>
        </button>
        <div className="h-28 overflow-hidden border-t border-white/10 px-4 py-2 font-mono text-xs leading-relaxed">
          {peekEvents.length === 0 && <div className="text-gray-500">waiting for events…</div>}
          {peekEvents.map((e) => (
            <LogLine key={e.id} event={e} />
          ))}
        </div>
      </div>

      {/* Expanded overlay — absolutely positioned against the diagram
          wrapper (the nearest `relative` ancestor, set up in Run.tsx),
          covering it completely. Bottom is inset 16px to match the docked
          bar's own bottom margin instead of sitting flush against the
          container edge. */}
      {expanded && (
        <div className="absolute inset-x-0 top-0 bottom-4 z-20 flex flex-col overflow-hidden rounded-t-lg border border-b-0 border-[var(--color-border)] bg-[#111214] text-gray-100">
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="flex w-full shrink-0 items-center justify-between px-4 py-2 font-mono text-xs uppercase tracking-wide text-gray-300 hover:bg-white/5"
          >
            <span>event log · {events.length}</span>
            <span aria-hidden="true">⌄</span>
          </button>
          <div className="relative min-h-0 flex-1">
            <div
              ref={scrollRef}
              onScroll={handleScroll}
              className="h-full overflow-y-auto border-t border-white/10 px-4 py-2 font-mono text-xs leading-relaxed"
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
        </div>
      )}
    </>
  )
}
