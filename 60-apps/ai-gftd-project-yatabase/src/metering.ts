// metering.ts — fire-and-forget billing event emission.
//
// emitMeter() is called in executionCtx.waitUntil() so it never blocks
// the customer response. Two paths run in parallel:
//   1. KV bump — fast counter for /api/usage, survives RW outages
//   2. Pod XRPC — writes vertex_billing_event + vertex_api_key growth columns
//      via the lg-yatabase pod (Worker cannot touch RisingWave per ADR-2605111200)

export type MeterMetric =
  | "api_request"
  | "yata_query_cu_ms"
  | "storage_gb_hour"
  | "egress_gb"
  | "mcp_call"
  | "did_mint";

export interface MeterEvent {
  orgDid: string;
  actorDid?: string;
  metric: MeterMetric;
  qty: number;
  product?: "yata" | "obj" | "platform";
  refResource?: string;
}

export interface MeterEnv {
  HYPERDRIVE?: unknown;
  etzhayyim_METERING_DISABLED?: string;
  YATABASE_AUTH_CACHE?: KVNamespace; // P63: KV mirror of meter counters
  LG_YATABASE_URL?: string;          // direct pod URL for meterEvent XRPC
  DISPATCHER_INTERNAL_SECRET?: string;
}

// P63: KV-mirrored per-metric counters. Each emitMeter() bumps an integer
// counter keyed `usage:v1:{orgDid}:{metric}:{YYYY-MM-DD}` so /api/usage can
// serve a non-zero summary even when Hyperdrive direct writes are blocked
// by ADR-2605111200. The pod-side /xrpc/yata.meter migration will provide
// the durable rollup later.
async function kvBumpUsage(env: MeterEnv, event: MeterEvent): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return;
  const today = new Date().toISOString().slice(0, 10);
  const key = `usage:v1:${event.orgDid}:${event.metric}:${today}`;
  try {
    const prev = await kv.get(key);
    const cur = prev ? JSON.parse(prev) as { qty: number; events: number } : { qty: 0, events: 0 };
    cur.qty += event.qty;
    cur.events += 1;
    await kv.put(key, JSON.stringify(cur), { expirationTtl: 86400 * 35 });
  } catch (e) {
    console.warn("[yatabase][meter] KV bump failed:", e);
  }
}

// JPY-micro rate card per metric (= ¥/unit × 1_000_000). Aligned with
// ADR-2605080000 §D1 list price column. Storage is per GB-month so we
// translate to per GB-second internally; the rollup MV owns aggregation.
const RATE_CARD_JPY_MICRO: Record<MeterMetric, number> = {
  api_request: 200,                 // ¥2.0 / 10K req → ¥0.0002 / req → 200 µJPY
  yata_query_cu_ms: 83,             // ¥300 / CU-hour → 83 µJPY / CU-ms
  storage_gb_hour: 13_889,          // ¥10 / GB-month / (30*24h) → 13_889 µJPY / GB-h
  egress_gb: 15_000_000,            // ¥15 / GB → 15M µJPY / GB
  mcp_call: 30_000,                 // ¥3.0 / 100 calls → 30_000 µJPY / call
  did_mint: 300_000_000,            // ¥300 / mint → 300M µJPY
};

/** Compute the un-discounted billed amount for a single event. */
function listPrice(metric: MeterMetric, qty: number): number {
  const unit = RATE_CARD_JPY_MICRO[metric] ?? 0;
  return Math.round(unit * qty);
}

async function podMeterEvent(env: MeterEnv, event: MeterEvent): Promise<void> {
  const base = env.LG_YATABASE_URL;
  if (!base) return;
  const url = `${base.replace(/\/+$/, "")}/xrpc/com.etzhayyim.apps.yata.meterEvent`;
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (env.DISPATCHER_INTERNAL_SECRET) {
    headers["x-internal-trust"] = env.DISPATCHER_INTERNAL_SECRET;
  }
  try {
    await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        orgDid: event.orgDid,
        metric: event.metric,
        qty: event.qty,
        refResource: event.refResource ?? "",
      }),
    });
  } catch (e) {
    console.warn("[yatabase][meter] pod meterEvent failed:", e);
  }
}

export async function emitMeter(env: MeterEnv, event: MeterEvent): Promise<void> {
  if (env.etzhayyim_METERING_DISABLED === "1") return;
  if (!event.orgDid || event.qty < 0) return;
  // Always bump KV counter — survives RW outages so /api/usage stays non-zero.
  await kvBumpUsage(env, event);
  // Forward to pod so vertex_billing_event and vertex_api_key growth columns
  // receive the event (Worker cannot write RisingWave per ADR-2605111200).
  await podMeterEvent(env, event);
}

// ── Usage summary readback ──

export interface UsageSummary {
  orgDid: string;
  windowStart: string;
  windowEnd: string;
  byMetric: Array<{
    metric: string;
    totalQty: number;
    totalBilledJpyMicro: number;
    eventCount: number;
  }>;
  totalBilledJpy: number;
}

// P63: KV-only readback when Hyperdrive direct queries are unavailable.
async function readUsageFromKv(env: MeterEnv, orgDid: string): Promise<UsageSummary | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  const nowMs = Date.now();
  const startMs = nowMs - 24 * 60 * 60 * 1000;
  const todayKey = new Date(nowMs).toISOString().slice(0, 10);
  const yesterdayKey = new Date(nowMs - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const metrics: MeterMetric[] = ["api_request", "yata_query_cu_ms", "storage_gb_hour", "egress_gb", "mcp_call", "did_mint"];
  const byMetric: UsageSummary["byMetric"] = [];
  let totalMicro = 0;
  for (const metric of metrics) {
    let qty = 0;
    let events = 0;
    for (const day of [todayKey, yesterdayKey]) {
      const raw = await kv.get(`usage:v1:${orgDid}:${metric}:${day}`);
      if (raw) {
        try {
          const v = JSON.parse(raw) as { qty?: number; events?: number };
          qty += Number(v.qty ?? 0);
          events += Number(v.events ?? 0);
        } catch { /* ignore */ }
      }
    }
    if (qty > 0 || events > 0) {
      const billed = listPrice(metric, qty);
      totalMicro += billed;
      byMetric.push({
        metric,
        totalQty: qty,
        totalBilledJpyMicro: billed,
        eventCount: events,
      });
    }
  }
  return {
    orgDid,
    windowStart: new Date(startMs).toISOString(),
    windowEnd: new Date(nowMs).toISOString(),
    byMetric,
    totalBilledJpy: Math.round(totalMicro / 1_000_000),
  };
}

export async function getUsageLast24h(env: MeterEnv, orgDid: string): Promise<UsageSummary | null> {
  return readUsageFromKv(env, orgDid);
}
