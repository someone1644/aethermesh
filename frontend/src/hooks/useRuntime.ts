import { useMemo } from 'react'
import { useRuntimeStore } from '../store/runtimeStore'
import type { RuntimeEvent } from '../types/event'
import type { DecisionAction, RuntimeDecision } from '../types/runtime'

export function derivePolicyDecisions(events: RuntimeEvent[]): RuntimeDecision[] {
  const decisions: RuntimeDecision[] = []

  events.forEach((event, i) => {
    if (event.event_type !== 'policy_triggered') return
    const next = events[i + 1]

    let action: DecisionAction = 'none'
    let target_node: string | null = null
    let new_node: string | null = null

    if (next?.event_type === 'node_replaced') {
      action = 'replace'
      target_node = (next.details.old_node as string) ?? null
      new_node = (next.details.new_node as string) ?? null
    } else if (next?.event_type === 'node_added') {
      action = 'add'
      new_node = (next.details.node_id as string) ?? null
    } else if (next?.event_type === 'node_removed') {
      action = 'remove'
      target_node = (next.details.node_id as string) ?? null
    }

    decisions.push({
      action,
      target_node,
      new_node,
      reason: event.reason,
      policy_name: (event.details.policy as string) ?? 'unknown_policy',
      priority: 0,
      metadata: event.details,
    })
  })

  return decisions
}

export function useRuntime() {
  const executionState = useRuntimeStore((s) => s.executionState)
  const isLive = useRuntimeStore((s) => s.isLive)
  const policyDecisions = useMemo(
    () => derivePolicyDecisions(executionState.events),
    [executionState.events],
  )

  return { executionState, isLive, policyDecisions }
}
