import { API_BASE, USE_MOCKS } from './runtime'
import { mockEventStream } from '../mocks/executionState'
import type { RuntimeEvent } from '../types/event'

/**
 * Streams runtime events one at a time. In mock mode this replays the fixture
 * on an interval so the Timeline/Logs/Mutation Feed feel live; the real
 * implementation subscribes to the backend's SSE endpoint instead.
 */
export function subscribeToEvents(
  onEvent: (event: RuntimeEvent) => void,
  intervalMs = 1200,
): () => void {
  if (USE_MOCKS) {
    let i = 0
    const timer = setInterval(() => {
      if (i >= mockEventStream.length) {
        clearInterval(timer)
        return
      }
      onEvent(mockEventStream[i])
      i += 1
    }, intervalMs)
    return () => clearInterval(timer)
  }

  const source = new EventSource(`${API_BASE}/events/stream`)
  source.onmessage = (msg) => onEvent(JSON.parse(msg.data))
  return () => source.close()
}
