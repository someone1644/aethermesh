export default function ReplayPanel({
  index,
  total,
  playing,
  onPlay,
  onPause,
  onRestart,
  onSeek,
}: {
  index: number
  total: number
  playing: boolean
  onPlay: () => void
  onPause: () => void
  onRestart: () => void
  onSeek: (i: number) => void
}) {
  return (
    <div className="space-y-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onRestart}
          className="rounded-md border border-[var(--color-border)] px-2.5 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]"
        >
          ⏮
        </button>
        <button
          type="button"
          onClick={playing ? onPause : onPlay}
          className="flex-1 rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
        >
          {playing ? 'Pause' : 'Play'}
        </button>
        <span className="font-mono text-xs text-[var(--color-text-muted)]">
          {Math.min(index + 1, total)} / {total}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(total - 1, 0)}
        value={index}
        onChange={(e) => onSeek(Number(e.target.value))}
        className="w-full accent-[var(--color-accent)]"
      />
    </div>
  )
}
