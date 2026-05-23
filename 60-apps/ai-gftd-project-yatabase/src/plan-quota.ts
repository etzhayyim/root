// plan-quota.ts — Plan tier inference + daily quota enforcement (P7).
//
// Each tenant is assigned a plan tier based on the orgDid pattern. The
// `yata-tenant.etzhayyim.com` namespace produced by /auth/v1/signup defaults
// to the Free tier; non-tenant DIDs (gftd internal CLI keys, enterprise
// onboarded customers) get Enterprise unlimited.
//
// Quota check sums today's `vertex_billing_event` rows per orgDid and
// blocks at 429 if the running total exceeds the plan limit.
// The result is cached in CF Cache API for 30s to avoid querying RW
// on every hot-path request — the cost is potentially up to ~30s of
// over-quota usage before the limit takes effect, which is fine for
// MVP economics.

export type PlanTier = "free" | "starter" | "developer" | "business" | "enterprise";

export interface PlanRules {
  apiRequestPerDay: number | null;  // null = unlimited
  storageGbCap: number | null;
  cypherCuMsPerDay: number | null;
  mvSlots: number | null;           // deploy-first query MV count cap (ADR-2605210000)
  monthlyUsd: number;          // primary list price (US market lead)
  monthlyJpy: number;          // secondary display, uses FX_JPY_PER_USD
}

// FX snapshot from root deps.toml `[platform.market] fx_jpy_per_usd`.
// Refreshed monthly via the billing pool cron.
export const FX_JPY_PER_USD = 150;

function jpyFromUsd(usd: number): number {
  return Math.round(usd * FX_JPY_PER_USD);
}

// US-primary pricing (deps.toml [platform.products.yatabase]).
// USD list aligned to graphdb / BaaS competitive bench:
//   Neo4j AuraDB Free $0, Pro $65/mo
//   Supabase Free $0, Pro $25/mo
// Aggressive entry tier ($13 Starter) undercuts Supabase by 50%; bands
// scale 2.5× through Developer ($33) → Business ($650) → Enterprise floor.
export const PLAN_RULES: Record<PlanTier, PlanRules> = {
  free: {
    apiRequestPerDay: 1_000,
    storageGbCap: 5,
    cypherCuMsPerDay: 5 * 60 * 60 * 1000,    // 5 CU-hours
    mvSlots: 5,
    monthlyUsd: 0,
    monthlyJpy: 0,
  },
  starter: {
    apiRequestPerDay: 33_333,                // 1M/mo amortized
    storageGbCap: 50,
    cypherCuMsPerDay: 50 * 60 * 60 * 1000,
    mvSlots: 20,
    monthlyUsd: 13,
    monthlyJpy: jpyFromUsd(13),              // ~¥1,950 at 150 JPY/USD
  },
  developer: {
    apiRequestPerDay: 333_333,               // 10M/mo
    storageGbCap: 500,
    cypherCuMsPerDay: 500 * 60 * 60 * 1000,
    mvSlots: 100,
    monthlyUsd: 33,
    monthlyJpy: jpyFromUsd(33),              // ~¥4,950
  },
  business: {
    apiRequestPerDay: 33_333_333,            // 1B/mo
    storageGbCap: 5000,
    cypherCuMsPerDay: 5000 * 60 * 60 * 1000,
    mvSlots: null,                           // unlimited
    monthlyUsd: 650,
    monthlyJpy: jpyFromUsd(650),             // ~¥97,500
  },
  enterprise: {
    apiRequestPerDay: null,
    storageGbCap: null,
    cypherCuMsPerDay: null,
    mvSlots: null,                           // unlimited
    monthlyUsd: 6700,                        // floor; sales-negotiated
    monthlyJpy: jpyFromUsd(6700),            // ~¥1,005,000
  },
};

export interface PlanQuotaEnv {
  HYPERDRIVE?: unknown;
}

/**
 * Pick a plan tier from the orgDid alone. The signup flow always mints
 * `yata-tenant.etzhayyim.com` DIDs so freshly-signed-up tenants start on Free.
 * Non-tenant DIDs (e.g. gftd CLI internal keys, enterprise customers
 * onboarded out-of-band) bypass the quota.
 */
export function inferPlan(orgDid: string): PlanTier {
  if (!orgDid) return "free";
  if (/yata-tenant\.gftd\.ai$/.test(orgDid)) return "free";
  return "enterprise";
}

/**
 * Resolve the effective plan tier for an org. P8: prefers a persisted
 * `vertex_org_plan` row (set by the USDC webhook on donation confirm or
 * by the free-tier downgrade path); falls back to `inferPlan(orgDid)`
 * when no persisted plan exists.
 *
 * Charter Rider §2 (ADR-2605192115): the legacy `billing-stripe` module
 * was renamed to `billing` as part of the Stripe→USDC cutover. This
 * function unconditionally targets the new module.
 */
export async function resolvePlan(env: PlanQuotaEnv, orgDid: string): Promise<PlanTier> {
  try {
    const sdk = await import("./billing");
    const persisted = await sdk.getPersistedPlan(env, orgDid);
    if (persisted) return persisted;
  } catch {
    /* fall through to default */
  }
  return inferPlan(orgDid);
}

interface AnyKyselyDb {
  selectFrom(table: string): unknown;
}

async function getDb(env: PlanQuotaEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

export interface QuotaStatus {
  plan: PlanTier;
  apiRequestPerDay: number | null;
  apiRequestUsedToday: number;
  apiRequestRemaining: number | null;
  exceeded: boolean;
  windowStart: string;
}

/**
 * Sum today's `api_request` qty for the org, bypassing the cache. Returns
 * 0 on RW failure — fail-open is intentional so a billing-event-side
 * outage doesn't lock customers out.
 */
async function fetchDailyApiCount(env: PlanQuotaEnv, orgDid: string): Promise<number> {
  // P66: try KV-mirrored counter first (P63 emitMeter writes here too).
  // Falls back to RW direct only when KV miss + Hyperdrive available.
  const kv = (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  if (kv) {
    try {
      const today = new Date().toISOString().slice(0, 10);
      const raw = await kv.get(`usage:v1:${orgDid}:api_request:${today}`);
      if (raw) {
        const v = JSON.parse(raw) as { qty?: number };
        const q = Number(v?.qty ?? 0);
        if (Number.isFinite(q)) return q;
      }
    } catch (e) {
      console.warn("[yatabase][quota] KV read failed:", e);
    }
  }

  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    return 0;
  }
  if (!sqlTag) return 0;
  const db = await getDb(env);
  if (!db) return 0;

  const startMs = startOfTodayMs();
  const q = sqlTag`
    SELECT COALESCE(SUM(qty), 0) AS total
    FROM vertex_billing_event
    WHERE org_did = ${orgDid}
      AND metric = 'api_request'
      AND ts_ms >= ${startMs}
  `;
  try {
    const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    const total = Number(result.rows?.[0]?.total ?? 0);
    return Number.isFinite(total) ? total : 0;
  } catch (e) {
    console.warn("[yatabase][quota] daily count failed:", e);
    return 0;
  }
}

function startOfTodayMs(): number {
  const d = new Date();
  d.setUTCHours(0, 0, 0, 0);
  return d.getTime();
}

/**
 * Compute current quota status. Caches the daily count for 30 s in CF
 * Cache API; the cache lifetime is short enough to bound over-quota
 * leakage but long enough to amortize the SUM query cost.
 */
export async function getQuotaStatus(env: PlanQuotaEnv, orgDid: string): Promise<QuotaStatus> {
  const plan = await resolvePlan(env, orgDid);
  const rules = PLAN_RULES[plan];
  const limit = rules.apiRequestPerDay;
  const windowStart = new Date(startOfTodayMs()).toISOString();

  if (limit === null) {
    return {
      plan,
      apiRequestPerDay: null,
      apiRequestUsedToday: 0,
      apiRequestRemaining: null,
      exceeded: false,
      windowStart,
    };
  }

  let used = 0;
  const cacheKey = new Request(`https://cache-yatabase.etzhayyim.com/quota/${encodeURIComponent(orgDid)}`);
  const cache = (caches as unknown as { default?: Cache }).default;
  if (cache) {
    const cached = await cache.match(cacheKey);
    if (cached) {
      try {
        const body = await cached.json() as { used?: number };
        used = Number(body?.used ?? 0);
      } catch {
        used = 0;
      }
    } else {
      used = await fetchDailyApiCount(env, orgDid);
      await cache.put(
        cacheKey,
        new Response(JSON.stringify({ used }), {
          status: 200,
          headers: {
            "content-type": "application/json",
            "cache-control": "max-age=30",
          },
        }),
      );
    }
  } else {
    used = await fetchDailyApiCount(env, orgDid);
  }

  return {
    plan,
    apiRequestPerDay: limit,
    apiRequestUsedToday: used,
    apiRequestRemaining: Math.max(0, limit - used),
    exceeded: used >= limit,
  windowStart,
  };
}

/**
 * Build a 429 response carrying a Retry-After header pointing to the
 * next UTC midnight (when the quota window rolls over).
 */
export function quotaExceededResponse(status: QuotaStatus): Response {
  const tomorrow = new Date(startOfTodayMs() + 24 * 60 * 60 * 1000);
  const retryAfterSec = Math.max(1, Math.floor((tomorrow.getTime() - Date.now()) / 1000));
  return new Response(
    JSON.stringify({
      error: "QuotaExceeded",
      plan: status.plan,
      apiRequestPerDay: status.apiRequestPerDay,
      apiRequestUsedToday: status.apiRequestUsedToday,
      windowStart: status.windowStart,
      message: `Daily ${status.plan} plan limit (${status.apiRequestPerDay} api_request) exceeded. Retry after ${tomorrow.toISOString()} UTC, or upgrade your plan.`,
    }),
    {
      status: 429,
      headers: {
        "content-type": "application/json",
        "retry-after": String(retryAfterSec),
        "x-yatabase-plan": status.plan,
        "x-yatabase-quota-limit": String(status.apiRequestPerDay),
        "x-yatabase-quota-used": String(status.apiRequestUsedToday),
      },
    },
  );
}
