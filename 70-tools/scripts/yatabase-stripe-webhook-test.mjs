#!/usr/bin/env node
/**
 * yatabase-stripe-webhook-test — end-to-end integration test for the
 * Stripe Live → /webhook/stripe → vertex_org_plan plan-flip pipeline.
 *
 * No real Stripe call is made. The harness:
 *   1. POST /auth/v1/signup           — mints a fresh tenant + API key
 *   2. GET  /api/plan                 — confirms inferred plan = "free"
 *   3. Build synthetic checkout.session.completed event (Stripe shape)
 *   4. HMAC-SHA-256 sign payload with `STRIPE_WEBHOOK_SECRET` (Stripe v1
 *      scheme: `t=<unix>,v1=<hex digest of "<unix>.<body>">`)
 *   5. POST /webhook/stripe with the event + signature header
 *   6. Wait for RW propagation, then GET /api/plan to verify tier flip
 *
 * Required env:
 *   YATA_BASE                  default https://yatabase.etzhayyim.com
 *   STRIPE_WEBHOOK_SECRET      same value pushed via `wrangler secret put`
 *
 * Optional env:
 *   PLAN                       target plan tier (default "starter")
 *   PROPAGATION_MAX_S          max seconds to wait for plan flip (default 180)
 *
 * Exits non-zero on any step failure. Suitable as a CI gate.
 */

import crypto from "node:crypto";

const HOST = (process.env.YATA_BASE ?? "https://yatabase.etzhayyim.com").replace(/\/$/, "");
const SECRET = process.env.STRIPE_WEBHOOK_SECRET;
const TARGET_PLAN = (process.env.PLAN ?? "starter").trim();
const PROPAGATION_MAX = Number(process.env.PROPAGATION_MAX_S ?? "180") | 0;

const ALLOWED_PLANS = new Set(["starter", "developer", "business"]);
if (!SECRET) {
  console.error("ERR: STRIPE_WEBHOOK_SECRET env required (must match the wrangler secret on the Worker)");
  process.exit(2);
}
if (!ALLOWED_PLANS.has(TARGET_PLAN)) {
  console.error(`ERR: PLAN must be one of ${[...ALLOWED_PLANS].join(",")}, got "${TARGET_PLAN}"`);
  process.exit(2);
}

function step(label) {
  process.stdout.write(`▸ ${label.padEnd(56, " ")}`);
}
function ok(msg) { console.log(`OK   ${msg ?? ""}`); }
function fail(msg) { console.log(`FAIL ${msg ?? ""}`); process.exit(1); }

function fmtSig(unixTs, payload, secret) {
  const signedPayload = `${unixTs}.${payload}`;
  const v1 = crypto.createHmac("sha256", secret).update(signedPayload).digest("hex");
  return `t=${unixTs},v1=${v1}`;
}

function syntheticCheckoutSession(orgDid, plan) {
  const subId = `sub_test_${crypto.randomBytes(12).toString("hex")}`;
  const sessId = `cs_test_${crypto.randomBytes(16).toString("hex")}`;
  const custId = `cus_test_${crypto.randomBytes(12).toString("hex")}`;
  const ts = Math.floor(Date.now() / 1000);
  return {
    id: `evt_test_${crypto.randomBytes(12).toString("hex")}`,
    object: "event",
    api_version: "2024-04-10",
    created: ts,
    type: "checkout.session.completed",
    data: {
      object: {
        id: sessId,
        object: "checkout.session",
        customer: custId,
        subscription: subId,
        client_reference_id: orgDid,
        metadata: {
          org_did: orgDid,
          plan,
        },
        mode: "subscription",
        payment_status: "paid",
        status: "complete",
      },
    },
  };
}

async function main() {
  console.log(`yatabase-stripe-webhook-test  target=${HOST}  plan=${TARGET_PLAN}`);
  console.log("─".repeat(72));

  // 1. Signup
  step("POST /auth/v1/signup");
  let signup;
  try {
    const resp = await fetch(`${HOST}/auth/v1/signup`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "stripe-webhook-smoke" }),
    });
    if (!resp.ok) fail(`status=${resp.status}`);
    signup = await resp.json();
    if (!signup.apiKey || !signup.orgDid) fail("missing apiKey/orgDid in response");
    ok(`apiKey=${signup.apiKey.slice(0, 18)}… org=${signup.orgDid.slice(0, 30)}…`);
  } catch (e) { fail(`threw: ${e.message ?? e}`); }

  const orgDid = signup.orgDid;
  const apiKey = signup.apiKey;

  // 2. Plan inference (should be "free" for fresh yata-tenant.etzhayyim.com DID)
  // Retry up to 3min — vertex_api_key INSERT from signup needs to propagate
  // through RW read replicas before /api/plan auth resolves.
  step("GET /api/plan (pre-webhook, with auth-propagation retry)");
  let preFlipPlan = "?";
  {
    const deadline = Date.now() + 180_000;
    let lastStatus = 0;
    while (Date.now() < deadline) {
      const resp = await fetch(`${HOST}/api/plan`, {
        headers: { authorization: `Bearer ${apiKey}` },
      });
      lastStatus = resp.status;
      if (resp.ok) {
        const body = await resp.json();
        preFlipPlan = body.plan ?? "?";
        break;
      }
      await new Promise((r) => setTimeout(r, 8000));
    }
    if (preFlipPlan === "?") fail(`could not authenticate fresh key (last status=${lastStatus})`);
    if (preFlipPlan !== "free") fail(`expected plan=free, got plan=${preFlipPlan}`);
    ok(`plan=${preFlipPlan}`);
  }

  // 3-5. Build + sign + send synthetic event
  step("POST /webhook/stripe (synthetic, signed)");
  let webhookResp;
  try {
    const event = syntheticCheckoutSession(orgDid, TARGET_PLAN);
    const payload = JSON.stringify(event);
    const ts = Math.floor(Date.now() / 1000);
    const sigHeader = fmtSig(ts, payload, SECRET);
    const resp = await fetch(`${HOST}/webhook/stripe`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "stripe-signature": sigHeader,
      },
      body: payload,
    });
    if (!resp.ok) fail(`status=${resp.status} body=${(await resp.text()).slice(0, 240)}`);
    webhookResp = await resp.json();
    if (!webhookResp.ok) fail(`webhook reply not ok: ${JSON.stringify(webhookResp)}`);
    ok(`event=${event.type} ack=${JSON.stringify(webhookResp)}`);
  } catch (e) { fail(`threw: ${e.message ?? e}`); }

  // 6. Negative test: reject bad signature
  step("POST /webhook/stripe (bad signature → 400)");
  try {
    const event = syntheticCheckoutSession(orgDid, TARGET_PLAN);
    const payload = JSON.stringify(event);
    const ts = Math.floor(Date.now() / 1000);
    const sigHeader = `t=${ts},v1=${"00".repeat(32)}`;
    const resp = await fetch(`${HOST}/webhook/stripe`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "stripe-signature": sigHeader,
      },
      body: payload,
    });
    if (resp.status !== 400) fail(`expected 400, got ${resp.status}`);
    ok(`rejected as expected (400)`);
  } catch (e) { fail(`threw: ${e.message ?? e}`); }

  // 7. Wait for RW propagation; poll /api/plan until flipped or timeout
  step(`GET /api/plan (post-webhook, poll up to ${PROPAGATION_MAX}s)`);
  const deadline = Date.now() + PROPAGATION_MAX * 1000;
  let postFlipPlan = preFlipPlan;
  let elapsed = 0;
  while (Date.now() < deadline) {
    const resp = await fetch(`${HOST}/api/plan`, {
      headers: { authorization: `Bearer ${apiKey}` },
    });
    const body = resp.ok ? await resp.json() : { plan: "?" };
    postFlipPlan = body.plan ?? "?";
    elapsed = Math.round((Date.now() - (deadline - PROPAGATION_MAX * 1000)) / 1000);
    if (postFlipPlan === TARGET_PLAN) {
      ok(`plan=${postFlipPlan} after ${elapsed}s`);
      break;
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
  if (postFlipPlan !== TARGET_PLAN) {
    fail(`plan stuck at ${postFlipPlan} after ${elapsed}s; expected ${TARGET_PLAN}`);
  }

  console.log("─".repeat(72));
  console.log(`PASS — webhook signature verify ✓ · plan flip ${preFlipPlan} → ${postFlipPlan} ✓`);
}

main().catch((e) => {
  console.error("ERR:", e?.stack ?? e);
  process.exit(1);
});
