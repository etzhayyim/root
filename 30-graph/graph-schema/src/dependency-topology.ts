export interface DependencyTopologyNode {
  vertexId: string;
  displayName?: string | null;
  vertexKind?: string | null;
}

export interface DependencyTopologyEdge {
  edgeId?: string | null;
  dependentVid: string;
  prerequisiteVid: string;
}

export interface DependencyTopologyOrderRow {
  graph_scope: string;
  vertex_id: string;
  display_name?: string | null;
  vertex_kind?: string | null;
  topo_rank: number;
  reverse_topo_rank: number;
  topo_level: number;
  dependency_count: number;
  dependent_count: number;
  unresolved_dependency_count: number;
  cycle_status: "acyclic" | "cycle_member";
  computed_at: string;
  algorithm: "kahn-v1";
  payload_json: string;
}

export interface ComputeDependencyTopologyOptions {
  graphScope?: string;
  computedAt?: string;
}

/**
 * Computes stable topo and reverse-topo ranks for edges whose direction is:
 * dependentVid depends on prerequisiteVid.
 */
export function computeDependencyTopologyOrder(
  nodes: DependencyTopologyNode[],
  edges: DependencyTopologyEdge[],
  options: ComputeDependencyTopologyOptions = {},
): DependencyTopologyOrderRow[] {
  const graphScope = options.graphScope ?? "strategy";
  const computedAt = options.computedAt ?? new Date().toISOString();
  const explicitNodeIds = new Set(nodes.map((node) => node.vertexId));
  const nodeById = new Map<string, DependencyTopologyNode>();

  for (const node of nodes) nodeById.set(node.vertexId, node);
  for (const edge of edges) {
    if (!nodeById.has(edge.dependentVid)) nodeById.set(edge.dependentVid, { vertexId: edge.dependentVid });
    if (!nodeById.has(edge.prerequisiteVid)) nodeById.set(edge.prerequisiteVid, { vertexId: edge.prerequisiteVid });
  }

  const ids = [...nodeById.keys()].sort();
  const dependencyCount = new Map<string, number>();
  const dependentCount = new Map<string, number>();
  const unresolvedCount = new Map<string, number>();
  const indegree = new Map<string, number>();
  const dependentsByPrerequisite = new Map<string, string[]>();
  const topoLevel = new Map<string, number>();

  for (const id of ids) {
    dependencyCount.set(id, 0);
    dependentCount.set(id, 0);
    unresolvedCount.set(id, 0);
    indegree.set(id, 0);
    dependentsByPrerequisite.set(id, []);
    topoLevel.set(id, 0);
  }

  const seenEdges = new Set<string>();
  for (const edge of edges) {
    const key = `${edge.dependentVid}\u0000${edge.prerequisiteVid}`;
    if (seenEdges.has(key)) continue;
    seenEdges.add(key);

    dependencyCount.set(edge.dependentVid, (dependencyCount.get(edge.dependentVid) ?? 0) + 1);
    dependentCount.set(edge.prerequisiteVid, (dependentCount.get(edge.prerequisiteVid) ?? 0) + 1);

    if (!explicitNodeIds.has(edge.prerequisiteVid)) {
      unresolvedCount.set(edge.dependentVid, (unresolvedCount.get(edge.dependentVid) ?? 0) + 1);
    }

    dependentsByPrerequisite.get(edge.prerequisiteVid)?.push(edge.dependentVid);
    indegree.set(edge.dependentVid, (indegree.get(edge.dependentVid) ?? 0) + 1);
  }

  for (const dependents of dependentsByPrerequisite.values()) dependents.sort();

  const ready = ids.filter((id) => (indegree.get(id) ?? 0) === 0).sort();
  const topo: string[] = [];

  while (ready.length > 0) {
    const id = ready.shift()!;
    topo.push(id);

    for (const dependent of dependentsByPrerequisite.get(id) ?? []) {
      topoLevel.set(dependent, Math.max(topoLevel.get(dependent) ?? 0, (topoLevel.get(id) ?? 0) + 1));
      const next = (indegree.get(dependent) ?? 0) - 1;
      indegree.set(dependent, next);
      if (next === 0) {
        ready.push(dependent);
        ready.sort();
      }
    }
  }

  const topoSet = new Set(topo);
  const cycleMembers = ids.filter((id) => !topoSet.has(id)).sort();
  const ordered = [...topo, ...cycleMembers];
  const total = ordered.length;

  return ordered.map((id, topoRank) => {
    const node = nodeById.get(id);
    const cycleStatus: DependencyTopologyOrderRow["cycle_status"] = topoSet.has(id) ? "acyclic" : "cycle_member";
    const row = {
      graph_scope: graphScope,
      vertex_id: id,
      display_name: node?.displayName ?? null,
      vertex_kind: node?.vertexKind ?? null,
      topo_rank: topoRank,
      reverse_topo_rank: total - topoRank - 1,
      topo_level: topoLevel.get(id) ?? 0,
      dependency_count: dependencyCount.get(id) ?? 0,
      dependent_count: dependentCount.get(id) ?? 0,
      unresolved_dependency_count: unresolvedCount.get(id) ?? 0,
      cycle_status: cycleStatus,
      computed_at: computedAt,
      algorithm: "kahn-v1" as const,
    };

    return {
      ...row,
      payload_json: JSON.stringify({
        graphScope: row.graph_scope,
        vertexId: row.vertex_id,
        vertexKind: row.vertex_kind ?? "unknown",
        displayName: row.display_name ?? "",
        dependencyCount: row.dependency_count,
        dependentCount: row.dependent_count,
        topoRank: row.topo_rank,
        reverseTopoRank: row.reverse_topo_rank,
        topoLevel: row.topo_level,
        unresolvedDependencyCount: row.unresolved_dependency_count,
        cycleStatus: row.cycle_status,
      }),
    };
  });
}
