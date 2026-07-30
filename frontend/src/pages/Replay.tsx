import { useRuntime } from '../hooks/useRuntime'
import { useReplay } from '../hooks/useReplay'
import ReplayPanel from '../components/sidebar/ReplayPanel'
import EventLog from '../components/sidebar/EventLog'
import WorkflowCanvas from '../components/workflow/WorkflowCanvas'

export default function Replay() {
  const { executionState } = useRuntime()
  const replay = useReplay(executionState.events)

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <h1 className="font-mono text-sm uppercase tracking-wide text-[var(--color-text-muted)]">
        Replay
      </h1>

      <ReplayPanel
        index={replay.index}
        total={replay.total}
        playing={replay.playing}
        onPlay={replay.play}
        onPause={replay.pause}
        onRestart={replay.restart}
        onSeek={replay.seek}
      />

      <div className="h-72 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <WorkflowCanvas workflow={replay.workflowAtIndex} />
      </div>

      <div>
        <h2 className="mb-3 font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
          Events up to this point
        </h2>
        <EventLog events={replay.visibleEvents} />
      </div>
    </div>
  )
}
