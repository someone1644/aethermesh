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

/**
 * Static policy design cards. Backend policy implementations are stubs today, so this
 * intentionally doesn't wire up live RuntimeDecision data — `decisions` is accepted only
 * for backward compatibility with older call sites and is currently unused.
 */
export default function DecisionPanel(_props: { decisions?: RuntimeDecision[] } = {}) {
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
