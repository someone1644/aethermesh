import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { NodeStatus } from '../../types/workflow'

export interface WorkflowNodeData {
  [key: string]: unknown
  label: string
  agentType: string
  status: NodeStatus
}

const STATUS_COLORS: Record<NodeStatus, { border: string; text: string; glow: string }> = {
  pending: { border: '#27272a', text: '#52525b', glow: 'none' },
  ready: { border: '#3f3f46', text: '#71717a', glow: 'none' },
  active: { border: '#f59e0b', text: '#fbbf24', glow: '0 0 16px rgba(245, 158, 11, 0.2)' },
  completed: { border: '#34d399', text: '#34d399', glow: '0 0 12px rgba(52, 211, 153, 0.12)' },
  failed: { border: '#f87171', text: '#f87171', glow: '0 0 12px rgba(248, 113, 113, 0.12)' },
  skipped: { border: '#27272a', text: '#52525b', glow: 'none' },
}

export default function WorkflowNode({ data }: NodeProps & { data: WorkflowNodeData }) {
  const colors = STATUS_COLORS[data.status]
  return (
    <div
      className={`min-w-[160px] rounded-xl border-2 bg-[var(--color-surface)] px-4 py-3 ${data.status === 'active' ? 'node-pulse' : ''}`}
      style={{ borderColor: colors.border, boxShadow: colors.glow }}
    >
      <Handle type="target" position={Position.Left} className="!bg-[var(--color-border)]" />
      <div className="font-mono text-[10px] uppercase tracking-widest" style={{ color: colors.text }}>
        {data.agentType}
      </div>
      <div className="mt-0.5 text-sm font-medium text-[var(--color-text)]">{data.label}</div>
      <div className="mt-1 font-mono text-[10px] uppercase tracking-wider" style={{ color: colors.text }}>
        {data.status}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-[var(--color-border)]" />
    </div>
  )
}
