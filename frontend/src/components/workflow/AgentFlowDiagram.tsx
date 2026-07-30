import type { NodeStatus, WorkflowNode } from '../../types/workflow'

const STATUS_STYLES: Record<
  NodeStatus,
  { bg: string; border: string; text: string; pulse?: boolean; dashed?: boolean }
> = {
  pending: { bg: '#F3F4F6', border: '#D1D5DB', text: '#6B7280' },
  ready: { bg: '#F3F4F6', border: '#9CA3AF', text: '#4B5563' },
  active: { bg: '#FEF3E2', border: '#D97706', text: '#B45309', pulse: true },
  completed: { bg: '#E7F6EC', border: '#1E8E3E', text: '#166534' },
  failed: { bg: '#FDECEA', border: '#D93025', text: '#B91C1C' },
  skipped: { bg: '#F3F4F6', border: '#D1D5DB', text: '#9CA3AF', dashed: true },
}

function AgentNode({ node }: { node: WorkflowNode }) {
  const style = STATUS_STYLES[node.status]
  return (
    <div
      className={`flex h-[90px] w-[180px] shrink-0 flex-col justify-center gap-1 rounded-xl border bg-white px-3.5 py-3 text-left shadow-sm ${style.pulse ? 'node-pulse' : ''}`}
      style={{ borderColor: style.border, borderStyle: style.dashed ? 'dashed' : 'solid' }}
    >
      <span
        className="inline-flex w-fit items-center rounded-full px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide"
        style={{ backgroundColor: style.bg, color: style.text }}
      >
        Agent
      </span>
      <div className="truncate text-sm font-semibold text-[var(--color-text)]">{node.name}</div>
      <div className="truncate font-mono text-[10px] uppercase tracking-wider" style={{ color: style.text }}>
        {node.status}
      </div>
    </div>
  )
}

function Connector({ active }: { active: boolean }) {
  const color = active ? '#D97706' : '#E5E5E5'
  return (
    <div className="relative flex min-w-[40px] flex-1 items-center px-1">
      <svg width="100%" height="4" preserveAspectRatio="none" className="block">
        <line
          x1="0"
          y1="2"
          x2="100%"
          y2="2"
          stroke={color}
          strokeWidth={active ? 2 : 1.5}
          strokeDasharray={active ? '6 4' : undefined}
          className={active ? 'connector-flow' : undefined}
        />
      </svg>
      <span
        className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 bg-white"
        style={{ borderColor: color }}
      />
    </div>
  )
}

export default function AgentFlowDiagram({
  nodes,
  mutationNote,
}: {
  nodes: WorkflowNode[]
  mutationNote?: string
}) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
      <div className="flex items-center overflow-x-auto">
        {nodes.map((node, i) => (
          <div key={node.id} className="flex items-center">
            <AgentNode node={node} />
            {i < nodes.length - 1 && <Connector active={nodes[i + 1]?.status === 'active'} />}
          </div>
        ))}
      </div>
      {mutationNote && <p className="mt-4 font-mono text-xs text-[#B45309]">{mutationNote}</p>}
    </div>
  )
}
