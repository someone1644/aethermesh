import type { ReactNode } from 'react'
import type { RuntimeDecision } from '../../types/runtime'

function IconShell({ children }: { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

const LowConfidenceIcon = () => (
  <IconShell>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5" />
    <circle cx="12" cy="16" r="0.9" fill="currentColor" stroke="none" />
  </IconShell>
)

const ContradictionIcon = () => (
  <IconShell>
    <path d="M8 3 4 7l4 4" />
    <path d="M4 7h11a5 5 0 0 1 5 5v1" />
    <path d="M16 21l4-4-4-4" />
    <path d="M20 17H9a5 5 0 0 1-5-5v-1" />
  </IconShell>
)

const MissingRepoIcon = () => (
  <IconShell>
    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <path d="M9.5 12.5l5 5M14.5 12.5l-5 5" />
  </IconShell>
)

const TimeoutIcon = () => (
  <IconShell>
    <circle cx="12" cy="13" r="8" />
    <path d="M12 9v4l3 2" />
    <path d="M9 2h6" />
  </IconShell>
)

const LowSourcesIcon = () => (
  <IconShell>
    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
    <path d="M9 10h6" />
  </IconShell>
)

const POLICIES: { key: string; name: string; description: string; Icon: () => ReactNode; color: string }[] = [
  {
    key: 'low_confidence',
    name: 'Low Confidence',
    description: 'Flags an agent result when its confidence score falls below the safe-execution threshold.',
    Icon: LowConfidenceIcon,
    color: '#fbbf24',
  },
  {
    key: 'contradiction',
    name: 'Contradiction',
    description: 'Detects conflicting evidence gathered across agents and halts execution before it compounds.',
    Icon: ContradictionIcon,
    color: '#f87171',
  },
  {
    key: 'missing_repo',
    name: 'Missing Repository',
    description: 'Flags when a referenced repository or resource cannot be located before agents act on it.',
    Icon: MissingRepoIcon,
    color: '#6366f1',
  },
  {
    key: 'execution_timeout',
    name: 'Execution Timeout',
    description: 'Flags a workflow that has exceeded its allotted execution time and may be stuck.',
    Icon: TimeoutIcon,
    color: '#f97316',
  },
  {
    key: 'low_sources',
    name: 'Low Sources',
    description: 'Adds additional research when too few sources are found to support confident execution.',
    Icon: LowSourcesIcon,
    color: '#22d3ee',
  },
]

const ACTION_LABEL: Record<string, { text: string; color: string }> = {
  add: { text: 'Added node', color: '#34d399' },
  remove: { text: 'Removed node', color: '#f87171' },
  replace: { text: 'Replaced node', color: '#fbbf24' },
  none: { text: 'No action', color: '#71717a' },
}

function LiveDecisions({ decisions }: { decisions: RuntimeDecision[] }) {
  return (
    <div className="space-y-3">
      {decisions.map((d, i) => {
        const action = ACTION_LABEL[d.action] ?? ACTION_LABEL.none
        return (
          <div
            key={`${d.policy_name}-${i}`}
            className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 card-hover animate-fade-in-up stagger-${i + 1}`}
          >
            <div className="flex items-center justify-between gap-2.5">
              <span className="font-mono text-sm font-medium text-[var(--color-text)]">{d.policy_name}</span>
              <span
                className="rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide"
                style={{ color: action.color, backgroundColor: `${action.color}15` }}
              >
                {action.text}
              </span>
            </div>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">{d.reason}</p>
            {(d.target_node || d.new_node) && (
              <p className="mt-2 font-mono text-[11px] text-[var(--color-text-faint)]">
                {d.target_node ? `target: ${d.target_node}` : ''}
                {d.target_node && d.new_node ? ' → ' : ''}
                {d.new_node ? `new: ${d.new_node}` : ''}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}

/** Reference cards describing each policy the backend's PolicyEngine evaluates. */
function PolicyReference() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {POLICIES.map(({ key, name, description, Icon, color }, i) => (
        <div
          key={key}
          className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 card-hover animate-fade-in-up stagger-${i + 1}`}
        >
          <div className="flex items-center gap-3">
            <span
              className="flex h-9 w-9 items-center justify-center rounded-lg"
              style={{ backgroundColor: `${color}15`, color }}
            >
              <Icon />
            </span>
            <span className="font-mono text-sm font-medium text-[var(--color-text)]">{name}</span>
          </div>
          <p className="mt-3 text-[13px] leading-relaxed text-[var(--color-text-muted)]">{description}</p>
        </div>
      ))}
    </div>
  )
}

export default function DecisionPanel({ decisions }: { decisions?: RuntimeDecision[] } = {}) {
  if (decisions && decisions.length > 0) {
    return <LiveDecisions decisions={decisions} />
  }
  return <PolicyReference />
}
