import { Link } from 'react-router-dom'

const TAGLINE =
  'An adaptive runtime that monitors multi-agent AI execution, detects failures, and safely adapts workflows while explaining every runtime decision through replayable audit logs.'

export default function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 py-16 text-center">
      <img
        src="https://placehold.co/1200x600?text=AetherMesh"
        alt="AetherMesh"
        className="w-full max-w-3xl rounded-xl border border-[var(--color-border)]"
      />
      <div className="max-w-xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight text-[var(--color-text)]">AetherMesh</h1>
        <p className="text-[var(--color-text-muted)]">{TAGLINE}</p>
      </div>
      <Link
        to="/prompt"
        className="rounded-md bg-[var(--color-primary)] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
      >
        New task
      </Link>
    </div>
  )
}
