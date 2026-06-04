/**
 * Local graph cache accelerator for yoro.
 *
 * Remote label scans were disabled after Kagami started enforcing
 * selective WHERE predicates and promoted-column-only ORDER BY.
 * Canonical data access remains the app's regular XRPC routes.
 */

/** Sentinel name used in pseudo-SQL FROM clauses for multi-hop join detection. */
const LOCAL_GRAPH_TABLE = "local_graph" as const;
import { atProcedure } from '$lib/atproto-agent';

const labelMeta = new Map<string, { loadedAt: number; rowCount: number }>();

type GraphRow = Record<string, unknown> & {
  label?: string;
  vertex_id?: string;
  edge_id?: string;
  src_vid?: string;
  dst_vid?: string;
  val?: string;
  text?: string;
  updated_at?: string;
  record_type?: string;
};

/** Cached rows keyed by label. */
const _apiRows = new Map<string, Record<string, unknown>[]>();

export function isEnabled(): boolean { return false; }

/** Get cached rows for a label. */
export function getCachedRows(label: string): Record<string, unknown>[] {
  return _apiRows.get(label) ?? [];
}

/** Replace cached rows for a label. */
export function setCachedRows(label: string, rows: Record<string, unknown>[]): void {
  _apiRows.set(label, rows);
}

let _ready = $state(false);
let _loading = $state(false);
let _error = $state("");
let _loadedLabels = $state<string[]>([]);

export function isReady(): boolean { return _ready; }
export function isLoading(): boolean { return _loading; }
export function getError(): string { return _error; }
export function getLoadedLabels(): string[] { return _loadedLabels; }

function normalizeRow(raw: Record<string, unknown>, fallbackLabel: string): GraphRow {
  const row: GraphRow = { ...raw };
  row.label = String(raw.label ?? fallbackLabel);
  row.record_type = String(raw.record_type ?? (raw.edge_id ? 'edge' : 'vertex'));
  row.vertex_id = raw.vertex_id ? String(raw.vertex_id) : undefined;
  row.edge_id = raw.edge_id ? String(raw.edge_id) : undefined;
  row.src_vid = raw.src_vid ? String(raw.src_vid) : undefined;
  row.dst_vid = raw.dst_vid ? String(raw.dst_vid) : undefined;
  row.updated_at = raw.updated_at ? String(raw.updated_at) : '';
  const val = raw.val;
  if (typeof val === 'string') row.val = val;
  else if (val && typeof val === 'object') row.val = JSON.stringify(val);
  else row.val = '';
  const text = raw.text ?? raw.summary ?? raw.content ?? '';
  row.text = String(text);
  return row;
}

export async function setupPropertyGraph(): Promise<void> {
  // No-op: property graph acceleration removed; XRPC is now the sole path.
}

/** Local-only compatibility shim.
 *  Remote `MATCH (n:Label)` scans now fail Kagami validation (`FULL_TABLE_SCAN`). */
export async function loadLabel(label: string, limit = 50): Promise<number> {
  _loading = true;
  _error = "";

  try {
    const existing = (_apiRows.get(label) ?? []) as GraphRow[];
    const totalRows = existing.slice(0, Math.max(Number(limit) || 50, 0)).length;
    labelMeta.set(label, { loadedAt: Date.now(), rowCount: totalRows });
    _loadedLabels = Array.from(labelMeta.keys());
    _ready = true;
    return totalRows;
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.warn(`[kagami-store] loadLabel(${label}) failed`, msg);
    _error = msg;
    return 0;
  } finally {
    _loading = false;
  }
}

export function hasLabel(label: string): boolean {
  return (_apiRows.get(label)?.length ?? 0) > 0;
}

export async function listAvailableLabels(): Promise<Array<{ label: string; count?: number }>> {
  try {
    const res = await atProcedure<{ labels?: Array<{ label?: string; count?: number }> }>('com.etzhayyim.kagami.listLabels', {});
    const labels = Array.isArray(res?.labels) ? res.labels : [];
    return labels
      .map((l) => ({ label: String(l?.label ?? ''), count: l?.count }))
      .filter((l) => l.label.length > 0);
  } catch {
    return Array.from(labelMeta.entries()).map(([label, meta]) => ({ label, count: meta.rowCount }));
  }
}

function matchesKeyword(row: GraphRow, keyword: string): boolean {
  const kw = keyword.toLowerCase();
  if (kw.length === 0) return true;
  const text = String(row.text ?? '').toLowerCase();
  const valText = String(row.val ?? '').toLowerCase();
  return text.includes(kw) || valText.includes(kw);
}

export async function federatedQuery(label: string, keyword: string, limit = 50): Promise<number> {
  try {
    const existing = ((_apiRows.get(label) ?? []) as GraphRow[])
      .map((row) => normalizeRow(row, label));
    const normalized = existing
      .filter((row) => matchesKeyword(row, keyword))
      .slice(0, Math.max(Number(limit) || 50, 0));
    const dedup = new Map<string, GraphRow>();
    for (const row of existing) {
      const key = String(row.vertex_id ?? row.edge_id ?? JSON.stringify(row));
      dedup.set(key, row);
    }
    for (const row of normalized) {
      const key = String(row.vertex_id ?? row.edge_id ?? JSON.stringify(row));
      dedup.set(key, row);
    }
    const merged = Array.from(dedup.values());
    _apiRows.set(label, merged);
    labelMeta.set(label, { loadedAt: Date.now(), rowCount: merged.length });
    _loadedLabels = Array.from(labelMeta.keys());
    _ready = true;
    return normalized.length;
  } catch {
    return 0;
  }
}

function extractLikeKeywords(query: string): string[] {
  const out: string[] = [];
  const re = /LIKE\s+'%([^%']+)%'/g;
  let m: RegExpExecArray | null = null;
  while ((m = re.exec(query)) !== null) out.push(m[1].toLowerCase());
  return [...new Set(out)];
}

function extractLimit(query: string, fallback = 50): number {
  const m = query.match(/LIMIT\s+(\d+)/i);
  if (!m) return fallback;
  const n = Number(m[1]);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function allRows(): GraphRow[] {
  return Array.from(_apiRows.values()).flat().map((r) => r as GraphRow);
}

/** Execute pseudo-SQL over local cache for GraphRAG compatibility. */
export async function sql<T = Record<string, unknown>>(query: string): Promise<T[]> {
  if (!_ready) return [];
  const q = query.toLowerCase();
  const keywords = extractLikeKeywords(query);
  const limit = extractLimit(query, 50);

  if (q.includes(`join ${LOCAL_GRAPH_TABLE} e`) && q.includes(`join ${LOCAL_GRAPH_TABLE} t`)) {
    const vertices = allRows().filter((r) => String(r.record_type ?? 'vertex') === 'vertex');
    const edges = allRows().filter((r) => String(r.record_type ?? '') === 'edge');
    const out: GraphRow[] = [];
    for (const v of vertices) {
      if (keywords.length > 0 && !keywords.some((kw) => matchesKeyword(v, kw))) continue;
      for (const e of edges) {
        const vid = String(v.vertex_id ?? '');
        const src = String(e.src_vid ?? '');
        const dst = String(e.dst_vid ?? '');
        if (src !== vid && dst !== vid) continue;
        const neighborId = src === vid ? dst : src;
        const neighbor = vertices.find((n) => String(n.vertex_id ?? '') === neighborId);
        if (!neighbor) continue;
        out.push(neighbor);
        if (out.length >= limit) break;
      }
      if (out.length >= limit) break;
    }
    const dedup = new Map<string, GraphRow>();
    for (const row of out) dedup.set(String(row.vertex_id ?? row.edge_id ?? JSON.stringify(row)), row);
    return Array.from(dedup.values()).slice(0, limit) as T[];
  }

  const rows = allRows()
    .filter((r) => (keywords.length === 0 ? true : keywords.some((kw) => matchesKeyword(r, kw))))
    .sort((a, b) => String(b.updated_at ?? '').localeCompare(String(a.updated_at ?? '')))
    .slice(0, limit);
  return rows as T[];
}

/** Alias kept for compatibility. */
export async function icebergSql<T = Record<string, unknown>>(query: string): Promise<T[]> {
  return sql<T>(query);
}

export function isStale(label: string): boolean {
  const meta = labelMeta.get(label);
  if (!meta) return true;
  return Date.now() - meta.loadedAt > 300_000;
}

export async function syncLabel(label: string): Promise<number> {
  return loadLabel(label, labelMeta.get(label)?.rowCount ?? 10000);
}

export async function close(): Promise<void> {
  _ready = false;
  _error = '';
  labelMeta.clear();
  _apiRows.clear();
  _loadedLabels = [];
}
