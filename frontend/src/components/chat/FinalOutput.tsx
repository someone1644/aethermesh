import { useEffect, useRef, useState } from 'react'

const TYPEWRITER_SPEED_MS = 12

/** Reveals `text` one character at a time as it changes, instead of popping in whole. Resumes from where it left off if `text` is extended, restarts if it's replaced. */
function useTypewriter(text: string, speedMs: number): string {
  const [displayed, setDisplayed] = useState('')
  const indexRef = useRef(0)
  const prevTextRef = useRef('')

  useEffect(() => {
    if (text === prevTextRef.current) return

    if (!text || !text.startsWith(prevTextRef.current)) {
      indexRef.current = 0
      setDisplayed('')
    }
    prevTextRef.current = text

    if (!text) return

    const id = setInterval(() => {
      indexRef.current += 1
      setDisplayed(text.slice(0, indexRef.current))
      if (indexRef.current >= text.length) {
        clearInterval(id)
      }
    }, speedMs)

    return () => clearInterval(id)
  }, [text, speedMs])

  return displayed
}

export default function FinalOutput({ output }: { output: string }) {
  const typed = useTypewriter(output, TYPEWRITER_SPEED_MS)

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="mb-2 font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
        Result
      </div>
      {output ? (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-text)]">
          {typed}
          {typed.length < output.length && <span className="animate-pulse">▍</span>}
        </p>
      ) : (
        <p className="text-sm text-[var(--color-text-muted)]">Waiting for the run to complete…</p>
      )}
    </div>
  )
}
