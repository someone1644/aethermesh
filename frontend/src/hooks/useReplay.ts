import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { RuntimeEvent } from '../types/event'
import type { Workflow } from '../types/workflow'
import { reconstructUpTo } from '../lib/workflowEvents'

export function useReplay(events: RuntimeEvent[], baseWorkflow?: Workflow) {
  const [index, setIndex] = useState(Math.max(events.length - 1, 0))
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!playing) return undefined
    timerRef.current = setInterval(() => {
      setIndex((i) => {
        if (i + 1 >= events.length) {
          setPlaying(false)
          return i
        }
        return i + 1
      })
    }, 800)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [playing, events.length])

  const play = useCallback(() => setPlaying(true), [])
  const pause = useCallback(() => setPlaying(false), [])
  const restart = useCallback(() => {
    setIndex(0)
    setPlaying(false)
  }, [])
  const seek = useCallback(
    (i: number) => setIndex(Math.max(0, Math.min(i, events.length - 1))),
    [events.length],
  )

  const workflowAtIndex = useMemo(
    () => reconstructUpTo(events, index, baseWorkflow),
    [events, index, baseWorkflow],
  )
  const visibleEvents = useMemo(() => events.slice(0, index + 1), [events, index])

  return {
    index,
    playing,
    play,
    pause,
    restart,
    seek,
    workflowAtIndex,
    visibleEvents,
    total: events.length,
  }
}
