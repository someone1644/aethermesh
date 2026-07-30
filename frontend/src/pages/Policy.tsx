import DecisionPanel from '../components/sidebar/DecisionPanel'

export default function Policy() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Policy</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Runtime policies AetherMesh evaluates during execution. These are design placeholders —
          policy logic is not yet wired to live decisions in this prototype.
        </p>
      </div>
      <DecisionPanel />
    </div>
  )
}
