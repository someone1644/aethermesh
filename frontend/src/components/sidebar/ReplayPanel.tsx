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
    <div className="space-y-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 animate-fade-in-up">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onRestart}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-hover)] px-3 py-2 text-sm text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-glow)] hover:text-[var(--color-text)]"
        >
          ⏮
        </button>
        <button
          type="button"
          onClick={playing ? onPause : onPlay}
          className="flex-1 rounded-lg btn-primary px-4 py-2 text-sm font-medium"
        >
          {playing ? '⏸ Pause' : '▶ Play'}
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
        className="w-full accent-[var(--color-primary)]"
      />
    </div>
  )
}
