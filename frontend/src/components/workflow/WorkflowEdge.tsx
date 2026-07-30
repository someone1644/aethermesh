import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react'

export default function WorkflowEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}: EdgeProps & { data?: { active?: boolean } }) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  return (
    <BaseEdge
      path={edgePath}
      markerEnd={markerEnd}
      style={{
        stroke: data?.active ? 'var(--color-accent)' : 'var(--color-border)',
        strokeWidth: data?.active ? 2.5 : 1.5,
      }}
    />
  )
}
