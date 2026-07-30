export default function About() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-xl font-semibold text-[var(--color-text)]">About</h1>
      <p className="text-sm text-[var(--color-text-muted)]">
        AetherMesh is an adaptive runtime that monitors multi-agent AI execution, detects
        failures, and safely adapts workflows while explaining every runtime decision through
        replayable audit logs.
      </p>
      <div>
        <h2 className="font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
          Team — Ctrl Alt Defeat
        </h2>
        <ul className="mt-2 space-y-1 text-sm text-[var(--color-text)]">
          <li>Advaith Suriyanarayanan</li>
          <li>K V Lokesh Kumar</li>
          <li>Viswa Danuskka</li>
          <li>Sinduja U V</li>
        </ul>
      </div>
    </div>
  )
}
