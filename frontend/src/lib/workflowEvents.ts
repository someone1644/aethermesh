import type { Workflow, WorkflowNode } from '../types/workflow'
import type { RuntimeEvent } from '../types/event'

const AGENT_SEQUENCE: { id: string; name: string; agentType: string }[] = [
  { id: 'planner-1', name: 'Planner', agentType: 'planner' },
  { id: 'researcher-1', name: 'Researcher', agentType: 'researcher' },
  { id: 'coder-1', name: 'Coder', agentType: 'coder' },
  { id: 'reviewer-1', name: 'Reviewer', agentType: 'reviewer' },
  { id: 'evaluator-1', name: 'Evaluator', agentType: 'evaluator' },
]

function makeNode(
  id: string,
  name: string,
  agent_type: string,
  status: WorkflowNode['status'] = 'pending',
  metadata: Record<string, unknown> = {},
): WorkflowNode {
  return { id, name, agent_type, status, metadata }
}

/** Nodes a `node_replaced` event may introduce that aren't in the original sequence. */
const REPLACEMENT_NODE_POOL: WorkflowNode[] = [
  makeNode('researcher-2', 'Researcher (retry)', 'researcher', 'pending', { retried_from: 'researcher-1' }),
]

export const initialWorkflow: Workflow = {
  nodes: AGENT_SEQUENCE.map((a) => makeNode(a.id, a.name, a.agentType)),
  edges: [
    { source: 'planner-1', target: 'researcher-1' },
    { source: 'researcher-1', target: 'coder-1' },
    { source: 'coder-1', target: 'reviewer-1' },
    { source: 'reviewer-1', target: 'evaluator-1' },
  ],
  current_node: null,
  history: [],
}

/** Folds a single runtime event into a workflow snapshot. Single source of truth for both live and replayed runs. */
export function applyEventToWorkflow(workflow: Workflow, event: RuntimeEvent): Workflow {
  switch (event.event_type) {
    case 'agent_started': {
      const id = event.details.node_id as string
      return {
        ...workflow,
        current_node: id,
        nodes: workflow.nodes.map((n) => (n.id === id ? { ...n, status: 'active' } : n)),
      }
    }
    case 'agent_completed': {
      const id = event.details.node_id as string
      const failed = event.details.failed === true
      return {
        ...workflow,
        nodes: workflow.nodes.map((n) =>
          n.id === id ? { ...n, status: failed ? 'failed' : 'completed' } : n,
        ),
        history: workflow.history.includes(id) ? workflow.history : [...workflow.history, id],
      }
    }
    case 'node_replaced': {
      const oldId = event.details.old_node as string
      const newId = event.details.new_node as string
      const base = REPLACEMENT_NODE_POOL.find((n) => n.id === newId)
      if (!base) return workflow
      return {
        ...workflow,
        nodes: workflow.nodes.map((n) => (n.id === oldId ? { ...base, status: 'ready' } : n)),
        edges: workflow.edges.map((e) => ({
          source: e.source === oldId ? newId : e.source,
          target: e.target === oldId ? newId : e.target,
        })),
      }
    }
    case 'node_removed': {
      const id = event.details.node_id as string
      return {
        ...workflow,
        nodes: workflow.nodes.filter((n) => n.id !== id),
        edges: workflow.edges.filter((e) => e.source !== id && e.target !== id),
      }
    }
    default:
      return workflow
  }
}

export function foldEvents(events: RuntimeEvent[]): Workflow {
  return events.reduce(applyEventToWorkflow, initialWorkflow)
}

export function reconstructUpTo(events: RuntimeEvent[], uptoIndex: number): Workflow {
  return foldEvents(events.slice(0, uptoIndex + 1))
}
