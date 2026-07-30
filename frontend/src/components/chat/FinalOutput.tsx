export default function FinalOutput({ output }: { output: string }) {
  if (!output) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--color-border)] p-4 text-sm text-[var(--color-text-muted)]">
        No final output yet — the run hasn't completed.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="mb-2 font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
        Final output
      </div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-text)]">{output}</p>
    </div>
  )
}
