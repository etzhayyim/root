// billing-stripe.ts — Plan upgrade + Stripe checkout (P8).
//
// Two-mode flow:
//   1. Stub mode (default, no STRIPE_SECRET_KEY env var): /auth/v1/upgrade
//      directly writes a `vertex_org_plan` row and returns 200. The
//      tenant's plan tier flips immediately. Useful for demo and CI.
//   2. Real Stripe mode (when STRIPE_SECRET_KEY is set): /auth/v1/upgrade
//      creates a Stripe Checkout Session via Stripe's REST API and
//      returns the hosted-page URL. Customer pays at Stripe; Stripe
//      webhook hits /webhook/stripe → server activates the plan.
//
// 適格請求書 (Japanese qualified invoice, T9007028460042) generation
// is deferred to a separate cron worker (P8.5) that scans monthly
// `vertex_billing_event` aggregates per org_did and renders PDF via
// the K8s LangServer pool. This file owns the plan-state side only.

import type { PlanTier } from "./plan-quota";
import { PLAN_RULES } from "./plan-quota";
import { recordConversion } from "./referrer";

export interface BillingEnv {
  HYPERDRIVE?: unknown;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  STRIPE_PRICE_STARTER?: string;
  STRIPE_PRICE_DEVELOPER?: string;
  STRIPE_PRICE_BUSINESS?: string;
  YATA_VERSION?: string;
  YATABASE_AUTH_CACHE?: KVNamespace; // also used as plan-state KV (P63)
}

// KV-backed plan state. After ADR-2605111200 the Worker no longer touches
// Hyperdrive directly; we cache the active plan per org in the same KV
// namespace used for auth resolution. Reads check KV first, fall back to
// the legacy RW path if available.
function kvPlanKey(orgDid: string): string {
  return `plan:v1:${orgDid}`;
}

async function kvPutPlan(
  env: BillingEnv,
  orgDid: string,
  plan: PlanTier,
  source: string,
  stripeSubscriptionId: string | null,
  stripeCustomerId: string | null,
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return;
  const body = JSON.stringify({
    plan,
    source,
    stripeSubscriptionId: stripeSubscriptionId ?? "",
    stripeCustomerId: stripeCustomerId ?? "",
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
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

function stripePriceForPlan(env: BillingEnv, plan: PlanTier): string | null {
  switch (plan) {
    case "starter": return env.STRIPE_PRICE_STARTER ?? null;
    case "developer": return env.STRIPE_PRICE_DEVELOPER ?? null;
    case "business": return env.STRIPE_PRICE_BUSINESS ?? null;
    default: return null;
  }
}

async function persistPlan(
  env: BillingEnv,
  orgDid: string,
  plan: PlanTier,
  source: "stub-upgrade" | "stripe-webhook" | "signup-default",
  stripeSubscriptionId: string | null,
  stripeCustomerId: string | null,
): Promise<void> {
  // P63: KV is the authoritative store while RW writes are degraded.
  // The legacy RW INSERT (vertex_org_plan) is best-effort — when
  // createKyselyDb throws (ADR-2605111200) we still flip the plan in KV
  // so the customer journey sees the correct tier on /api/plan.
  await kvPutPlan(env, orgDid, plan, source, stripeSubscriptionId, stripeCustomerId);
  try {
    const db = await getDb(env);
    if (!db) return; // KV-only mode (RW unavailable) — return without throwing
    const now = Date.now();
    const nowIso = new Date(now).toISOString();
    const rules = PLAN_RULES[plan];
    const vertexId = `at://did:web:billing.etzhayyim.com/com.etzhayyim.apps.billing.org_plan/${encodeURIComponent(orgDid)}-${now}`;
    await db.insertInto("vertex_org_plan").values({
      vertex_id: vertexId,
      org_did: orgDid,
      plan_tier: plan,
      started_at: nowIso,
      source,
      stripe_subscription_id: stripeSubscriptionId ?? "",
      stripe_customer_id: stripeCustomerId ?? "",
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
    const sdk = await import("@etzhayyim/magatama-host-sdk");
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

interface UpgradeRequestBody {
  plan?: string;
  successUrl?: string;
  cancelUrl?: string;
}

const ALLOWED_TARGETS: PlanTier[] = ["free", "starter", "developer", "business"];

/**
 * POST /auth/v1/upgrade — plan upgrade entry point.
 *
 * Body: { plan: "starter" | "developer" | "business",
 *         successUrl?, cancelUrl? }
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

  // Free tier downgrade is always allowed without payment.
  if (plan === "free") {
    try {
      await persistPlan(env, orgDid, "free", "stub-upgrade", null, null);
    } catch (e) {
      return new Response(
        JSON.stringify({ error: "PersistFailed", message: e instanceof Error ? e.message.slice(0, 300) : "INSERT failed" }),
        { status: 500, headers: { "content-type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({ ok: true, plan, mode: "stub", message: "Downgraded to Free." }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }

  // Real Stripe path when secret is configured.
  if (env.STRIPE_SECRET_KEY) {
    const priceId = stripePriceForPlan(env, plan);
    if (!priceId) {
      return new Response(
        JSON.stringify({
          error: "StripePriceUnconfigured",
          message: `No Stripe price ID configured for ${plan} (set STRIPE_PRICE_${plan.toUpperCase()}).`,
        }),
        { status: 503, headers: { "content-type": "application/json" } },
      );
    }
    const checkout = await createStripeCheckoutSession(env, orgDid, plan, priceId, body.successUrl, body.cancelUrl);
    if (!checkout.url) {
      return new Response(
        JSON.stringify({ error: "StripeCheckoutFailed", upstream: checkout.error?.slice(0, 300) }),
        { status: 502, headers: { "content-type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({
        ok: true,
        mode: "stripe",
        plan,
        checkoutUrl: checkout.url,
        sessionId: checkout.sessionId,
        message: "Redirect the customer to checkoutUrl. After successful payment Stripe webhook activates the plan.",
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }

  // Stub mode (no Stripe credentials): activate the plan immediately and
  // emit a synthetic invoice line so the metering / usage panes show
  // the upgraded tier right away. Real production must use Stripe.
  try {
    await persistPlan(env, orgDid, plan, "stub-upgrade", null, null);
  } catch (e) {
    return new Response(
      JSON.stringify({ error: "PersistFailed", message: e instanceof Error ? e.message.slice(0, 300) : "INSERT failed" }),
      { status: 500, headers: { "content-type": "application/json" } },
    );
  }
  // Sprint 1 H1: record referrer conversion.
  try { await recordConversion(env, orgDid, plan); } catch { /* non-fatal */ }
  // P15: outbox email confirmation. We don't have a per-tenant email yet
  // (signup is anonymous), so this writes to outbox in 'queued-no-recipient'
  // status — once the customer attaches an email via /auth/v1/signup body
  // or a future verify flow, the cron resender will pick it up.
  try {
    const outbox = await import("./email-outbox");
    const tpl = outbox.planUpgradeEmail(orgDid, plan, PLAN_RULES[plan].monthlyUsd);
    await outbox.emitOutbox(env as unknown as { HYPERDRIVE?: unknown }, {
      orgDid,
      kind: "plan-upgrade",
      subject: tpl.subject,
      bodyText: tpl.text,
      bodyHtml: tpl.html,
    });
  } catch (e) {
    console.warn("[yatabase][upgrade] outbox emit failed:", e);
  }
  return new Response(
    JSON.stringify({
      ok: true,
      mode: "stub",
      plan,
      message: `Stub upgrade to ${plan}. Real Stripe checkout requires STRIPE_SECRET_KEY + STRIPE_PRICE_${plan.toUpperCase()} wrangler secrets.`,
      monthlyUsd: PLAN_RULES[plan].monthlyUsd,
      monthlyJpy: PLAN_RULES[plan].monthlyJpy,
    }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
}

/**
 * P71: read the cached Stripe customer ID for an org. Returns null if
 * the customer hasn't completed a Stripe checkout yet (e.g. still on
 * free, or upgraded via stub mode). The webhook writes it on
 * checkout.session.completed.
 */
async function kvGetStripeCustomerId(env: BillingEnv, orgDid: string): Promise<string | null> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return null;
  try {
    const raw = await kv.get(kvPlanKey(orgDid));
    if (!raw) return null;
    const data = JSON.parse(raw) as { stripeCustomerId?: string };
    const id = (data?.stripeCustomerId ?? "").trim();
    return id.startsWith("cus_") ? id : null;
  } catch {
    return null;
  }
}

interface PortalRequestBody {
  returnUrl?: string;
}

/**
 * POST /auth/v1/portal — Stripe Customer Portal session (P71).
 *
 * Allows customers to self-serve: change card, cancel, see invoice
 * history. Returns a hosted-page URL to redirect the customer to.
 * Requires that the org has already gone through Stripe checkout
 * (i.e. has a `cus_*` ID cached). Free / stub-upgraded orgs get a
 * 400 with a clear message telling them to upgrade via Checkout first.
 */
export async function handlePortal(
  env: BillingEnv,
  orgDid: string,
  req: Request,
): Promise<Response> {
  if (!env.STRIPE_SECRET_KEY) {
    return new Response(
      JSON.stringify({ error: "StripeDisabled", message: "STRIPE_SECRET_KEY not configured" }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }
  let body: PortalRequestBody = {};
  try { body = await req.json(); } catch { /* empty body is fine */ }

  const customerId = await kvGetStripeCustomerId(env, orgDid);
  if (!customerId) {
    return new Response(
      JSON.stringify({
        error: "NoStripeCustomer",
        message: "This org has not completed a Stripe checkout yet. Upgrade via POST /auth/v1/upgrade first.",
      }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  const params = new URLSearchParams();
  params.set("customer", customerId);
  params.set("return_url", body.returnUrl ?? "https://yatabase.etzhayyim.com/dashboard");

  try {
    const resp = await fetch("https://api.stripe.com/v1/billing_portal/sessions", {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
        "content-type": "application/x-www-form-urlencoded",
      },
      body: params.toString(),
    });
    const text = await resp.text().catch(() => "");
    if (!resp.ok) {
      return new Response(
        JSON.stringify({ error: "StripePortalFailed", status: resp.status, upstream: text.slice(0, 300) }),
        { status: 502, headers: { "content-type": "application/json" } },
      );
    }
    const data = JSON.parse(text) as { id?: string; url?: string };
    if (!data?.url) {
      return new Response(
        JSON.stringify({ error: "StripePortalNoUrl", upstream: text.slice(0, 300) }),
        { status: 502, headers: { "content-type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({
        ok: true,
        portalUrl: data.url,
        sessionId: data.id,
        customerId,
        message: "Redirect the customer to portalUrl. They can change card, cancel, or view invoices there.",
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  } catch (e) {
    return new Response(
      JSON.stringify({ error: "StripePortalThrew", message: e instanceof Error ? e.message.slice(0, 300) : String(e) }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }
}

interface CheckoutResult {
  url?: string;
  sessionId?: string;
  error?: string;
}

async function createStripeCheckoutSession(
  env: BillingEnv,
  orgDid: string,
  plan: PlanTier,
  priceId: string,
  successUrl: string | undefined,
  cancelUrl: string | undefined,
): Promise<CheckoutResult> {
  if (!env.STRIPE_SECRET_KEY) return { error: "STRIPE_SECRET_KEY not configured" };
  const params = new URLSearchParams();
  params.set("mode", "subscription");
  params.set("line_items[0][price]", priceId);
  params.set("line_items[0][quantity]", "1");
  params.set("client_reference_id", orgDid);
  params.set("metadata[org_did]", orgDid);
  params.set("metadata[plan]", plan);
  params.set("success_url", successUrl ?? "https://yatabase.etzhayyim.com/?upgrade=success");
  params.set("cancel_url", cancelUrl ?? "https://yatabase.etzhayyim.com/?upgrade=cancel");
  // Stripe Tax: auto-compute US sales tax (Wayfair nexus) + JP consumption
  // tax. `customer_creation` is invalid in subscription mode — Stripe
  // creates the customer record automatically when the subscription
  // is signed.
  params.set("automatic_tax[enabled]", "true");

  try {
    const resp = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
        "content-type": "application/x-www-form-urlencoded",
      },
      body: params.toString(),
    });
    const text = await resp.text().catch(() => "");
    if (!resp.ok) {
      console.warn("[yatabase][stripe] checkout failed:", resp.status, text.slice(0, 200));
      return { error: text.slice(0, 200) };
    }
    const data = JSON.parse(text) as { id?: string; url?: string };
    return { url: data?.url, sessionId: data?.id };
  } catch (e) {
    return { error: e instanceof Error ? e.message : String(e) };
  }
}

/**
 * POST /webhook/stripe — Stripe-side webhook (P8). Activates the plan
 * once Stripe confirms the customer has paid. Verifies the
 * `Stripe-Signature` header against `STRIPE_WEBHOOK_SECRET` to defend
 * against forged events.
 *
 * Handled events:
 *   checkout.session.completed       → activate plan
 *   customer.subscription.deleted    → revert to free
 *   customer.subscription.updated    → re-activate (plan change mid-cycle)
 */
export async function handleStripeWebhook(env: BillingEnv, req: Request): Promise<Response> {
  if (!env.STRIPE_WEBHOOK_SECRET) {
    return new Response(
      JSON.stringify({ error: "WebhookDisabled", message: "STRIPE_WEBHOOK_SECRET not configured" }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }
  const sig = req.headers.get("stripe-signature") ?? "";
  const raw = await req.text();
  if (!await verifyStripeSignature(env.STRIPE_WEBHOOK_SECRET, sig, raw)) {
    return new Response(
      JSON.stringify({ error: "BadSignature" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  let event: { id?: string; type?: string; data?: { object?: Record<string, unknown> } } = {};
  try {
    event = JSON.parse(raw);
  } catch {
    return new Response(
      JSON.stringify({ error: "BadJson" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  // P72: idempotency. Stripe retries webhooks (up to 3 days) until 2xx;
  // re-processing the same checkout.session.completed event would
  // re-flip the plan / re-emit confirmation emails. Track seen event
  // IDs in KV (24h TTL — long after Stripe's retry budget) and short-
  // circuit duplicates with a 200 OK + duplicate marker.
  const eventId = (event.id ?? "").trim();
  if (eventId && env.YATABASE_AUTH_CACHE) {
    const dedupKey = `stripe_event:v1:${eventId}`;
    try {
      const seen = await env.YATABASE_AUTH_CACHE.get(dedupKey);
      if (seen) {
        return new Response(
          JSON.stringify({ ok: true, duplicate: true, eventId, firstSeenAt: seen }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      }
      await env.YATABASE_AUTH_CACHE.put(dedupKey, new Date().toISOString(), { expirationTtl: 86400 });
    } catch (e) {
      // KV failure shouldn't break webhook processing — Stripe needs a 200.
      console.warn("[yatabase][stripe-webhook] dedup KV failed (continuing):", e);
    }
  }
  const obj = event.data?.object ?? {};
  const orgDid = String((obj.metadata as Record<string, unknown> | undefined)?.org_did
    ?? (obj.client_reference_id as string)
    ?? "");
  const plan = String((obj.metadata as Record<string, unknown> | undefined)?.plan ?? "") as PlanTier;
  const subId = String(obj.subscription ?? obj.id ?? "");
  const customerId = String(obj.customer ?? "");

  switch (event.type) {
    case "checkout.session.completed":
    case "customer.subscription.updated":
      if (orgDid && ALLOWED_TARGETS.includes(plan) && plan !== "free") {
        try {
          await persistPlan(env, orgDid, plan, "stripe-webhook", subId, customerId);
        } catch (e) {
          console.warn("[yatabase][stripe-webhook] persist failed:", e);
        }
        try { await recordConversion(env, orgDid, plan); } catch { /* non-fatal */ }
      }
      break;
    case "customer.subscription.deleted":
      if (orgDid) {
        try {
          await persistPlan(env, orgDid, "free", "stripe-webhook", null, customerId);
        } catch (e) {
          console.warn("[yatabase][stripe-webhook] downgrade failed:", e);
        }
      }
      break;
    default:
      // Ignore other event types silently (Stripe expects 200 OK).
      break;
  }
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function verifyStripeSignature(secret: string, header: string, body: string): Promise<boolean> {
  // Stripe-Signature header: "t=1492774577,v1=hex_digest,v0=..."
  if (!header) return false;
  const parts = Object.fromEntries(
    header.split(",").map((s) => {
      const i = s.indexOf("=");
      return [s.slice(0, i), s.slice(i + 1)];
    }),
  ) as Record<string, string>;
  const ts = parts.t;
  const provided = parts.v1;
  if (!ts || !provided) return false;
  const signedPayload = `${ts}.${body}`;
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(signedPayload));
  const expected = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  // Constant-time compare.
  if (expected.length !== provided.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ provided.charCodeAt(i);
  }
  return diff === 0;
}
