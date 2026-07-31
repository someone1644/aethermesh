import type { RuntimeEvent } from '../../types/event'

function lastPolicyName(events: RuntimeEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].event_type === 'policy_triggered') {
      return (events[i].details.policy as string) ?? 'unknown_policy'
    }
  }
  return null
}

/** Live indicator of the most recent policy_triggered event, driven by the same event stream as the rest of the Run page. */
export default function PolicyTriggerChip({ events }: { events: RuntimeEvent[] }) {
  const policyName = lastPolicyName(events)

  return (
    <div>
      <div className="mb-1.5 font-mono text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
        Triggered by
      </div>
      {policyName ? (
        <div className="flex items-center gap-2 rounded-md border border-[#D97706] bg-[#FEF3E2] px-3 py-2 font-mono text-xs font-semibold text-[#92400E]">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#D97706] node-pulse" />
          {policyName}
        </div>
      ) : (
        <div className="flex items-center gap-2 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-xs text-[var(--color-text-muted)]">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-text-muted)]" />
          No policy triggered yet
        </div>
      )}
    </div>
  )
}
