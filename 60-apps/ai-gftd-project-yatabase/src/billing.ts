// billing.ts — Plan-state management (post-Stripe).
//
// Charter Rider §2 (ADR-2605192115) migration outcome:
//   - External fiat subscription via Stripe is prohibited.
//   - Upgrades happen through USDC donations on Base L2; see
//     `donate.ts` (POST /api/donate) and `webhook-usdc.ts`
//     (POST /webhook/usdc + ChartersComplianceRegistry attestation).
//   - The three legacy endpoint handlers exported from this file
//     (handleUpgrade / handlePortal / handleStripeWebhook) are kept
//     because /auth/v1/upgrade /auth/v1/portal /webhook/stripe must
//     still respond — they now return Charter Rider §2 rejections
//     so any historical caller (SDK / Studio v1) sees a clear error
//     instead of a 404.
//
// Plan-state persistence below is unchanged from the pre-migration
// design: KV is authoritative (per P63), with a best-effort RW
// insert via `@gftd/magatama-host-sdk` for downstream analytics.
//
// 適格請求書 (Japanese qualified invoice, T9007028460042) generation
// remains deferred to the P8.5 cron worker; tax-receipt issuance now
// keys off USDC donation events rather than Stripe invoices.

import type { PlanTier } from "./plan-quota";
import { PLAN_RULES } from "./plan-quota";
import { recordConversion } from "./referrer";

export interface BillingEnv {
  HYPERDRIVE?: unknown;
  YATA_VERSION?: string;
  YATABASE_AUTH_CACHE?: KVNamespace; // also used as plan-state KV (P63)
}

// ─── KV-backed plan state ───────────────────────────────────────────
// After ADR-2605111200 the Worker no longer touches Hyperdrive directly;
// we cache the active plan per org in the same KV namespace used for
// auth resolution. Reads check KV first, fall back to the legacy RW
// path if available.

function kvPlanKey(orgDid: string): string {
  return `plan:v1:${orgDid}`;
}

async function kvPutPlan(
  env: BillingEnv,
  orgDid: string,
  plan: PlanTier,
  source: PlanUpdateSource,
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return;
  const body = JSON.stringify({
    plan,
    source,
    startedAt: new Date().toISOString(),
  });
  try {
    await kv.put(kvPlanKey(orgDid), body); // no TTL — plan state persists
    console.log(`[yatabase][plan] KV PUT orgDid=${orgDid} plan=${plan} source=${source}`);
  } catch (e) {
    console.warn("[yatabase][plan] KV put failed:", e);
  }
}

async function kvGetPlan(env: BillingEnv, orgDid: string): Promise<PlanTier | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const raw = await kv.get(kvPlanKey(orgDid));
    if (!raw) return null;
    const data = JSON.parse(raw) as { plan?: string };
    const tier = data?.plan;
    if (typeof tier !== "string") return null;
    if (["free", "starter", "developer", "business", "enterprise"].includes(tier)) {
      return tier as PlanTier;
    }
    return null;
  } catch {
    return null;
  }
}

interface AnyKyselyDb {
  insertInto(table: string): {
    values(row: Record<string, unknown>): { execute(): Promise<unknown> };
  };
  selectFrom(table: string): unknown;
}

async function getDb(env: BillingEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

// `source` enumerates the workflow that triggered the plan write.
// `usdc-webhook` replaces the v0.1 `stripe-webhook` source after the
// Charter Rider §2 cutover.
export type PlanUpdateSource =
  | "stub-upgrade"
  | "usdc-webhook"
  | "signup-default";

export async function persistPlan(
  env: BillingEnv,
  orgDid: string,
  plan: PlanTier,
  source: PlanUpdateSource,
): Promise<void> {
  // P63: KV is the authoritative store while RW writes are degraded.
  // The legacy RW INSERT (vertex_org_plan) is best-effort — when
  // createKyselyDb throws (ADR-2605111200) we still flip the plan in KV
  // so the customer journey sees the correct tier on /api/plan.
  await kvPutPlan(env, orgDid, plan, source);
  try {
    const db = await getDb(env);
    if (!db) return; // KV-only mode (RW unavailable) — return without throwing
    const now = Date.now();
    const nowIso = new Date(now).toISOString();
    const rules = PLAN_RULES[plan];
    const vertexId = `at://did:web:billing.etzhayyim.com/ai.gftd.apps.billing.org_plan/${encodeURIComponent(orgDid)}-${now}`;
    await db.insertInto("vertex_org_plan").values({
      vertex_id: vertexId,
      org_did: orgDid,
      plan_tier: plan,
      started_at: nowIso,
      source,
      monthly_jpy_micro: rules.monthlyJpy * 1_000_000,
      status: "active",
      created_at: nowIso,
    }).execute();
  } catch (e) {
    // RW write failed but KV is authoritative — log and continue.
    console.warn("[yatabase][plan] RW persist best-effort failed (KV is authoritative):", e);
  }
}

/**
 * Look up the most recent `vertex_org_plan` row for an org. Returns null
 * when no row exists (caller falls back to `inferPlan(orgDid)`).
 */
export async function getPersistedPlan(env: BillingEnv, orgDid: string): Promise<PlanTier | null> {
  // P63: check KV first (authoritative while RW is degraded). Fall back
  // to the legacy RW read if KV miss.
  const kvPlan = await kvGetPlan(env, orgDid);
  if (kvPlan) return kvPlan;

  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    return null;
  }
  if (!sqlTag) return null;
  const db = await getDb(env);
  if (!db) return null;
  const q = sqlTag`
    SELECT plan_tier
    FROM vertex_org_plan
    WHERE org_did = ${orgDid} AND status = 'active'
    ORDER BY started_at DESC
    LIMIT 1
  `;
  try {
    const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
    const result = await exec.call(q, db);
    const row = result.rows?.[0];
    const tier = row?.plan_tier;
    if (typeof tier !== "string") return null;
    if (["free", "starter", "developer", "business", "enterprise"].includes(tier)) {
      return tier as PlanTier;
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Charter Rider §2 disabled-endpoint handlers ────────────────────
// These are kept so the routes /auth/v1/upgrade /auth/v1/portal
// /webhook/stripe respond with a clear Charter Rider §2 explanation
// instead of a 404. New callers must use /api/donate (donate.ts) or
// /webhook/usdc (webhook-usdc.ts).

interface UpgradeRequestBody {
  plan?: string;
  successUrl?: string;
  cancelUrl?: string;
}

const ALLOWED_TARGETS: PlanTier[] = ["free", "starter", "developer", "business"];
const CHARTER_RIDER_URL =
  "https://github.com/etzhayyim/root/blob/main/CHARTER-RIDER.md#section-2-prohibited-payment-purposes";

/**
 * POST /auth/v1/upgrade — plan-change entry point.
 *
 * Free-tier downgrade is permitted and persists immediately. Paid-tier
 * upgrades are no longer reachable via this endpoint: the SDK / Studio
 * must drive a USDC donation through /api/donate (handle in
 * `donate.ts`); the webhook-usdc receipt flips the plan asynchronously.
 *
 * Per ADR-2605192115 §3.
 */
export async function handleUpgrade(
  env: BillingEnv,
  orgDid: string,
  req: Request,
): Promise<Response> {
  let body: UpgradeRequestBody = {};
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: "BadRequest", message: "request body must be JSON" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  const target = (body.plan ?? "").toLowerCase().trim();
  if (!ALLOWED_TARGETS.includes(target as PlanTier)) {
    return new Response(
      JSON.stringify({
        error: "InvalidPlan",
        message: `Allowed: ${ALLOWED_TARGETS.join(", ")}. Enterprise tier is sales-only.`,
      }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  const plan = target as PlanTier;

  if (plan === "free") {
    try {
      await persistPlan(env, orgDid, "free", "stub-upgrade");
    } catch (e) {
      return new Response(
        JSON.stringify({
          error: "PersistFailed",
          message: e instanceof Error ? e.message.slice(0, 300) : "INSERT failed",
        }),
        { status: 500, headers: { "content-type": "application/json" } },
      );
    }
    // P88 conversion attribution (kept; non-monetary signal).
    try { await recordConversion(env as never, orgDid, "downgrade-free"); } catch { /* best-effort */ }
    return new Response(
      JSON.stringify({ ok: true, plan, mode: "free-downgrade", message: "Downgraded to Free." }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }

  return new Response(
    JSON.stringify({
      error: "external-fiat-not-permitted",
      code: "CHARTER_RIDER_SECTION_2",
      message:
        "Paid plan upgrades via fiat subscription are prohibited per Charter Rider §2. " +
        "Use POST /api/donate with purpose='internal-subscription' (SBT-bound) or " +
        "purpose='donation' (unrestricted) on Base L2 USDC.",
      donateEndpoint: "/api/donate",
      learnMore: CHARTER_RIDER_URL,
    }),
    { status: 403, headers: { "content-type": "application/json" } },
  );
}

/**
 * POST /auth/v1/portal — Stripe Customer Portal session (P71).
 *
 * Per ADR-2605192115 §3 this endpoint is permanently disabled.
 * Returns 410 Gone with a pointer to /api/donate.
 */
export async function handlePortal(
  _env: BillingEnv,
  _orgDid: string,
  _req: Request,
): Promise<Response> {
  return new Response(
    JSON.stringify({
      error: "external-fiat-not-permitted",
      code: "CHARTER_RIDER_SECTION_2",
      message:
        "Stripe Customer Portal is permanently disabled. External fiat payment is " +
        "prohibited per Charter Rider §2. Manage USDC donations through /api/donate.",
      donateEndpoint: "/api/donate",
      learnMore: CHARTER_RIDER_URL,
    }),
    { status: 410, headers: { "content-type": "application/json" } },
  );
}

/**
 * POST /webhook/stripe — legacy Stripe webhook surface.
 *
 * Permanently disabled per ADR-2605192115 §3. Returns 410 Gone so
 * Stripe stops retrying. New donation acknowledgements arrive via
 * POST /webhook/usdc (see `webhook-usdc.ts`).
 */
export async function handleStripeWebhook(_env: BillingEnv, req: Request): Promise<Response> {
  const raw = await req.text().catch(() => "");
  console.log(
    "[yatabase][stripe-webhook] REJECTED per Charter Rider §2: external-fiat-not-permitted",
    { contentLength: raw.length, timestamp: new Date().toISOString() },
  );
  return new Response(
    JSON.stringify({
      error: "external-fiat-not-permitted",
      code: "CHARTER_RIDER_SECTION_2",
      message:
        "POST /webhook/stripe is permanently disabled. USDC donation receipts arrive " +
        "via POST /webhook/usdc (ChartersComplianceRegistry attestation).",
      replacementEndpoint: "/webhook/usdc",
      learnMore: CHARTER_RIDER_URL,
    }),
    { status: 410, headers: { "content-type": "application/json" } },
  );
}
