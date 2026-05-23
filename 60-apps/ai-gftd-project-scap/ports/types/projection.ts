import type { SecurityEvent, GraphNode, GraphEdge } from "@/types/security-graph"

export function projectToGraph(events: SecurityEvent[]): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const nodeIds = new Set<string>()

  for (const event of events) {
    switch (event.type) {
      case "RESOURCE_CREATED": {
        const { id, type, label } = event.payload
        if (!nodeIds.has(id)) {
          nodes.push({ id, type, label })
          nodeIds.add(id)
        }
        break
      }
      case "POLICY_ATTACHED": {
        const { source, target, policy } = event.payload
        if (nodeIds.has(source) && nodeIds.has(target)) {
          edges.push({ source, target, label: policy })
        }
        break
      }
      case "VULNERABILITY_FOUND": {
        const { resourceId, vulnerabilityId, description } = event.payload
        if (!nodeIds.has(vulnerabilityId)) {
          nodes.push({ id: vulnerabilityId, type: "VULNERABILITY", label: description, hasWarning: true })
          nodeIds.add(vulnerabilityId)
        }
        if (nodeIds.has(resourceId)) {
          edges.push({ source: resourceId, target: vulnerabilityId })
          const resourceNode = nodes.find((n) => n.id === resourceId)
          if (resourceNode) {
            resourceNode.hasWarning = true
          }
        }
        break
      }
      case "CONNECTION_ESTABLISHED": {
        const { source, target, port } = event.payload
        if (nodeIds.has(source) && nodeIds.has(target)) {
          edges.push({ source, target, label: `Port ${port}` })
        }
        break
      }
    }
  }

  return { nodes, edges }
}
