import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { NodeStatus } from '../../types/workflow'

export interface WorkflowNodeData {
  [key: string]: unknown
  label: string
  agentType: string
  status: NodeStatus
}

const ROLE_SUBTITLES: Record<string, string> = {
  planner: 'Plans execution workflow',
  researcher: 'Gathers context & sources',
  coder: 'Implements code fix',
  reviewer: 'Audits output quality',
  evaluator: 'Scores final confidence',
  debugger: 'Diagnoses root cause & hotfixes',
  security_auditor: 'Audits OWASP & secrets',
  optimizer: 'Profiles memory & speed',
  sandbox_runner: 'Verifies sandbox execution',
  analyst: 'Evaluates risks & trade-offs',
  summarizer: 'Synthesizes executive report',
}

const STATUS_BADGES: Record<NodeStatus, { text: string; bg: string; border: string; label: string }> = {
  pending: { text: '#9CA3AF', bg: '#1F2937', border: '#374151', label: 'Pending' },
  ready: { text: '#D1D5DB', bg: '#1F2937', border: '#4B5563', label: 'Ready' },
  active: { text: '#F59E0B', bg: '#451A03', border: '#D97706', label: 'Active' },
  completed: { text: '#10B981', bg: '#064E3B', border: '#059669', label: 'Completed' },
  failed: { text: '#EF4444', bg: '#451212', border: '#DC2626', label: 'Failed' },
  skipped: { text: '#6B7280', bg: '#111827', border: '#374151', label: 'Skipped' },
}

export default function WorkflowNode({ data }: NodeProps & { data: WorkflowNodeData }) {
  const badge = STATUS_BADGES[data.status] ?? STATUS_BADGES.pending
  const subtitle = ROLE_SUBTITLES[data.agentType] ?? data.agentType
  const isActive = data.status === 'active'

  return (
    <div
      className={`relative min-w-[210px] rounded-xl border bg-[var(--color-surface)] px-4 pb-4 pt-5 shadow-xl transition-all duration-300 ${
        isActive ? 'ring-2 ring-[#F59E0B] ring-offset-2 ring-offset-[#090D16] animate-pulse-glow' : ''
      }`}
      style={{ borderColor: badge.border }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-[var(--color-border)] !bg-[var(--color-surface)]"
      />
      
      {/* Floating Status Badge */}
      <span
        className="absolute -top-3 left-3 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider shadow-md"
        style={{ backgroundColor: badge.bg, borderColor: badge.border, color: badge.text }}
      >
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: badge.text }} />
        {badge.label}
      </span>

      <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
        {data.agentType}
      </div>
      <div className="mt-0.5 truncate text-sm font-bold text-[var(--color-text)]">
        {data.label}
      </div>
      <div className="mt-1 truncate text-xs text-[var(--color-text-muted)] opacity-80">
        {subtitle}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-[var(--color-border)] !bg-[var(--color-surface)]"
      />
    </div>
  )
}
