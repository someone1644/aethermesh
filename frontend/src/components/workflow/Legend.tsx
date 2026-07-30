import type { NodeStatus } from '../../types/workflow'

const ITEMS: { status: NodeStatus; label: string; color: string }[] = [
  { status: 'pending', label: 'Pending', color: 'var(--color-status-pending)' },
  { status: 'ready', label: 'Ready', color: 'var(--color-status-ready)' },
  { status: 'active', label: 'Active', color: 'var(--color-status-active)' },
  { status: 'completed', label: 'Completed', color: 'var(--color-status-completed)' },
  { status: 'failed', label: 'Failed', color: 'var(--color-status-failed)' },
  { status: 'skipped', label: 'Skipped', color: 'var(--color-status-skipped)' },
]

export default function Legend() {
  return (
    <div className="flex flex-wrap gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-xs">
      {ITEMS.map((item) => (
        <div key={item.status} className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
          <span className="h-2 w-2 rounded-full border-2" style={{ borderColor: item.color }} />
          {item.label}
        </div>
      ))}
    </div>
  )
}
