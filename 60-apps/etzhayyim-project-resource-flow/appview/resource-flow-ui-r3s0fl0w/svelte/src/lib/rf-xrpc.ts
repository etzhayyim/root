// resource-flow XRPC client. Hits atproto.etzhayyim.com (PDS pipethrough →
// resource-flow Worker) by default, falls back to same-origin when the
// page is served from resource-flow.etzhayyim.com itself.

const DEFAULT_SERVICE = 'https://atproto.etzhayyim.com';

function service(): string {
  if (typeof window !== 'undefined') {
    const override = (window as any).__RF_SERVICE__;
    if (typeof override === 'string' && override) return override;
    const isLocalhost =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';
    if (!isLocalhost && window.location.origin.endsWith('etzhayyim.com')) {
      return window.location.origin;
    }
  }
  return DEFAULT_SERVICE;
}

async function xrpcQuery<T = unknown>(
  nsid: string,
  params: Record<string, string | number | undefined> = {},
): Promise<T> {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const url = `${service()}/xrpc/${nsid}${sp.toString() ? `?${sp}` : ''}`;
  const resp = await fetch(url, { headers: { accept: 'application/json' } });
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`${nsid} ${resp.status}: ${text}`);
  }
  return (await resp.json()) as T;
}

// ── Types ──

export type FlowClass = 'currency' | 'service' | 'personnel';

export interface SankeyEdge {
  source_did: string;
  counterparty_did: string;
  source_facade_did?: string;
  counterparty_facade_did?: string;
  fiscal_period: string;
  industry_code: string;
  amount_sum?: number;
  amount_bucket?: string;
  currency?: string;
  service_class?: string;
  service_unit?: string;
  total_count?: number;
  revenue_sum?: number;
  flow_type?: string;
  headcount_sum?: number;
  event_count: number;
}

export interface SankeyResponse {
  flowClass: FlowClass;
  edges: SankeyEdge[];
  nodes: { id: string }[];
}

export function getSankey(params: {
  flowClass: FlowClass;
  domain?: string;
  industryCode?: string;
  sourceDid?: string;
  fiscalPeriod?: string;
  limit?: number;
}) {
  return xrpcQuery<SankeyResponse>(
    'com.etzhayyim.apps.resourceFlow.getSankey',
    params as Record<string, string | number | undefined>,
  );
}

export function listFlows(params: {
  flowClass: FlowClass;
  sourceDid?: string;
  fiscalPeriod?: string;
  limit?: number;
  offset?: number;
}) {
  return xrpcQuery<{ flowClass: FlowClass; flows: any[]; total: number; offset: number; limit: number }>(
    'com.etzhayyim.apps.resourceFlow.listFlows',
    params as Record<string, string | number | undefined>,
  );
}

export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Anomaly {
  vertex_id: string;
  anomaly_id: string;
  flow_class: FlowClass;
  source_did: string;
  counterparty_did: string | null;
  fiscal_period: string;
  industry_code: string | null;
  currency: string | null;
  service_class: string | null;
  observed_value: number;
  baseline_avg: number;
  baseline_window_days: number;
  baseline_sample_count: number;
  threshold_factor: number;
  severity: AnomalySeverity;
  observed_at: string;
  detection_run_id: string;
  post_uri: string | null;
  // Phase 16' — joined from mv_resource_flow_anomaly_review_latest.
  review_count?: number | null;
  last_reviewed_at?: string | null;
  last_action?: AnomalyAction | null;
  last_reviewer_did?: string | null;
  last_thread_post_uri?: string | null;
}

export type AnomalyReviewedFilter = 'open' | 'closed' | 'any';

export type AnomalyAction = 'acknowledge' | 'dismiss' | 'escalate';

export interface ReviewAnomalyOutput {
  reviewId: string;
  anomalyId: string;
  action: AnomalyAction;
  vertexId: string;
  threadUri?: string;
}

export async function reviewAnomaly(
  input: { anomalyId: string; action: AnomalyAction; reason?: string; post?: boolean },
  bearer?: string,
): Promise<ReviewAnomalyOutput> {
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  if (bearer) headers.authorization = `Bearer ${bearer}`;
  const resp = await fetch(`${service()}/xrpc/com.etzhayyim.apps.resourceFlow.reviewAnomaly`, {
    method: 'POST',
    headers,
    body: JSON.stringify(input),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`reviewAnomaly ${resp.status}: ${text}`);
  }
  return (await resp.json()) as ReviewAnomalyOutput;
}

export function listAnomalies(params: {
  flowClass?: FlowClass;
  severity?: AnomalySeverity;
  sourceDid?: string;
  fiscalPeriod?: string;
  since?: string;
  reviewed?: AnomalyReviewedFilter;
  limit?: number;
  offset?: number;
} = {}) {
  return xrpcQuery<{
    anomalies: Anomaly[];
    total: number;
    offset: number;
    limit: number;
    reviewed?: AnomalyReviewedFilter;
  }>(
    'com.etzhayyim.apps.resourceFlow.listAnomalies',
    params as Record<string, string | number | undefined>,
  );
}

// ── Actor label resolution (ADR-0074) ──
//
// Single round-trip via com.etzhayyim.apps.resourceFlow.getActorLabels which
// reads view_resource_flow_actor_label (vertex_profile + edge_erc725_facade_did).
// Resolves both facade DIDs (did:web / did:plc) and ERC725 root DIDs to the
// same display_name row. Falls back to per-DID app.bsky.actor.getProfile
// when the bulk endpoint is unavailable (e.g. dev server, auth-gated).

export interface ActorLabel {
  did: string;
  kind?: 'facade' | 'root';
  facadeDid?: string;
  rootDid?: string;
  handle?: string;
  displayName?: string;
  description?: string;
  rootIdentityAddr?: string;
}

const labelCache = new Map<string, ActorLabel | null>();

async function getActorLabels(dids: string[]): Promise<ActorLabel[]> {
  if (dids.length === 0) return [];
  // XRPC array params: repeated `?dids=...&dids=...` is the AT convention.
  const sp = new URLSearchParams();
  for (const d of dids) sp.append('dids', d);
  const url = `${service()}/xrpc/com.etzhayyim.apps.resourceFlow.getActorLabels?${sp}`;
  const resp = await fetch(url, { headers: { accept: 'application/json' } });
  if (!resp.ok) {
    throw new Error(`getActorLabels ${resp.status}`);
  }
  const json = (await resp.json()) as { labels?: ActorLabel[] };
  return json.labels ?? [];
}

export async function resolveProfiles(dids: string[]): Promise<Record<string, ActorLabel | null>> {
  const out: Record<string, ActorLabel | null> = {};
  const todo: string[] = [];
  for (const d of dids) {
    if (!d) continue;
    if (labelCache.has(d)) {
      out[d] = labelCache.get(d) ?? null;
    } else {
      todo.push(d);
    }
  }
  if (todo.length === 0) return out;
  try {
    const labels = await getActorLabels(todo);
    const byDid = new Map(labels.map((l) => [l.did, l]));
    for (const d of todo) {
      const l = byDid.get(d) ?? null;
      labelCache.set(d, l);
      out[d] = l;
    }
  } catch {
    // Fallback: per-DID app.bsky.actor.getProfile.
    await Promise.all(
      todo.map(async (d) => {
        try {
          const p = await xrpcQuery<any>('app.bsky.actor.getProfile', { actor: d });
          const lite: ActorLabel = {
            did:         d,
            kind:        'facade',
            facadeDid:   d,
            handle:      p?.handle,
            displayName: p?.displayName,
            description: p?.description,
          };
          labelCache.set(d, lite);
          out[d] = lite;
        } catch {
          labelCache.set(d, null);
          out[d] = null;
        }
      }),
    );
  }
  return out;
}

// Backwards-compat single-DID resolver used by older call sites.
export async function resolveProfile(did: string): Promise<ActorLabel | null> {
  const map = await resolveProfiles([did]);
  return map[did] ?? null;
}

export function shortLabel(did: string): string {
  if (did === 'independent') return 'Independent';
  // ADR-0074: prefer ERC725 root display, but truncate long contract addrs.
  if (did.startsWith('did:erc725:')) {
    const tail = did.split(':').pop() ?? '';
    return `erc725:${tail.slice(0, 8)}…`;
  }
  if (did.startsWith('did:web:')) {
    return did.slice('did:web:'.length).split(':').slice(0, 4).join(':');
  }
  return did.length > 32 ? did.slice(0, 32) + '…' : did;
}
