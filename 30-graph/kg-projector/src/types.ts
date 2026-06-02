/**
 * Record shapes matching 00-contracts/lexicons/com/etzhayyim/kg/{node,edge}.json.
 *
 * The record body is what would land in a PDS under collection com.etzhayyim.kg.node /
 * com.etzhayyim.kg.edge at rkey <rkey>. The `$type` field is set so consumers can
 * route on it without external schema lookup.
 */

export type Source =
  | "deps.toml"
  | "adr-frontmatter"
  | "lexicon-refs"
  | "module-manifest"
  | "manual";

export interface KgNodeRecord {
  $type: "com.etzhayyim.kg.node";
  nodeId: string;
  nodeType: string;
  label?: string;
  summary?: string;
  tags?: string[];
  source: Source;
  createdAt: string;
}

export interface KgEdgeRecord {
  $type: "com.etzhayyim.kg.edge";
  subject: string;
  predicate: string;
  object?: string;
  literal?: string;
  weight?: number;
  context?: string;
  createdAt: string;
}

export type KgRecord = KgNodeRecord | KgEdgeRecord;

export interface KgProjection {
  nodes: KgNodeRecord[];
  edges: KgEdgeRecord[];
}

export function emptyProjection(): KgProjection {
  return { nodes: [], edges: [] };
}

export function mergeProjections(...parts: KgProjection[]): KgProjection {
  return {
    nodes: parts.flatMap((p) => p.nodes),
    edges: parts.flatMap((p) => p.edges),
  };
}
