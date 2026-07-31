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
  animated,
}: EdgeProps & { data?: { active?: boolean } }) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const isActive = data?.active || animated

  return (
    <BaseEdge
      path={edgePath}
      markerEnd={markerEnd}
      style={{
        stroke: isActive ? '#F59E0B' : 'var(--color-border)',
        strokeWidth: isActive ? 2.5 : 1.5,
        strokeDasharray: isActive ? '6 4' : undefined,
        opacity: isActive ? 1 : 0.6,
      }}
      className={isActive ? 'connector-flow' : undefined}
    />
  )
}
