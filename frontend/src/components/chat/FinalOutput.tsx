export default function FinalOutput({ output }: { output: string }) {
  if (!output) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--color-border)] p-5 text-sm text-[var(--color-text-muted)] animate-fade-in">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[var(--color-text-faint)] animate-pulse" />
          No final output yet — the run hasn't completed.
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 animate-fade-in-up glow-emerald">
      <div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-[var(--color-accent-emerald)]">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
        Final output
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-text)]">{output}</p>
    </div>
  )
}
