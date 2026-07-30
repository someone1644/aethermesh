import type { NodeStatus, WorkflowNode } from '../../types/workflow'

const STATUS_STYLES: Record<
  NodeStatus,
  { border: string; text: string; bg: string; pulse?: boolean; dashed?: boolean }
> = {
  pending: { border: '#D1D5DB', text: '#6B7280', bg: '#F3F4F6' },
  ready: { border: '#9CA3AF', text: '#4B5563', bg: '#F3F4F6' },
  active: { border: '#D97706', text: '#B45309', bg: '#FEF3E2', pulse: true },
  completed: { border: '#1E8E3E', text: '#166534', bg: '#E7F6EC' },
  failed: { border: '#D93025', text: '#B91C1C', bg: '#FDECEA' },
  skipped: { border: '#D1D5DB', text: '#9CA3AF', bg: '#F3F4F6', dashed: true },
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
  debugger: 'Diagnoses root cause & hotfixes',
  security_auditor: 'Audits OWASP & secrets',
  optimizer: 'Profiles memory & performance',
  sandbox_runner: 'Verifies sandbox execution',
  analyst: 'Evaluates risks & trade-offs',
  summarizer: 'Synthesizes executive report',
}

function AgentNode({ node }: { node: WorkflowNode }) {
  const style = STATUS_STYLES[node.status]
  const role = ROLE_DESCRIPTIONS[node.agent_type] ?? node.agent_type
  return (
    <div
      className={`relative w-[210px] shrink-0 rounded-[10px] border bg-white px-4 pb-8 pt-6 text-left shadow-sm ${style.pulse ? 'node-pulse' : ''}`}
      style={{ borderColor: style.border, borderStyle: style.dashed ? 'dashed' : 'solid' }}
    >
      <span
        className="absolute -top-2.5 left-3 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium shadow-sm"
        style={{ backgroundColor: style.bg, borderColor: style.border, color: style.text }}
      >
        <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: style.text }} />
        {STATUS_LABEL[node.status]}
      </span>
      <div className="truncate text-sm font-semibold text-[var(--color-text)]">{node.name}</div>
      <div className="mt-0.5 truncate text-xs text-[var(--color-text-muted)]">{role}</div>
    </div>
  )
}

function Connector({ active }: { active: boolean }) {
  const color = active ? '#D97706' : '#D1D5DB'
  return (
    <div className="flex h-10 min-w-[36px] flex-1 items-center">
      <svg width="100%" height="40" viewBox="0 0 100 40" preserveAspectRatio="none" className="block overflow-visible">
        <path
          d="M0,20 C30,12 70,28 100,20"
          fill="none"
          stroke={color}
          strokeWidth={active ? 2 : 1.2}
          strokeOpacity={active ? 1 : 0.6}
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
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
      <div className="flex items-center overflow-x-auto pt-2.5">
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
