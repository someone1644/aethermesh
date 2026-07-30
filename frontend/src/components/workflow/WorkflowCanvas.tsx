import { useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { Workflow } from '../../types/workflow'
import { edgeId } from '../../types/workflow'
import WorkflowNode, { type WorkflowNodeData } from './WorkflowNode'
import WorkflowEdge from './WorkflowEdge'

const nodeTypes = { workflowNode: WorkflowNode }
const edgeTypes = { workflowEdge: WorkflowEdge }

function layout(workflow: Workflow): { nodes: Node<WorkflowNodeData>[]; edges: Edge[] } {
  const nodes: Node<WorkflowNodeData>[] = workflow.nodes.map((n, i) => ({
    id: n.id,
    type: 'workflowNode',
    position: { x: i * 220, y: (i % 2) * 90 },
    data: { label: n.name, agentType: n.agent_type, status: n.status },
  }))

  const edges: Edge[] = workflow.edges.map((e) => ({
    id: edgeId(e),
    source: e.source,
    target: e.target,
    type: 'workflowEdge',
    data: { active: workflow.current_node === e.target },
  }))

  return { nodes, edges }
}

export default function WorkflowCanvas({ workflow, className }: { workflow: Workflow; className?: string }) {
  const { nodes, edges } = useMemo(() => layout(workflow), [workflow])

  return (
    <div className={className ?? 'h-full w-full'}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} color="var(--color-border)" gap={20} />
        <Controls showInteractive={false} />
        <MiniMap
          pannable
          zoomable
          nodeColor="var(--color-accent)"
          maskColor="rgba(10,10,15,0.6)"
          style={{ backgroundColor: 'var(--color-surface)' }}
        />
      </ReactFlow>
    </div>
  )
}
