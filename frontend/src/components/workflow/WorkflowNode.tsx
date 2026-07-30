import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { NodeStatus } from '../../types/workflow'

export interface WorkflowNodeData {
  [key: string]: unknown
  label: string
  agentType: string
  status: NodeStatus
}

const STATUS_STYLES: Record<NodeStatus, string> = {
  pending: 'border-[var(--color-status-pending)] text-[var(--color-status-pending)]',
  ready: 'border-[var(--color-status-ready)] text-[var(--color-status-ready)]',
  active: 'border-[var(--color-status-active)] text-[var(--color-status-active)] animate-pulse-active',
  completed: 'border-[var(--color-status-completed)] text-[var(--color-status-completed)]',
  failed: 'border-[var(--color-status-failed)] text-[var(--color-status-failed)]',
  skipped: 'border-[var(--color-status-skipped)] text-[var(--color-status-skipped)] opacity-60',
}

export default function WorkflowNode({ data }: NodeProps & { data: WorkflowNodeData }) {
  return (
    <div
      className={`min-w-[160px] rounded-lg border-2 bg-[var(--color-surface)] px-4 py-3 shadow-lg ${STATUS_STYLES[data.status]}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-[var(--color-border)]" />
      <div className="font-mono text-xs uppercase tracking-wide opacity-70">{data.agentType}</div>
      <div className="mt-0.5 text-sm font-medium text-[var(--color-text)]">{data.label}</div>
      <div className="mt-1 font-mono text-[10px] uppercase tracking-wider">{data.status}</div>
      <Handle type="source" position={Position.Right} className="!bg-[var(--color-border)]" />
    </div>
  )
}
