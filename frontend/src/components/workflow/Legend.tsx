import type { NodeStatus } from '../../types/workflow'

const ITEMS: { status: NodeStatus; label: string; color: string }[] = [
  { status: 'pending', label: 'Pending', color: '#52525b' },
  { status: 'ready', label: 'Ready', color: '#71717a' },
  { status: 'active', label: 'Active', color: '#f59e0b' },
  { status: 'completed', label: 'Completed', color: '#34d399' },
  { status: 'failed', label: 'Failed', color: '#f87171' },
  { status: 'skipped', label: 'Skipped', color: '#52525b' },
]

export default function Legend() {
  return (
    <div className="flex flex-wrap gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-xs">
      {ITEMS.map((item) => (
        <div key={item.status} className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
          {item.label}
        </div>
      ))}
    </div>
  )
}
