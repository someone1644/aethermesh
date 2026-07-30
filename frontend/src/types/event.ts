export type EventType =
  | 'workflow_started'
  | 'agent_started'
  | 'agent_completed'
  | 'node_added'
  | 'node_removed'
  | 'node_replaced'
  | 'policy_triggered'
  | 'workflow_completed'

export interface RuntimeEvent {
  id: string
  timestamp: string
  event_type: EventType
  reason: string
  details: Record<string, unknown>
}
