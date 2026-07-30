export type NodeStatus =
  | 'pending'
  | 'ready'
  | 'active'
  | 'completed'
  | 'failed'
  | 'skipped'

export interface WorkflowNode {
  id: string
  name: string
  agent_type: string
  status: NodeStatus
  metadata: Record<string, unknown>
}

export interface WorkflowEdge {
  source: string
  target: string
}

export interface Workflow {
  id?: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  current_node: string | null
  history: string[]
}

export const edgeId = (edge: WorkflowEdge): string => `${edge.source}->${edge.target}`
