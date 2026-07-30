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

const POLICIES: { key: string; name: string; description: string; Icon: () => ReactNode }[] = [
  {
    key: 'low_confidence',
    name: 'Low Confidence',
    description: 'Flags an agent result when its confidence score falls below the safe-execution threshold.',
    Icon: LowConfidenceIcon,
  },
  {
    key: 'contradiction',
    name: 'Contradiction',
    description: 'Detects conflicting evidence gathered across agents and halts execution before it compounds.',
    Icon: ContradictionIcon,
  },
  {
    key: 'missing_repo',
    name: 'Missing Repository',
    description: 'Flags when a referenced repository or resource cannot be located before agents act on it.',
    Icon: MissingRepoIcon,
  },
  {
    key: 'execution_timeout',
    name: 'Execution Timeout',
    description: 'Flags a workflow that has exceeded its allotted execution time and may be stuck.',
    Icon: TimeoutIcon,
  },
]

const ACTION_LABEL: Record<string, string> = {
  add: 'Added node',
  remove: 'Removed node',
  replace: 'Replaced node',
  none: 'No action',
}

function LiveDecisions({ decisions }: { decisions: RuntimeDecision[] }) {
  return (
    <div className="space-y-3">
      {decisions.map((d, i) => (
        <div
          key={`${d.policy_name}-${i}`}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
        >
          <div className="flex items-center justify-between gap-2.5">
            <span className="font-mono text-sm font-medium text-[var(--color-text)]">{d.policy_name}</span>
            <span className="font-mono text-xs uppercase tracking-wide text-[var(--color-accent)]">
              {ACTION_LABEL[d.action] ?? d.action}
            </span>
          </div>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{d.reason}</p>
          {(d.target_node || d.new_node) && (
            <p className="mt-1 font-mono text-xs text-[var(--color-text-muted)]">
              {d.target_node ? `target: ${d.target_node}` : ''}
              {d.target_node && d.new_node ? ' · ' : ''}
              {d.new_node ? `new: ${d.new_node}` : ''}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

/** Reference cards describing each policy the backend's PolicyEngine evaluates. */
function PolicyReference() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {POLICIES.map(({ key, name, description, Icon }) => (
        <div
          key={key}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-[var(--color-surface-hover)] text-[var(--color-text)]">
              <Icon />
            </span>
            <span className="font-mono text-sm font-medium text-[var(--color-text)]">{name}</span>
          </div>
          <p className="mt-3 text-sm text-[var(--color-text-muted)]">{description}</p>
        </div>
      ))}
    </div>
  )
}

/**
 * Renders live RuntimeDecisions from the backend's PolicyEngine when a run has
 * produced any (derived from `policy_triggered`/`node_*` events). Falls back to
 * a static reference of the policies AetherMesh evaluates when none exist yet
 * (idle state, or a run that didn't trigger any policy).
 */
export default function DecisionPanel({ decisions }: { decisions?: RuntimeDecision[] } = {}) {
  if (decisions && decisions.length > 0) {
    return <LiveDecisions decisions={decisions} />
  }
  return <PolicyReference />
}
