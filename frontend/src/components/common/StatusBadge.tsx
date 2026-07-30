import type { ExecutionStatus } from '../../types/runtime'

const STYLES: Record<ExecutionStatus, { bg: string; text: string; dot: string }> = {
  idle: { bg: '#F7F7F7', text: '#6B6B6B', dot: '#9CA3AF' },
  running: { bg: '#FEF3E2', text: '#92400E', dot: '#D97706' },
  completed: { bg: '#EAF7EE', text: '#14532D', dot: '#1E8E3E' },
  failed: { bg: '#FDECEA', text: '#7F1D1D', dot: '#D93025' },
  paused_for_approval: { bg: '#FEF3E2', text: '#92400E', dot: '#D97706' },
}

export default function StatusBadge({ status }: { status: ExecutionStatus }) {
  const style = STYLES[status]
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)] px-2.5 py-1 font-mono text-xs uppercase tracking-wide"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${status === 'running' ? 'node-pulse' : ''}`}
        style={{ backgroundColor: style.dot }}
      />
      {status}
    </span>
  )
}
