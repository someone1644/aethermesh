import type { ExecutionStatus } from '../../types/runtime'

const STYLES: Record<ExecutionStatus, { bg: string; text: string; dot: string; glow: string }> = {
  idle: { bg: 'rgba(82, 82, 91, 0.15)', text: '#71717a', dot: '#52525b', glow: '' },
  running: { bg: 'rgba(245, 158, 11, 0.12)', text: '#fbbf24', dot: '#f59e0b', glow: 'shadow-amber-500/20' },
  completed: { bg: 'rgba(52, 211, 153, 0.12)', text: '#34d399', dot: '#34d399', glow: 'shadow-emerald-500/20' },
  failed: { bg: 'rgba(248, 113, 113, 0.12)', text: '#f87171', dot: '#f87171', glow: 'shadow-red-500/20' },
}

export default function StatusBadge({ status }: { status: ExecutionStatus }) {
  const style = STYLES[status]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)] px-2.5 py-1 font-mono text-xs uppercase tracking-wide shadow-sm ${style.glow}`}
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
