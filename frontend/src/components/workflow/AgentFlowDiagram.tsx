import type { NodeStatus, WorkflowNode } from '../../types/workflow'

const STATUS_STYLES: Record<
  NodeStatus,
  { border: string; text: string; bg: string; glow?: string; pulse?: boolean; dashed?: boolean }
> = {
  pending: { border: '#27272a', text: '#52525b', bg: 'rgba(39, 39, 42, 0.3)' },
  ready: { border: '#3f3f46', text: '#71717a', bg: 'rgba(63, 63, 70, 0.3)' },
  active: { border: '#f59e0b', text: '#fbbf24', bg: 'rgba(245, 158, 11, 0.08)', glow: '0 0 20px rgba(245, 158, 11, 0.15)', pulse: true },
  completed: { border: '#34d399', text: '#34d399', bg: 'rgba(52, 211, 153, 0.08)', glow: '0 0 12px rgba(52, 211, 153, 0.1)' },
  failed: { border: '#f87171', text: '#f87171', bg: 'rgba(248, 113, 113, 0.08)', glow: '0 0 12px rgba(248, 113, 113, 0.1)' },
  skipped: { border: '#27272a', text: '#52525b', bg: 'rgba(39, 39, 42, 0.2)', dashed: true },
}

const STATUS_LABEL: Record<NodeStatus, string> = {
  pending: 'Pending',
  ready: 'Ready',
  active: 'Active',
  completed: 'Completed',
  failed: 'Failed',
  skipped: 'Skipped',
}

const ROLE_DESCRIPTIONS: Record<string, string> = {
  planner: 'Plans the execution workflow',
  researcher: 'Gathers supporting evidence',
  coder: 'Implements the fix',
  reviewer: 'Reviews the proposed change',
  evaluator: 'Scores final confidence',
}

function AgentNode({ node, index }: { node: WorkflowNode; index: number }) {
  const style = STATUS_STYLES[node.status]
  const role = ROLE_DESCRIPTIONS[node.agent_type] ?? node.agent_type
  return (
    <div
      className={`relative w-[210px] shrink-0 rounded-xl border px-4 pb-8 pt-6 text-left transition-all duration-300 animate-fade-in-up stagger-${index + 1} ${style.pulse ? 'node-pulse' : ''}`}
      style={{
        borderColor: style.border,
        borderStyle: style.dashed ? 'dashed' : 'solid',
        backgroundColor: style.bg,
        boxShadow: style.glow ?? 'none',
      }}
    >
      <span
        className="absolute -top-2.5 left-3 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium"
        style={{ backgroundColor: '#0a0a0f', borderColor: style.border, color: style.text }}
      >
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${style.pulse ? 'animate-pulse' : ''}`} style={{ backgroundColor: style.text }} />
        {STATUS_LABEL[node.status]}
      </span>
      <div className="truncate text-sm font-semibold text-[var(--color-text)]">{node.name}</div>
      <div className="mt-0.5 truncate text-xs text-[var(--color-text-muted)]">{role}</div>
    </div>
  )
}

function Connector({ active }: { active: boolean }) {
  const color = active ? '#f59e0b' : '#27272a'
  return (
    <div className="flex h-10 min-w-[36px] flex-1 items-center">
      <svg width="100%" height="40" viewBox="0 0 100 40" preserveAspectRatio="none" className="block overflow-visible">
        <path
          d="M0,20 C30,12 70,28 100,20"
          fill="none"
          stroke={color}
          strokeWidth={active ? 2 : 1}
          strokeOpacity={active ? 1 : 0.4}
          strokeDasharray={active ? '6 4' : undefined}
          vectorEffect="non-scaling-stroke"
          className={active ? 'connector-flow' : undefined}
        />
      </svg>
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
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
      <div className="flex items-center overflow-x-auto pt-2.5">
        {nodes.map((node, i) => (
          <div key={node.id} className="flex items-center">
            <AgentNode node={node} index={i} />
            {i < nodes.length - 1 && <Connector active={nodes[i + 1]?.status === 'active'} />}
          </div>
        ))}
      </div>
      {mutationNote && (
        <p className="mt-4 flex items-center gap-2 font-mono text-xs text-[#fbbf24]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#fbbf24] animate-pulse" />
          {mutationNote}
        </p>
      )}
    </div>
  )
}
