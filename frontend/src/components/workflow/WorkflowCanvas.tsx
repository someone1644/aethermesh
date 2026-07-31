import { useMemo, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
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

/**
 * Calculates progressive real-time positions for visible nodes in a clean multi-column grid/tree topology.
 */
function computeProgressiveLayout(workflow: Workflow): { nodes: Node<WorkflowNodeData>[]; edges: Edge[] } {
  const allNodes = workflow.nodes
  if (allNodes.length === 0) {
    return { nodes: [], edges: [] }
  }

  // Progressive Node Visibility: Always start with Planner (index 0).
  // Child nodes progressively reveal as they transition to ready, active, completed, or failed.
  const visibleNodes = allNodes.filter(
    (n, i) => i === 0 || n.status !== 'pending' || workflow.current_node === n.id
  )

  // Group nodes into topological columns
  const nodes: Node<WorkflowNodeData>[] = visibleNodes.map((n, i) => {
    // Column x-offset: 260px per step
    const col = i
    // Row y-offset: stagger alternate nodes for visual tree balance
    const row = (i % 2) * 110

    return {
      id: n.id,
      type: 'workflowNode',
      position: { x: col * 260 + 50, y: row + 80 },
      data: {
        label: n.name,
        agentType: n.agent_type,
        status: n.status,
      },
    }
  })

  // Filter edges where both source and target are currently visible
  const visibleIds = new Set(visibleNodes.map((n) => n.id))
  const edges: Edge[] = workflow.edges
    .filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
    .map((e) => {
      const isTargetActive = workflow.current_node === e.target
      return {
        id: edgeId(e),
        source: e.source,
        target: e.target,
        type: 'workflowEdge',
        animated: isTargetActive,
        data: { active: isTargetActive },
      }
    })

  return { nodes, edges }
}

export default function WorkflowCanvas({ workflow, className }: { workflow: Workflow; className?: string }) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => computeProgressiveLayout(workflow),
    [workflow]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Sync state whenever the execution workflow state updates
  useEffect(() => {
    const { nodes: updatedNodes, edges: updatedEdges } = computeProgressiveLayout(workflow)
    
    // Preserve user-dragged node positions if node already exists
    setNodes((existingNodes) => {
      const existingPosMap = new Map(existingNodes.map((n) => [n.id, n.position]))
      return updatedNodes.map((newN) => {
        const existingPos = existingPosMap.get(newN.id)
        if (existingPos) {
          return { ...newN, position: existingPos }
        }
        return newN
      })
    })
    
    setEdges(updatedEdges)
  }, [workflow, setNodes, setEdges])

  return (
    <div className={className ?? 'h-full w-full'}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ maxZoom: 0.75, padding: 0.5 }}
        minZoom={0.2}
        maxZoom={1.2}
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} color="var(--color-border)" gap={24} size={1.5} />
        <Controls showInteractive={true} className="!bg-[var(--color-surface)] !border-[var(--color-border)] text-[var(--color-text)]" />
      </ReactFlow>
    </div>
  )
}
