// cypher-kv.ts — Workers KV-backed Cypher engine (P64, 2026-05-12).
//
// Until the lg-yatabase pod ships com.etzhayyim.apps.yata.runCypher, this
// module serves simple `CREATE` and `MATCH` queries against the
// YATABASE_AUTH_CACHE KV namespace. Per-org node store with label index.
//
// Supported patterns (intentionally narrow — production graph queries
// will land via the pod when its handler exists):
//
//   CREATE (n:Label {prop:"val", ...}) RETURN n
//   MATCH (n:Label) RETURN n [LIMIT N]
//   MATCH (n:Label) RETURN n.prop [LIMIT N]
//
// Anything else returns `null` and the caller falls through to the
// dispatcher proxy (which currently 404s for runCypher — same as
// before).

export type KvCypherEnv = {
  YATABASE_AUTH_CACHE?: KVNamespace;
};

export type CypherKvResult = {
  columns: string[];
  data: Array<{ row: unknown[]; meta: Array<null> }>;
  // P97: mutation events to dispatch via webhooks. Caller iterates and
  // wraps each in waitUntil for fire-and-forget delivery.
  mutations?: Array<{ event: WebhookEventName; payload: Record<string, unknown> }>;
};

type WebhookEventName =
  | "cypher.create" | "cypher.set" | "cypher.delete"
  | "cypher.create_edge" | "cypher.delete_edge";

const NODE_KEY_PREFIX = "cypher:v1:";

function nodeKey(orgDid: string, label: string, nodeId: string): string {
  return `${NODE_KEY_PREFIX}${orgDid}:nodes:${label}:${nodeId}`;
}

function indexKey(orgDid: string, label: string): string {
  return `${NODE_KEY_PREFIX}${orgDid}:labels:${label}`;
}

// P92: edges. Per-orgDid keyspace, per-type index + per-source/dest
// indexes so traversal queries scale to many edges per node.
function edgeKey(orgDid: string, type: string, edgeId: string): string {
  return `${NODE_KEY_PREFIX}${orgDid}:edges:${type}:${edgeId}`;
}
function edgeTypeIndexKey(orgDid: string, type: string): string {
  return `${NODE_KEY_PREFIX}${orgDid}:edge_types:${type}`;
}
function edgeOutIndexKey(orgDid: string, srcLabel: string, srcId: string): string {
  return `${NODE_KEY_PREFIX}${orgDid}:edge_out:${srcLabel}:${srcId}`;
}

function parseProps(propsBlob: string): Record<string, unknown> {
  // Lightweight Cypher property parser: handles `prop:"value"` pairs with
  // string-only values. Good enough for the customer journey CREATE shape.
  const props: Record<string, unknown> = {};
  const re = /(\w+)\s*:\s*"([^"]*)"/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(propsBlob)) !== null) {
    props[m[1]] = m[2];
  }
  return props;
}

// P95/P96: WHERE clause predicates. Each predicate compares one property
// against a literal. Multiple predicates are joined by AND (P96).
type StringOp = "CONTAINS" | "STARTS_WITH" | "ENDS_WITH" | "EQ" | "NE";
type NumberOp = "GT" | "LT" | "GE" | "LE" | "EQ" | "NE";
type WherePredicate =
  | { prop: string; kind: "string"; op: StringOp; value: string }
  | { prop: string; kind: "number"; op: NumberOp; value: number };
type WhereFilter = WherePredicate[];

type ParsedCypher = {
  kind: "CREATE" | "MATCH" | "DELETE" | "SET" | "CREATE_EDGE" | "MATCH_EDGE" | "DELETE_EDGE" | "MATCH_TWO_HOP" | "MERGE_EDGE" | "OTHER";
  label?: string;
  props?: Record<string, unknown>;     // CREATE node properties OR MATCH filter
  setProps?: Record<string, unknown>;  // SET clause assignments
  whereFilter?: WhereFilter;           // P95
  returnExpr?: string;
  limit?: number;
  // P92/P93 edge fields
  srcLabel?: string;
  srcProps?: Record<string, unknown>;
  dstLabel?: string;
  dstProps?: Record<string, unknown>;
  edgeType?: string;
  edgeProps?: Record<string, unknown>;
  direction?: "outgoing" | "incoming"; // P93
  // P102 two-hop fields: (a:La)-[:T1]->(b:Lb?)-[:T2]->(c:Lc?)
  midLabel?: string;
  midProps?: Record<string, unknown>;
  edgeType2?: string;
};

// P95/P96: parse one or more predicates separated by AND. Returns null
// if the where clause doesn't parse cleanly (caller falls back to ignoring).
function parseWhere(whereClause: string): WhereFilter | null {
  const parts = whereClause.split(/\s+AND\s+/i).map((s) => s.trim()).filter(Boolean);
  if (parts.length === 0) return null;
  const out: WhereFilter = [];
  for (const part of parts) {
    const p = parseOnePredicate(part);
    if (!p) return null;
    out.push(p);
  }
  return out;
}

function parseOnePredicate(t: string): WherePredicate | null {
  // String predicates with explicit operator words.
  let m = /^\w+\.(\w+)\s+CONTAINS\s+"([^"]*)"$/i.exec(t);
  if (m) return { prop: m[1], kind: "string", op: "CONTAINS", value: m[2] };
  m = /^\w+\.(\w+)\s+STARTS\s+WITH\s+"([^"]*)"$/i.exec(t);
  if (m) return { prop: m[1], kind: "string", op: "STARTS_WITH", value: m[2] };
  m = /^\w+\.(\w+)\s+ENDS\s+WITH\s+"([^"]*)"$/i.exec(t);
  if (m) return { prop: m[1], kind: "string", op: "ENDS_WITH", value: m[2] };
  // String equality.
  m = /^\w+\.(\w+)\s*(=|!=|<>)\s*"([^"]*)"$/.exec(t);
  if (m) return { prop: m[1], kind: "string", op: m[2] === "=" ? "EQ" : "NE", value: m[3] };
  // Numeric comparison: prop OP number  (order matters: longer ops first)
  m = /^\w+\.(\w+)\s*(>=|<=|!=|<>|=|>|<)\s*(-?\d+(?:\.\d+)?)$/.exec(t);
  if (m) {
    const opMap: Record<string, NumberOp> = { ">": "GT", "<": "LT", ">=": "GE", "<=": "LE", "=": "EQ", "!=": "NE", "<>": "NE" };
    return { prop: m[1], kind: "number", op: opMap[m[2]] ?? "EQ", value: Number(m[3]) };
  }
  return null;
}

function applyWhere(props: Record<string, unknown>, predicates: WhereFilter): boolean {
  for (const p of predicates) {
    const v = props?.[p.prop];
    if (p.kind === "string") {
      if (typeof v !== "string") return false;
      switch (p.op) {
        case "CONTAINS":     if (!v.includes(p.value)) return false; break;
        case "STARTS_WITH":  if (!v.startsWith(p.value)) return false; break;
        case "ENDS_WITH":    if (!v.endsWith(p.value)) return false; break;
        case "EQ":           if (v !== p.value) return false; break;
        case "NE":           if (v === p.value) return false; break;
      }
    } else {
      // numeric — coerce both sides
      const n = typeof v === "number" ? v : (typeof v === "string" ? Number(v) : NaN);
      if (Number.isNaN(n)) return false;
      switch (p.op) {
        case "GT": if (!(n >  p.value)) return false; break;
        case "LT": if (!(n <  p.value)) return false; break;
        case "GE": if (!(n >= p.value)) return false; break;
        case "LE": if (!(n <= p.value)) return false; break;
        case "EQ": if (n !== p.value) return false; break;
        case "NE": if (n === p.value) return false; break;
      }
    }
  }
  return true;
}

function parseCypher(query: string): ParsedCypher {
  const trimmed = query.trim();

  // P92: CREATE (a:L1 {props})-[:TYPE {props}]->(b:L2 {props}) RETURN ...
  //      Creates both nodes + the edge in one statement. Must be checked
  //      BEFORE the simple CREATE branch because the edge form is a
  //      superset of the node form.
  const createEdgeMatch = /^CREATE\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*(\{([^}]*)\})?\s*\]\s*->\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*(?:RETURN\s+.+)?$/i.exec(trimmed);
  if (createEdgeMatch) {
    return {
      kind: "CREATE_EDGE",
      srcLabel: createEdgeMatch[1],
      srcProps: parseProps(createEdgeMatch[3] ?? ""),
      edgeType: createEdgeMatch[4],
      edgeProps: parseProps(createEdgeMatch[6] ?? ""),
      dstLabel: createEdgeMatch[7],
      dstProps: parseProps(createEdgeMatch[9] ?? ""),
    };
  }

  // P102: MERGE (a:L1 {props})-[:T]->(b:L2 {props}) RETURN a, b
  //       Reuses existing nodes that match label+props exactly; only
  //       creates fresh nodes if none match. Always creates a fresh
  //       edge (idempotent edge MERGE is harder; deferred).
  const mergeEdgeMatch = /^MERGE\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*(\{([^}]*)\})?\s*\]\s*->\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*(?:RETURN\s+.+)?$/i.exec(trimmed);
  if (mergeEdgeMatch) {
    return {
      kind: "MERGE_EDGE",
      srcLabel: mergeEdgeMatch[1],
      srcProps: parseProps(mergeEdgeMatch[3] ?? ""),
      edgeType: mergeEdgeMatch[4],
      edgeProps: parseProps(mergeEdgeMatch[6] ?? ""),
      dstLabel: mergeEdgeMatch[7],
      dstProps: parseProps(mergeEdgeMatch[9] ?? ""),
    };
  }

  // P102: MATCH (a:La {props}?)-[:T1]->(b:Lb? {props}?)-[:T2]->(c:Lc? {props}?) RETURN ...
  //       Two-hop outgoing traversal. Tried BEFORE single-hop / DELETE_EDGE
  //       because the simpler patterns would otherwise match a prefix.
  const twoHopRe = /^MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*\]\s*->\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*\]\s*->\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{([^}]*)\})?\s*\)\s*RETURN\s+(.+?)\s*(?:LIMIT\s+(\d+))?\s*$/i;
  const twoHopMatch = twoHopRe.exec(trimmed);
  if (twoHopMatch) {
    return {
      kind: "MATCH_TWO_HOP",
      srcLabel: twoHopMatch[2],
      srcProps: parseProps(twoHopMatch[4] ?? ""),
      edgeType: twoHopMatch[5],
      midLabel: twoHopMatch[7] || undefined,
      midProps: parseProps(twoHopMatch[9] ?? ""),
      edgeType2: twoHopMatch[10],
      dstLabel: twoHopMatch[12] || undefined,
      dstProps: parseProps(twoHopMatch[14] ?? ""),
      returnExpr: twoHopMatch[15],
      limit: twoHopMatch[16] ? Number(twoHopMatch[16]) : undefined,
    };
  }

  // P93: MATCH (a:L1 {filter})-[r:TYPE]->(b:L2 {filter}?) DELETE r
  //      Drops edges matching the pattern (nodes preserved).
  const deleteEdgeMatch = /^MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(\w+)\s*:\s*(\w+)\s*\]\s*->\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{([^}]*)\})?\s*\)\s*DELETE\s+(\w+)\s*$/i.exec(trimmed);
  if (deleteEdgeMatch && deleteEdgeMatch[11] === deleteEdgeMatch[5]) {
    return {
      kind: "DELETE_EDGE",
      srcLabel: deleteEdgeMatch[2],
      srcProps: parseProps(deleteEdgeMatch[4] ?? ""),
      edgeType: deleteEdgeMatch[6],
      dstLabel: deleteEdgeMatch[8] || undefined,
      dstProps: parseProps(deleteEdgeMatch[10] ?? ""),
    };
  }

  // P92: MATCH (a:L1 {filter})-[:TYPE]->(b:L2 {filter}?) RETURN ...
  //      Single-hop outgoing traversal. Returns (src, dst, edge) triples.
  const matchEdgeMatch = /^MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*\]\s*->\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{([^}]*)\})?\s*\)\s*RETURN\s+(.+?)\s*(?:LIMIT\s+(\d+))?\s*$/i.exec(trimmed);
  if (matchEdgeMatch) {
    return {
      kind: "MATCH_EDGE",
      direction: "outgoing",
      srcLabel: matchEdgeMatch[2],
      srcProps: parseProps(matchEdgeMatch[4] ?? ""),
      edgeType: matchEdgeMatch[5],
      dstLabel: matchEdgeMatch[7] || undefined,
      dstProps: parseProps(matchEdgeMatch[9] ?? ""),
      returnExpr: matchEdgeMatch[10],
      limit: matchEdgeMatch[11] ? Number(matchEdgeMatch[11]) : undefined,
    };
  }

  // P93: MATCH (b:L1 {filter})<-[:TYPE]-(a:L2 {filter}?) RETURN ...
  //      Single-hop INCOMING traversal — "who points at b?". Note: in
  //      our model we treat `b` (the inbound node) as src=L1 in user
  //      terms but execution walks the reverse direction. The parsed
  //      output uses `srcLabel` for the LEFT-side node in the pattern
  //      to stay consistent with the parser, with direction="incoming".
  const matchEdgeInMatch = /^MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*<\s*-\s*\[\s*(?:\w+\s*)?:\s*(\w+)\s*\]\s*-\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*(\{([^}]*)\})?\s*\)\s*RETURN\s+(.+?)\s*(?:LIMIT\s+(\d+))?\s*$/i.exec(trimmed);
  if (matchEdgeInMatch) {
    return {
      kind: "MATCH_EDGE",
      direction: "incoming",
      // LEFT-side variable (after `MATCH (`) is the inbound target — store
      // as dstLabel to match execution semantics (edges point TO it).
      dstLabel: matchEdgeInMatch[2],
      dstProps: parseProps(matchEdgeInMatch[4] ?? ""),
      edgeType: matchEdgeInMatch[5],
      // RIGHT-side variable is the source.
      srcLabel: matchEdgeInMatch[7] || undefined,
      srcProps: parseProps(matchEdgeInMatch[9] ?? ""),
      returnExpr: matchEdgeInMatch[10],
      limit: matchEdgeInMatch[11] ? Number(matchEdgeInMatch[11]) : undefined,
    };
  }

  // CREATE (n:Label {prop:"val", ...}) RETURN n
  const createMatch = /^CREATE\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*(?:RETURN\s+\w+)?/i.exec(trimmed);
  if (createMatch) {
    return { kind: "CREATE", label: createMatch[1], props: parseProps(createMatch[3] ?? "") };
  }
  // MATCH (n:Label) DELETE n  /  MATCH (n:Label) DETACH DELETE n
  const deleteMatch = /^MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\)\s*(?:DETACH\s+)?DELETE\s+\w+/i.exec(trimmed);
  if (deleteMatch) {
    return { kind: "DELETE", label: deleteMatch[1] };
  }
  // P90: MATCH (n:Label {filterProp:"val"}) SET n.prop = "newval" [, n.x="y"] RETURN n
  const setMatch = /^MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*SET\s+(.+?)\s*(?:RETURN\s+(\S+))?\s*$/i.exec(trimmed);
  if (setMatch) {
    const filter = parseProps(setMatch[4] ?? "");
    const assignments: Record<string, unknown> = {};
    // Parse "n.foo = \"bar\", n.baz = \"qux\"" — string values only.
    const ident = setMatch[1];
    const assignRe = new RegExp(`${ident}\\.(\\w+)\\s*=\\s*"([^"]*)"`, "g");
    let am: RegExpExecArray | null;
    while ((am = assignRe.exec(setMatch[5] ?? "")) !== null) {
      assignments[am[1]] = am[2];
    }
    return {
      kind: "SET",
      label: setMatch[2],
      props: filter,
      setProps: assignments,
      returnExpr: (setMatch[6] ?? "n").trim(),
    };
  }
  // P90/P95: MATCH (n:Label {props}?) [WHERE pred] RETURN expr [LIMIT N]
  const matchMatch = /^MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*(\{([^}]*)\})?\s*\)\s*(?:WHERE\s+(.+?)\s+)?RETURN\s+(\S+(?:\s*,\s*\S+)*)\s*(?:LIMIT\s+(\d+))?\s*$/i.exec(trimmed);
  if (matchMatch) {
    return {
      kind: "MATCH",
      label: matchMatch[1],
      props: parseProps(matchMatch[3] ?? ""),  // inline filter (may be empty)
      whereFilter: matchMatch[4] ? (parseWhere(matchMatch[4]) ?? undefined) : undefined,
      returnExpr: matchMatch[5],
      limit: matchMatch[6] ? Number(matchMatch[6]) : undefined,
    };
  }
  return { kind: "OTHER" };
}

export async function tryServeCypherFromKv(
  env: KvCypherEnv,
  orgDid: string,
  query: string,
): Promise<CypherKvResult | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  const parsed = parseCypher(query);
  if (parsed.kind === "OTHER") return null;

  if (parsed.kind === "CREATE" && parsed.label) {
    const nodeId = crypto.randomUUID();
    const node = { id: nodeId, label: parsed.label, props: parsed.props ?? {}, createdAt: new Date().toISOString() };
    await kv.put(nodeKey(orgDid, parsed.label, nodeId), JSON.stringify(node));
    // Maintain a label → [nodeId] index for MATCH scans.
    try {
      const idxRaw = await kv.get(indexKey(orgDid, parsed.label));
      const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
      idx.ids = [...(idx.ids ?? []), nodeId];
      await kv.put(indexKey(orgDid, parsed.label), JSON.stringify(idx));
    } catch (e) {
      console.warn("[yatabase][cypher-kv] index update failed:", e);
    }
    return {
      columns: ["n"],
      data: [{ row: [{ labels: [parsed.label], properties: node.props }], meta: [null] }],
      mutations: [{ event: "cypher.create", payload: { label: parsed.label, properties: node.props } }],
    };
  }

  if (parsed.kind === "MATCH" && parsed.label) {
    const idxRaw = await kv.get(indexKey(orgDid, parsed.label));
    const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
    // P90: load all candidates first, then apply property filter, then LIMIT.
    // (We can't slice ids early because the filter may eliminate some.)
    const allIds = idx.ids ?? [];
    const nodes: Array<{ id: string; label: string; props: Record<string, unknown> }> = [];
    const filter = parsed.props ?? {};
    const filterKeys = Object.keys(filter);
    const cap = parsed.limit ?? 100;
    for (const id of allIds) {
      const nodeRaw = await kv.get(nodeKey(orgDid, parsed.label, id));
      if (!nodeRaw) continue;
      try {
        const node = JSON.parse(nodeRaw) as { id: string; label: string; props: Record<string, unknown> };
        if (filterKeys.length > 0) {
          let matchAll = true;
          for (const k of filterKeys) {
            if (node.props?.[k] !== filter[k]) { matchAll = false; break; }
          }
          if (!matchAll) continue;
        }
        // P95: optional WHERE predicate (CONTAINS / STARTS WITH / ENDS WITH)
        if (parsed.whereFilter && !applyWhere(node.props, parsed.whereFilter)) continue;
        nodes.push(node);
        if (nodes.length >= cap) break;
      } catch { /* ignore */ }
    }
    // Project the RETURN expression. Supports `n`, `n.prop` (single).
    const returnExpr = (parsed.returnExpr ?? "n").trim();
    const isFullNode = /^\w+$/.test(returnExpr);
    if (isFullNode) {
      return {
        columns: [returnExpr],
        data: nodes.map((n) => ({
          row: [{ labels: [parsed.label!], properties: n.props }],
          meta: [null],
        })),
      };
    }
    const propMatch = /^\w+\.(\w+)$/.exec(returnExpr);
    if (propMatch) {
      const prop = propMatch[1];
      return {
        columns: [returnExpr],
        data: nodes.map((n) => ({ row: [n.props?.[prop] ?? null], meta: [null] })),
      };
    }
    // Fall back to full-node return on unknown shapes.
    return {
      columns: [returnExpr],
      data: nodes.map((n) => ({
        row: [{ labels: [parsed.label!], properties: n.props }],
        meta: [null],
      })),
    };
  }

  if (parsed.kind === "SET" && parsed.label) {
    const idxRaw = await kv.get(indexKey(orgDid, parsed.label));
    const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
    const filter = parsed.props ?? {};
    const filterKeys = Object.keys(filter);
    const assignments = parsed.setProps ?? {};
    const updated: Array<{ id: string; label: string; props: Record<string, unknown> }> = [];
    for (const id of idx.ids ?? []) {
      const k = nodeKey(orgDid, parsed.label, id);
      const raw = await kv.get(k);
      if (!raw) continue;
      try {
        const node = JSON.parse(raw) as { id: string; label: string; props: Record<string, unknown>; createdAt?: string };
        if (filterKeys.length > 0) {
          let matchAll = true;
          for (const fk of filterKeys) {
            if (node.props?.[fk] !== filter[fk]) { matchAll = false; break; }
          }
          if (!matchAll) continue;
        }
        node.props = { ...node.props, ...assignments };
        await kv.put(k, JSON.stringify(node));
        updated.push(node);
      } catch { /* ignore */ }
    }
    const returnExpr = (parsed.returnExpr ?? "n").trim();
    const isFullNode = /^\w+$/.test(returnExpr);
    const setMutations = updated.map((n) => ({
      event: "cypher.set" as const,
      payload: { label: parsed.label!, properties: n.props, updatedCount: updated.length },
    }));
    if (isFullNode) {
      return {
        columns: [returnExpr],
        data: updated.map((n) => ({
          row: [{ labels: [parsed.label!], properties: n.props }],
          meta: [null],
        })),
        mutations: setMutations,
      };
    }
    const propMatch = /^\w+\.(\w+)$/.exec(returnExpr);
    if (propMatch) {
      const prop = propMatch[1];
      return {
        columns: [returnExpr],
        data: updated.map((n) => ({ row: [n.props?.[prop] ?? null], meta: [null] })),
        mutations: setMutations,
      };
    }
    return { columns: [returnExpr], data: [], mutations: setMutations };
  }

  if (parsed.kind === "DELETE" && parsed.label) {
    const idxRaw = await kv.get(indexKey(orgDid, parsed.label));
    const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
    const ids = idx.ids ?? [];
    for (const id of ids) {
      try { await kv.delete(nodeKey(orgDid, parsed.label, id)); } catch { /* ignore */ }
    }
    try { await kv.delete(indexKey(orgDid, parsed.label)); } catch { /* ignore */ }
    return {
      columns: [],
      data: [],
      mutations: [{ event: "cypher.delete", payload: { label: parsed.label, deletedCount: ids.length } }],
    };
  }

  // P92: CREATE (a:L1)-[:T]->(b:L2). Creates both nodes + the edge.
  // P102: MERGE_EDGE — like CREATE_EDGE but reuses existing nodes that
  // match label+props exactly. Customers chain edges to build multi-hop
  // graphs without duplicating intermediate nodes.
  if (parsed.kind === "MERGE_EDGE" && parsed.srcLabel && parsed.dstLabel && parsed.edgeType) {
    async function findOrCreateNode(label: string, props: Record<string, unknown>): Promise<{ id: string; props: Record<string, unknown> }> {
      const idxRaw = await kv.get(indexKey(orgDid, label));
      const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
      const filterKeys = Object.keys(props);
      // Linear scan — fine at KV scale.
      for (const id of idx.ids ?? []) {
        const raw = await kv.get(nodeKey(orgDid, label, id));
        if (!raw) continue;
        try {
          const node = JSON.parse(raw) as { id: string; props: Record<string, unknown> };
          let matchAll = true;
          for (const k of filterKeys) {
            if (node.props?.[k] !== props[k]) { matchAll = false; break; }
          }
          if (matchAll) return { id: node.id, props: node.props };
        } catch { /* ignore */ }
      }
      // Not found — create.
      const newId = crypto.randomUUID();
      const newNode = { id: newId, label, props, createdAt: new Date().toISOString() };
      await kv.put(nodeKey(orgDid, label, newId), JSON.stringify(newNode));
      idx.ids = [...(idx.ids ?? []), newId];
      await kv.put(indexKey(orgDid, label), JSON.stringify(idx));
      return { id: newId, props };
    }
    const src = await findOrCreateNode(parsed.srcLabel, parsed.srcProps ?? {});
    const dst = await findOrCreateNode(parsed.dstLabel, parsed.dstProps ?? {});

    // P103: idempotent edge MERGE. Look for an existing edge of the same
    // type between src and dst. If one exists, return it without creating
    // a duplicate. Only adds a new edge when nothing matches.
    let existingEdgeId: string | null = null;
    let existingEdgeProps: Record<string, unknown> = {};
    try {
      const outRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, src.id));
      if (outRaw) {
        const out = JSON.parse(outRaw) as { edges?: string[] };
        for (const eId of out.edges ?? []) {
          const eRaw = await kv.get(edgeKey(orgDid, parsed.edgeType, eId));
          if (!eRaw) continue;
          try {
            const e = JSON.parse(eRaw) as { type: string; dstId: string; dstLabel: string; props: Record<string, unknown> };
            if (e.type === parsed.edgeType && e.dstId === dst.id && e.dstLabel === parsed.dstLabel) {
              existingEdgeId = eId;
              existingEdgeProps = e.props ?? {};
              break;
            }
          } catch { /* ignore */ }
        }
      }
    } catch { /* ignore */ }

    let edgeMutation: { event: "cypher.create_edge"; payload: Record<string, unknown> } | null = null;
    if (!existingEdgeId) {
      const edgeId = crypto.randomUUID();
      const edge = {
        id: edgeId, type: parsed.edgeType,
        srcLabel: parsed.srcLabel, srcId: src.id,
        dstLabel: parsed.dstLabel, dstId: dst.id,
        props: parsed.edgeProps ?? {}, createdAt: new Date().toISOString(),
      };
      await kv.put(edgeKey(orgDid, parsed.edgeType, edgeId), JSON.stringify(edge));
      try {
        const tRaw = await kv.get(edgeTypeIndexKey(orgDid, parsed.edgeType));
        const tIdx = tRaw ? JSON.parse(tRaw) as { ids?: string[] } : { ids: [] };
        tIdx.ids = [...(tIdx.ids ?? []), edgeId];
        await kv.put(edgeTypeIndexKey(orgDid, parsed.edgeType), JSON.stringify(tIdx));
      } catch { /* ignore */ }
      try {
        const outRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, src.id));
        const out = outRaw ? JSON.parse(outRaw) as { edges?: string[] } : { edges: [] };
        out.edges = [...(out.edges ?? []), edgeId];
        await kv.put(edgeOutIndexKey(orgDid, parsed.srcLabel, src.id), JSON.stringify(out));
      } catch { /* ignore */ }
      edgeMutation = {
        event: "cypher.create_edge",
        payload: {
          srcLabel: parsed.srcLabel, srcProperties: src.props,
          edgeType: parsed.edgeType, edgeProperties: edge.props,
          dstLabel: parsed.dstLabel, dstProperties: dst.props,
        },
      };
    }
    // (P103: when the edge already existed, no mutation event fires —
    // re-MERGE is a no-op as far as webhook subscribers are concerned.)
    return {
      columns: ["a", "b"],
      data: [{
        row: [
          { labels: [parsed.srcLabel], properties: src.props },
          { labels: [parsed.dstLabel], properties: dst.props },
        ],
        meta: [null, null],
      }],
      mutations: edgeMutation ? [edgeMutation] : [],
    };
  }

  if (parsed.kind === "CREATE_EDGE" && parsed.srcLabel && parsed.dstLabel && parsed.edgeType) {
    const srcId = crypto.randomUUID();
    const dstId = crypto.randomUUID();
    const edgeId = crypto.randomUUID();
    const now = new Date().toISOString();
    const srcNode = { id: srcId, label: parsed.srcLabel, props: parsed.srcProps ?? {}, createdAt: now };
    const dstNode = { id: dstId, label: parsed.dstLabel, props: parsed.dstProps ?? {}, createdAt: now };
    const edge = {
      id: edgeId, type: parsed.edgeType,
      srcLabel: parsed.srcLabel, srcId,
      dstLabel: parsed.dstLabel, dstId,
      props: parsed.edgeProps ?? {}, createdAt: now,
    };
    // Persist nodes + edge + indexes.
    await kv.put(nodeKey(orgDid, parsed.srcLabel, srcId), JSON.stringify(srcNode));
    await kv.put(nodeKey(orgDid, parsed.dstLabel, dstId), JSON.stringify(dstNode));
    await kv.put(edgeKey(orgDid, parsed.edgeType, edgeId), JSON.stringify(edge));
    for (const [lbl, id] of [[parsed.srcLabel, srcId], [parsed.dstLabel, dstId]]) {
      try {
        const idxRaw = await kv.get(indexKey(orgDid, lbl));
        const idx = idxRaw ? JSON.parse(idxRaw) as { ids?: string[] } : { ids: [] };
        idx.ids = [...(idx.ids ?? []), id];
        await kv.put(indexKey(orgDid, lbl), JSON.stringify(idx));
      } catch { /* ignore */ }
    }
    try {
      const tRaw = await kv.get(edgeTypeIndexKey(orgDid, parsed.edgeType));
      const tIdx = tRaw ? JSON.parse(tRaw) as { ids?: string[] } : { ids: [] };
      tIdx.ids = [...(tIdx.ids ?? []), edgeId];
      await kv.put(edgeTypeIndexKey(orgDid, parsed.edgeType), JSON.stringify(tIdx));
    } catch { /* ignore */ }
    try {
      const outRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, srcId));
      const out = outRaw ? JSON.parse(outRaw) as { edges?: string[] } : { edges: [] };
      out.edges = [...(out.edges ?? []), edgeId];
      await kv.put(edgeOutIndexKey(orgDid, parsed.srcLabel, srcId), JSON.stringify(out));
    } catch { /* ignore */ }
    return {
      columns: ["a", "b"],
      data: [{
        row: [
          { labels: [parsed.srcLabel], properties: srcNode.props },
          { labels: [parsed.dstLabel], properties: dstNode.props },
        ],
        meta: [null, null],
      }],
      mutations: [{
        event: "cypher.create_edge",
        payload: {
          srcLabel: parsed.srcLabel, srcProperties: srcNode.props,
          edgeType: parsed.edgeType, edgeProperties: edge.props,
          dstLabel: parsed.dstLabel, dstProperties: dstNode.props,
        },
      }],
    };
  }

  // P93: DELETE_EDGE — `MATCH (a:L)-[r:T]->(b) DELETE r`. Drops edges
  // matching the pattern (nodes preserved).
  if (parsed.kind === "DELETE_EDGE" && parsed.srcLabel && parsed.edgeType) {
    const srcIdxRaw = await kv.get(indexKey(orgDid, parsed.srcLabel));
    const srcIdx = srcIdxRaw ? JSON.parse(srcIdxRaw) as { ids?: string[] } : { ids: [] };
    const srcFilter = parsed.srcProps ?? {};
    const srcFilterKeys = Object.keys(srcFilter);
    const dstFilter = parsed.dstProps ?? {};
    const dstFilterKeys = Object.keys(dstFilter);
    for (const srcId of srcIdx.ids ?? []) {
      const srcRaw = await kv.get(nodeKey(orgDid, parsed.srcLabel, srcId));
      if (!srcRaw) continue;
      let srcNode: { props: Record<string, unknown> };
      try { srcNode = JSON.parse(srcRaw); } catch { continue; }
      let srcMatches = true;
      for (const k of srcFilterKeys) {
        if (srcNode.props?.[k] !== srcFilter[k]) { srcMatches = false; break; }
      }
      if (!srcMatches) continue;
      const outRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, srcId));
      if (!outRaw) continue;
      const outIdx = JSON.parse(outRaw) as { edges?: string[] };
      const remaining: string[] = [];
      for (const edgeId of outIdx.edges ?? []) {
        const eRaw = await kv.get(edgeKey(orgDid, parsed.edgeType, edgeId));
        if (!eRaw) { remaining.push(edgeId); continue; }
        let edge: { type: string; dstLabel: string; dstId: string };
        try { edge = JSON.parse(eRaw); } catch { remaining.push(edgeId); continue; }
        if (edge.type !== parsed.edgeType) { remaining.push(edgeId); continue; }
        if (parsed.dstLabel && edge.dstLabel !== parsed.dstLabel) { remaining.push(edgeId); continue; }
        if (dstFilterKeys.length > 0) {
          const dstRaw = await kv.get(nodeKey(orgDid, edge.dstLabel, edge.dstId));
          if (!dstRaw) { remaining.push(edgeId); continue; }
          let dstNode: { props: Record<string, unknown> };
          try { dstNode = JSON.parse(dstRaw); } catch { remaining.push(edgeId); continue; }
          let dstMatches = true;
          for (const k of dstFilterKeys) {
            if (dstNode.props?.[k] !== dstFilter[k]) { dstMatches = false; break; }
          }
          if (!dstMatches) { remaining.push(edgeId); continue; }
        }
        try { await kv.delete(edgeKey(orgDid, parsed.edgeType, edgeId)); } catch { /* ignore */ }
        try {
          const tRaw = await kv.get(edgeTypeIndexKey(orgDid, parsed.edgeType));
          if (tRaw) {
            const tIdx = JSON.parse(tRaw) as { ids?: string[] };
            const filtered = (tIdx.ids ?? []).filter((id) => id !== edgeId);
            await kv.put(edgeTypeIndexKey(orgDid, parsed.edgeType), JSON.stringify({ ids: filtered }));
          }
        } catch { /* ignore */ }
      }
      if (remaining.length !== (outIdx.edges ?? []).length) {
        await kv.put(edgeOutIndexKey(orgDid, parsed.srcLabel, srcId), JSON.stringify({ edges: remaining }));
      }
    }
    return {
      columns: [],
      data: [],
      mutations: [{
        event: "cypher.delete_edge",
        payload: {
          srcLabel: parsed.srcLabel,
          edgeType: parsed.edgeType,
          dstLabel: parsed.dstLabel,
        },
      }],
    };
  }

  // P93: MATCH (b:L)<-[:T]-(a) — incoming traversal. No edge_in index,
  // so scan all edges of the type and filter by dst.
  if (parsed.kind === "MATCH_EDGE" && parsed.direction === "incoming" && parsed.dstLabel && parsed.edgeType) {
    const dstFilter = parsed.dstProps ?? {};
    const dstFilterKeys = Object.keys(dstFilter);
    const srcFilter = parsed.srcProps ?? {};
    const srcFilterKeys = Object.keys(srcFilter);
    const cap = parsed.limit ?? 100;
    const matches: Array<{
      src: { label: string; props: Record<string, unknown> };
      dst: { label: string; props: Record<string, unknown> };
    }> = [];
    const tRaw = await kv.get(edgeTypeIndexKey(orgDid, parsed.edgeType));
    if (!tRaw) return { columns: (parsed.returnExpr ?? "a, b").split(",").map(s=>s.trim()), data: [] };
    const tIdx = JSON.parse(tRaw) as { ids?: string[] };
    for (const edgeId of tIdx.ids ?? []) {
      const eRaw = await kv.get(edgeKey(orgDid, parsed.edgeType, edgeId));
      if (!eRaw) continue;
      let edge: { type: string; srcLabel: string; srcId: string; dstLabel: string; dstId: string };
      try { edge = JSON.parse(eRaw); } catch { continue; }
      // Filter by dst label + dst props.
      if (edge.dstLabel !== parsed.dstLabel) continue;
      const dstRaw = await kv.get(nodeKey(orgDid, edge.dstLabel, edge.dstId));
      if (!dstRaw) continue;
      let dstNode: { label: string; props: Record<string, unknown> };
      try { dstNode = JSON.parse(dstRaw); } catch { continue; }
      let dstMatches = true;
      for (const k of dstFilterKeys) {
        if (dstNode.props?.[k] !== dstFilter[k]) { dstMatches = false; break; }
      }
      if (!dstMatches) continue;
      // Filter by src (label optional, props optional).
      const srcRaw = await kv.get(nodeKey(orgDid, edge.srcLabel, edge.srcId));
      if (!srcRaw) continue;
      let srcNode: { label: string; props: Record<string, unknown> };
      try { srcNode = JSON.parse(srcRaw); } catch { continue; }
      if (parsed.srcLabel && srcNode.label !== parsed.srcLabel) continue;
      let srcMatches = true;
      for (const k of srcFilterKeys) {
        if (srcNode.props?.[k] !== srcFilter[k]) { srcMatches = false; break; }
      }
      if (!srcMatches) continue;
      matches.push({ src: { label: srcNode.label, props: srcNode.props }, dst: { label: dstNode.label, props: dstNode.props } });
      if (matches.length >= cap) break;
    }
    const exprs = (parsed.returnExpr ?? "a, b").split(",").map((s) => s.trim());
    const data = matches.map((m) => {
      const row: unknown[] = [];
      for (const expr of exprs) {
        const m1 = /^(\w+)$/.exec(expr);
        if (m1) {
          const ref = m1[1];
          if (ref === "a") row.push({ labels: [m.src.label], properties: m.src.props });
          else if (ref === "b") row.push({ labels: [m.dst.label], properties: m.dst.props });
          else row.push(null);
          continue;
        }
        const m2 = /^(\w+)\.(\w+)$/.exec(expr);
        if (m2) {
          const ref = m2[1], prop = m2[2];
          if (ref === "a") row.push(m.src.props?.[prop] ?? null);
          else if (ref === "b") row.push(m.dst.props?.[prop] ?? null);
          else row.push(null);
          continue;
        }
        row.push(null);
      }
      return { row, meta: exprs.map(() => null) };
    });
    return { columns: exprs, data };
  }

  // P92: MATCH (a:L1)-[:T]->(b) RETURN a, b. Single-hop outgoing traversal.
  if (parsed.kind === "MATCH_EDGE" && parsed.srcLabel && parsed.edgeType) {
    // Find candidate source nodes matching the filter.
    const srcIdxRaw = await kv.get(indexKey(orgDid, parsed.srcLabel));
    const srcIdx = srcIdxRaw ? JSON.parse(srcIdxRaw) as { ids?: string[] } : { ids: [] };
    const srcFilter = parsed.srcProps ?? {};
    const srcFilterKeys = Object.keys(srcFilter);
    const matches: Array<{
      src: { label: string; props: Record<string, unknown> };
      dst: { label: string; props: Record<string, unknown> };
      edge: { type: string; props: Record<string, unknown> };
    }> = [];
    const cap = parsed.limit ?? 100;
    for (const srcId of srcIdx.ids ?? []) {
      const srcRaw = await kv.get(nodeKey(orgDid, parsed.srcLabel, srcId));
      if (!srcRaw) continue;
      let srcNode: { id: string; label: string; props: Record<string, unknown> };
      try { srcNode = JSON.parse(srcRaw); } catch { continue; }
      // Apply src filter.
      let srcMatches = true;
      for (const k of srcFilterKeys) {
        if (srcNode.props?.[k] !== srcFilter[k]) { srcMatches = false; break; }
      }
      if (!srcMatches) continue;
      // Walk outgoing edges of this type.
      const outRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, srcId));
      if (!outRaw) continue;
      const outIdx = JSON.parse(outRaw) as { edges?: string[] };
      for (const edgeId of outIdx.edges ?? []) {
        const eRaw = await kv.get(edgeKey(orgDid, parsed.edgeType, edgeId));
        if (!eRaw) continue;
        let edge: { type: string; dstLabel: string; dstId: string; props: Record<string, unknown> };
        try { edge = JSON.parse(eRaw); } catch { continue; }
        if (edge.type !== parsed.edgeType) continue;
        // Load destination node.
        const dstRaw = await kv.get(nodeKey(orgDid, edge.dstLabel, edge.dstId));
        if (!dstRaw) continue;
        let dstNode: { id: string; label: string; props: Record<string, unknown> };
        try { dstNode = JSON.parse(dstRaw); } catch { continue; }
        // Apply dst label filter if specified.
        if (parsed.dstLabel && dstNode.label !== parsed.dstLabel) continue;
        // Apply dst props filter.
        const dstFilter = parsed.dstProps ?? {};
        let dstMatches = true;
        for (const k of Object.keys(dstFilter)) {
          if (dstNode.props?.[k] !== dstFilter[k]) { dstMatches = false; break; }
        }
        if (!dstMatches) continue;
        matches.push({
          src: { label: srcNode.label, props: srcNode.props },
          dst: { label: dstNode.label, props: dstNode.props },
          edge: { type: edge.type, props: edge.props },
        });
        if (matches.length >= cap) break;
      }
      if (matches.length >= cap) break;
    }
    // Render based on returnExpr — supports "a, b", "a.prop, b.prop", etc.
    const exprs = (parsed.returnExpr ?? "a, b").split(",").map((s) => s.trim());
    const data = matches.map((m) => {
      const row: unknown[] = [];
      for (const expr of exprs) {
        const m1 = /^(\w+)$/.exec(expr);
        if (m1) {
          const ref = m1[1];
          if (ref === "a") row.push({ labels: [m.src.label], properties: m.src.props });
          else if (ref === "b") row.push({ labels: [m.dst.label], properties: m.dst.props });
          else row.push(null);
          continue;
        }
        const m2 = /^(\w+)\.(\w+)$/.exec(expr);
        if (m2) {
          const ref = m2[1], prop = m2[2];
          if (ref === "a") row.push(m.src.props?.[prop] ?? null);
          else if (ref === "b") row.push(m.dst.props?.[prop] ?? null);
          else row.push(null);
          continue;
        }
        row.push(null);
      }
      return { row, meta: exprs.map(() => null) };
    });
    return { columns: exprs, data };
  }

  // P102: two-hop outgoing traversal.
  if (parsed.kind === "MATCH_TWO_HOP" && parsed.srcLabel && parsed.edgeType && parsed.edgeType2) {
    const srcIdxRaw = await kv.get(indexKey(orgDid, parsed.srcLabel));
    const srcIdx = srcIdxRaw ? JSON.parse(srcIdxRaw) as { ids?: string[] } : { ids: [] };
    const srcFilter = parsed.srcProps ?? {};
    const srcFilterKeys = Object.keys(srcFilter);
    const midFilter = parsed.midProps ?? {};
    const midFilterKeys = Object.keys(midFilter);
    const dstFilter = parsed.dstProps ?? {};
    const dstFilterKeys = Object.keys(dstFilter);
    const cap = parsed.limit ?? 100;
    const matches: Array<{
      a: { label: string; props: Record<string, unknown> };
      b: { label: string; props: Record<string, unknown> };
      c: { label: string; props: Record<string, unknown> };
    }> = [];

    outer:
    for (const aId of srcIdx.ids ?? []) {
      const aRaw = await kv.get(nodeKey(orgDid, parsed.srcLabel, aId));
      if (!aRaw) continue;
      let aNode: { label: string; props: Record<string, unknown> };
      try { aNode = JSON.parse(aRaw); } catch { continue; }
      let aOk = true;
      for (const k of srcFilterKeys) {
        if (aNode.props?.[k] !== srcFilter[k]) { aOk = false; break; }
      }
      if (!aOk) continue;
      const aOutRaw = await kv.get(edgeOutIndexKey(orgDid, parsed.srcLabel, aId));
      if (!aOutRaw) continue;
      const aOut = JSON.parse(aOutRaw) as { edges?: string[] };
      for (const e1Id of aOut.edges ?? []) {
        const e1Raw = await kv.get(edgeKey(orgDid, parsed.edgeType, e1Id));
        if (!e1Raw) continue;
        let e1: { type: string; dstLabel: string; dstId: string };
        try { e1 = JSON.parse(e1Raw); } catch { continue; }
        if (e1.type !== parsed.edgeType) continue;
        if (parsed.midLabel && e1.dstLabel !== parsed.midLabel) continue;
        const bRaw = await kv.get(nodeKey(orgDid, e1.dstLabel, e1.dstId));
        if (!bRaw) continue;
        let bNode: { label: string; props: Record<string, unknown> };
        try { bNode = JSON.parse(bRaw); } catch { continue; }
        let bOk = true;
        for (const k of midFilterKeys) {
          if (bNode.props?.[k] !== midFilter[k]) { bOk = false; break; }
        }
        if (!bOk) continue;
        // Walk second hop from b.
        const bOutRaw = await kv.get(edgeOutIndexKey(orgDid, e1.dstLabel, e1.dstId));
        if (!bOutRaw) continue;
        const bOut = JSON.parse(bOutRaw) as { edges?: string[] };
        for (const e2Id of bOut.edges ?? []) {
          const e2Raw = await kv.get(edgeKey(orgDid, parsed.edgeType2, e2Id));
          if (!e2Raw) continue;
          let e2: { type: string; dstLabel: string; dstId: string };
          try { e2 = JSON.parse(e2Raw); } catch { continue; }
          if (e2.type !== parsed.edgeType2) continue;
          if (parsed.dstLabel && e2.dstLabel !== parsed.dstLabel) continue;
          const cRaw = await kv.get(nodeKey(orgDid, e2.dstLabel, e2.dstId));
          if (!cRaw) continue;
          let cNode: { label: string; props: Record<string, unknown> };
          try { cNode = JSON.parse(cRaw); } catch { continue; }
          let cOk = true;
          for (const k of dstFilterKeys) {
            if (cNode.props?.[k] !== dstFilter[k]) { cOk = false; break; }
          }
          if (!cOk) continue;
          matches.push({
            a: { label: aNode.label, props: aNode.props },
            b: { label: bNode.label, props: bNode.props },
            c: { label: cNode.label, props: cNode.props },
          });
          if (matches.length >= cap) break outer;
        }
      }
    }
    // Render. RETURN accepts a, b, c, or a.prop, b.prop, c.prop.
    const exprs = (parsed.returnExpr ?? "a, b, c").split(",").map((s) => s.trim());
    const data = matches.map((m) => {
      const row: unknown[] = [];
      for (const expr of exprs) {
        const m1 = /^(\w+)$/.exec(expr);
        if (m1) {
          const ref = m1[1];
          if (ref === "a") row.push({ labels: [m.a.label], properties: m.a.props });
          else if (ref === "b") row.push({ labels: [m.b.label], properties: m.b.props });
          else if (ref === "c") row.push({ labels: [m.c.label], properties: m.c.props });
          else row.push(null);
          continue;
        }
        const m2 = /^(\w+)\.(\w+)$/.exec(expr);
        if (m2) {
          const ref = m2[1], prop = m2[2];
          const src = ref === "a" ? m.a : ref === "b" ? m.b : ref === "c" ? m.c : null;
          row.push(src?.props?.[prop] ?? null);
          continue;
        }
        row.push(null);
      }
      return { row, meta: exprs.map(() => null) };
    });
    return { columns: exprs, data };
  }

  return null;
}
