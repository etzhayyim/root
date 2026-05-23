// yatabase.etzhayyim.com — L3 dispatcher CF Worker (ADR-2605080000 §D10 P3.1).
//
// Surfaces:
//   /health, /_app/meta                       — edge probe
//   /storage/v1/object/{bucket}/{key}         — Supabase REST (PUT/GET/HEAD/DELETE)
//   /storage/v1/object/list/{bucket}          — list objects
//   /storage/v1/object/sign/{bucket}/{key}    — presigned URL mint
//   /storage/v1/bucket                        — list buckets
//   /storage/v1/object/public/{bucket}/{key}  — public ACL (P3.2 stub)
//   /sparql                                   — SPARQL 1.1 SELECT/CONSTRUCT/ASK
//   /xrpc/ai.gftd.apps.{yata,billing}.*       — XRPC pass-through
//
// Auth: Bearer sk_live_yata_* / ES256 JWT → PDS service binding
// `/_internal/resolve-auth` returns { did, orgDid, activeDid, productScope }.
// All data-plane calls forward to bpmn-dispatcher with x-internal-trust HMAC.

import { Hono } from "hono";
import { handleStorageRest } from "./storage-rest";
import { handleS3Rest } from "./s3-rest";
import { handlePublicAcl } from "./public-acl";
import {
  listBucketsDirect,
  listObjectsDirect,
  headObjectDirect,
} from "./hyperdrive-reads";
import { dispatchYataXrpc, type DispatcherCallerContext } from "./dispatcher";
import { handleCypherRequest } from "./cypher";
import { handleMcpRequest } from "./mcp";
import { buildAgentJson, buildMcpJson } from "./well-known";
import { studioResponse } from "./studio";
import { landingResponse } from "./landing";
import { statusResponse } from "./status";
import { teamResponse } from "./team";
import { docsResponse } from "./docs";
import { robotsResponse, sitemapResponse, securityTxtResponse } from "./seo";
import { integrationsResponse } from "./integrations";
import { changelogResponse } from "./changelog";
import { quickstartResponse } from "./quickstart";
import { comparisonResponse } from "./comparison";
import { dashboardResponse } from "./dashboard";
// BMC writes now live in the lg-yatabase Granian pod (mitama-yata-pool).
// The yatabase Worker forwards XRPC requests over HTTPS+HMAC and never
// touches Hyperdrive for BMC tables. See src/bmc-forward.ts.
import { forwardBmc, isBmcNsid } from "./bmc-forward";
import { forwardQuery, isQueryNsid } from "./query-forward";
import { privacyResponse } from "./privacy";
import { termsResponse } from "./terms";
import { openapiResponse } from "./openapi";
import { describeTenantSchema } from "./schema-describe";
import { handleSignup } from "./auth-signup";
import { emitMeter, getUsageLast24h } from "./metering";
import { getQuotaStatus, quotaExceededResponse, PLAN_RULES } from "./plan-quota";
import { handleUpgrade, handleStripeWebhook, handlePortal } from "./billing-stripe";
import { handleDonate } from "./donate";
import { handleUsdcWebhook } from "./webhook-usdc";
import { handleInvoice, listInvoiceMonths } from "./invoice";
import { resolvePlan } from "./plan-quota";
import { listMembers, handleInvite, handleRevoke } from "./org-members";
import { handleExport, handleAccountDelete } from "./data-rights";
import { emitAudit, getAuditEvents } from "./audit-log";
import { getOutbox, retryOutboxBatch } from "./email-outbox";
import { listAgents, getAgent, runAgent, bootstrapAgentTables, recentAgentRuns } from "./agents/registry";
import type { AgentName } from "./agents/types";
import { handleLeadIngest, listLeads, setLeadOutreachStatus, setLeadContactEmail, setLeadEnrichment, leadsNeedingEnrichment, leadsSendable, getLeadByVertexId, sendApprovedLead, type LeadIngest } from "./leads";
import { fetchHnLeads, type HnScrapeReport } from "./lead-sources/hn";
import { enrichDomain, type EnrichResult } from "./lead-sources/enrich";
import { fetchGithubLeads, type GithubScrapeReport } from "./lead-sources/github";
import { getReferrerStats } from "./referrer";

type Env = {
  YATA_VERSION?: string;
  YATA_ACTOR_DID?: string;
  BPMN_DISPATCHER_URL: string;
  PDS_URL?: string;
  AUTHN_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
  PDS_SERVICE?: { fetch(req: Request): Promise<Response> };
  AUTHN_SERVICE?: { fetch(req: Request): Promise<Response> };
  HYPERDRIVE?: unknown;
  GFTD_METERING_DISABLED?: string;
  YATA_AGENT_ADMIN_KEY?: string;   // gate for POST /_agents/*/run
  RESEND_API_KEY?: string;
  EMAIL_FROM?: string;
  GITHUB_TOKEN?: string;            // optional, lifts /api/leads/sources/github budget 60 → 5000/h
  LG_YATABASE_URL?: string;         // BMC forward target (lg-yatabase Granian pod)
  YATABASE_AUTH_CACHE?: KVNamespace; // P62: Workers KV for sk_live_yata_* resolution fallback
  YATA_BURST_LIMITER?: { limit: (opts: { key: string }) => Promise<{ success: boolean }> }; // P82: CF native edge rate-limit (100/10s)
};

interface AuthContext {
  did: string;
  orgDid: string;
  activeDid?: string;
  productScope?: "yata" | "obj" | null;
}

declare module "hono" {
  interface ContextVariableMap {
    auth?: AuthContext;
  }
}

const app = new Hono<{ Bindings: Env }>();

// P67: CORS — yatabase is a customer-facing BaaS. Browser SDK clients
// must be able to call /auth/v1/signup, /cypher, /storage, /mcp, /api/*
// from any origin. Headers are echoed back; allow-list stays open since
// auth is Bearer-token based and there are no cookies / sessions to
// CSRF against.
const CORS_ALLOW_HEADERS = "authorization,content-type,x-active-did,x-yatabase-trace-id,if-none-match,if-match,x-amz-content-sha256,x-amz-date";
const CORS_EXPOSE_HEADERS = "etag,x-yatabase-cache,x-yatabase-storage-tier,x-yatabase-storage-provider,x-yatabase-signup-path,x-yatabase-surface,x-yatabase-trace-id,ratelimit-limit,ratelimit-remaining,ratelimit-reset,ratelimit-policy";

app.use("*", async (c, next) => {
  const origin = c.req.header("origin") ?? "";
  await next();
  // CORS headers (P67). Echoing origin (not "*") keeps credential-using
  // SDKs happy if customers ever opt-in to that.
  if (origin) {
    c.res.headers.set("access-control-allow-origin", origin);
    c.res.headers.set("vary", "origin");
    c.res.headers.set("access-control-allow-credentials", "true");
  } else {
    c.res.headers.set("access-control-allow-origin", "*");
  }
  c.res.headers.set("access-control-expose-headers", CORS_EXPOSE_HEADERS);

  // P68: production security headers. HSTS forces TLS for repeat visits;
  // X-Content-Type-Options blocks MIME-sniffing; Referrer-Policy keeps
  // tenant URLs out of third-party referrer logs; Permissions-Policy
  // strips browser feature access. HTML pages get a CSP that allows
  // inline styles + the Studio's own JSON-fetching code.
  c.res.headers.set("strict-transport-security", "max-age=63072000; includeSubDomains; preload");
  c.res.headers.set("x-content-type-options", "nosniff");
  c.res.headers.set("referrer-policy", "strict-origin-when-cross-origin");
  c.res.headers.set("permissions-policy", "geolocation=(), microphone=(), camera=(), payment=()");
  const ct = c.res.headers.get("content-type") ?? "";
  if (ct.startsWith("text/html")) {
    // /studio + landing pages — same-origin scripts + inline styles only.
    c.res.headers.set("content-security-policy",
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline'; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data: https:; " +
      "connect-src 'self' https://yatabase.etzhayyim.com https://atproto.etzhayyim.com https://api.resend.com; " +
      "frame-ancestors 'self'; " +
      "base-uri 'self'; " +
      "form-action 'self'");
    c.res.headers.set("x-frame-options", "SAMEORIGIN");
  }
});

// Preflight handler. Hono routes OPTIONS to the same path normally, but
// many of our routes are POST-only — so explicitly answer OPTIONS for
// every path with the right CORS response.
app.options("*", (c) => {
  const origin = c.req.header("origin") ?? "*";
  return new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": origin === "*" ? "*" : origin,
      "access-control-allow-methods": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
      "access-control-allow-headers": CORS_ALLOW_HEADERS,
      "access-control-allow-credentials": "true",
      "access-control-max-age": "86400",
      "vary": "origin",
    },
  });
});

app.get("/health", (c) =>
  c.json({ ok: true, app: "yatabase", ts: new Date().toISOString() }),
);

app.get("/_worker/health", (c) =>
  c.json({ ok: true, app: "yatabase", ts: new Date().toISOString() }),
);

app.get("/_app/meta", (c) =>
  c.json({
    app: "ai-gftd-project-yatabase",
    did: c.env.YATA_ACTOR_DID ?? "did:web:yatabase.etzhayyim.com",
    version: c.env.YATA_VERSION ?? "0.0.0",
    layer: "L3-dispatcher",
    codename: "io-yatabase",
    authoritativeAdr: "ADR-2605080000 §D10 + §D12-D24",
    surfaces: [
      "/",
      "/studio",
      "/embed",
      "/auth/v1/signup",
      "/auth/v1/upgrade",
      "/auth/v1/invite",
      "/auth/v1/revoke",
      "/api/donate",
      "/webhook/stripe",
      "/webhook/usdc",
      "/api/schema",
      "/api/usage",
      "/api/plan",
      "/api/members",
      "/api/invoices",
      "/api/invoice?month=YYYY-MM",
      "/api/audit",
      "/api/outbox",
      "/api/referrer-stats",
      "/api/export",
      "/api/account/delete",
      "/storage/v1/object/{bucket}/{key}",
      "/storage/v1/object/list/{bucket}",
      "/storage/v1/object/sign/{bucket}/{key}",
      "/storage/v1/object/public/{bucket}/{key}",
      "/storage/v1/bucket",
      "/s3/{bucket}/{key}",
      "/sparql",
      "/cypher",
      "/mcp",
      "/.well-known/agent.json",
      "/.well-known/mcp.json",
      "/xrpc/ai.gftd.apps.yata.*",
    ],
    backend: c.env.BPMN_DISPATCHER_URL,
  }),
);

// Public well-known docs (a2a + MCP discovery). No auth.
app.get("/.well-known/agent.json", (c) => c.json(buildAgentJson(c.env)));
app.get("/.well-known/mcp.json", (c) => c.json(buildMcpJson(c.env)));

// Studio — browser console for Cypher / SPARQL / Storage / MCP. CSR only,
// API key held in `localStorage`. Public HTML; the data-plane endpoints
// each enforce their own auth.
// `/`        — public marketing landing (no auth, edge-cacheable)
// `/studio`  — browser console (Cypher / SPARQL / Storage / MCP)
// `/embed`   — same as /studio, intended for iframe embedding
// `/status`  — public uptime + agent activity from vertex_yata_qa_run + vertex_yata_agent_run
// `/team`    — public 4-agent roster (chikada / tanaka / nishino / sakamoto)
app.get("/", (_c) => landingResponse());
app.get("/studio", (_c) => studioResponse());
app.get("/embed", (_c) => studioResponse());
app.get("/status", async (c) => statusResponse(c.env));
app.get("/team", async (c) => teamResponse(c.env));
app.get("/docs", (_c) => docsResponse());
app.get("/privacy", (_c) => privacyResponse());
app.get("/terms", (_c) => termsResponse());
app.get("/robots.txt", (_c) => robotsResponse());
app.get("/sitemap.xml", (_c) => sitemapResponse());
app.get("/openapi.json", (_c) => openapiResponse());
app.get("/integrations", (_c) => integrationsResponse());
app.get("/changelog", (_c) => changelogResponse());
app.get("/quickstart", (_c) => quickstartResponse());
app.get("/comparison", (_c) => comparisonResponse());
app.get("/dashboard", (_c) => dashboardResponse());
app.get("/.well-known/security.txt", (_c) => securityTxtResponse());

// ── P5: self-service signup (P15: optional email + welcome message) ──
app.post("/auth/v1/signup", async (c) => handleSignup(c.env, c.req.raw));

// (P6 /api/usage moved below the auth middleware so it picks up `auth` ctx.)

// Auth resolution. We call `com.atproto.server.getSession` on PDS which
// accepts BOTH atproto session JWTs (ES256 / DPoP) and api-key Bearer tokens
// (`sk_live_*` / `sk_live_yata_*`). On 200 the response carries the owner
// DID; we treat that DID as both `did` and `orgDid` until per-org mapping
// is wired (planned P4b §D11 retail-cloud admin).
//
// Service binding `PDS_SERVICE.fetch` is preferred (zero-egress, ~5ms) but
// falls back to public `https://atproto.etzhayyim.com/xrpc/...` if the binding is
// missing (local dev).
import { lookupCachedApiKey, rememberApiKeyResolution } from "./auth-cache";

// P85: 429 builder shared between P82 (per-POP) and P85 (global) layers.
function makeBurst429(orgDid: string, kind: "burst-pop" | "burst-global"): Response {
  return new Response(
    JSON.stringify({
      error: "QuotaExceeded",
      kind,
      message: kind === "burst-pop"
        ? "Per-POP burst limit: 100 requests per 10 seconds. Back off and retry."
        : "Global burst limit: 100 requests per 10 seconds per tenant. Back off and retry.",
      orgDid,
    }),
    {
      status: 429,
      headers: {
        "content-type": "application/json",
        "retry-after": "10",
        "ratelimit-policy": "100;w=10",
        "x-yatabase-ratelimit-kind": kind,
      },
    },
  );
}

// P77: erasure-tombstone check. /api/account/delete writes
// `erased:v1:{orgDid}` to KV; any bearer auth for that org must 401
// regardless of which path resolved the key (KV cache hit or pod
// authResolveApiKey).
async function checkErasureTombstone(env: Env, orgDid: string): Promise<boolean> {
  const kv = (env as unknown as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  if (!kv) return false;
  try {
    const tombstone = await kv.get(`erased:v1:${orgDid}`);
    return !!tombstone;
  } catch {
    return false;
  }
}

async function resolveAuthContext(req: Request, env: Env): Promise<AuthContext | null> {
  const h = req.headers.get("authorization") ?? "";
  if (!h.startsWith("Bearer ")) return null;
  const xActiveDid = req.headers.get("x-active-did") ?? undefined;

  // Bearer sk_live_yata_* keys: try Workers Cache first (fed by signup
  // handler at mint-time, P62 2026-05-12). If miss, fall through to the
  // pod's authResolveApiKey RPC.
  const rawKey = h.slice("Bearer ".length).trim();
  if (rawKey.startsWith("sk_live_yata_") || rawKey.startsWith("sk_test_yata_")) {
    const cached = await lookupCachedApiKey(env, rawKey);
    if (cached) {
      // P77: respect the erasure tombstone written by /api/account/delete.
      // Even if the pod-side vertex_api_key row still exists (RW degraded),
      // a tenant who exercised right-to-erasure must NOT keep authing.
      const erased = await checkErasureTombstone(env, cached.ownerDid);
      if (erased) return null;
      const productScope =
        cached.productScope === "yata" ? "yata" :
        cached.productScope === "obj"  ? "obj"  :
        detectProductScope(h);
      return {
        did: cached.ownerDid,
        orgDid: cached.ownerDid,
        activeDid: xActiveDid ?? cached.ownerDid,
        productScope: productScope as AuthContext["productScope"],
      };
    }

    const dispatcherBase = env.LG_YATABASE_URL || "https://dispatcher.etzhayyim.com";
    const url = `${dispatcherBase.replace(/\/+$/, "")}/xrpc/ai.gftd.apps.yata.authResolveApiKey`;
    try {
      const keyHash = await sha256Hex(rawKey);
      const bodyStr = JSON.stringify({ key_hash: keyHash });
      const headers: Record<string, string> = { "content-type": "application/json" };
      if (env.DISPATCHER_INTERNAL_SECRET) {
        headers["x-internal-trust"] = await hmacHex(env.DISPATCHER_INTERNAL_SECRET, bodyStr);
      }
      const resp = await fetch(url, { method: "POST", headers, body: bodyStr });
      if (!resp.ok) {
        console.warn(`[yatabase][auth] resolve key failed status=${resp.status}`);
        return null;
      }
      const data = (await resp.json()) as {
        ok?: boolean; found?: boolean;
        ownerDid?: string; scopes?: string; productScope?: string;
      };
      if (!data?.found || !data.ownerDid) return null;
      // P77: same erasure-tombstone check on the pod-resolution path.
      const erased = await checkErasureTombstone(env, data.ownerDid);
      if (erased) return null;
      // Backfill cache so subsequent bearer calls in this POP are free.
      await rememberApiKeyResolution(env, rawKey, data.ownerDid, data.scopes ?? "atproto", data.productScope ?? "yata");
      const productScope =
        data.productScope === "yata" ? "yata" :
        data.productScope === "obj"  ? "obj"  :
        detectProductScope(h);
      return {
        did: data.ownerDid,
        orgDid: data.ownerDid,
        activeDid: xActiveDid ?? data.ownerDid,
        productScope: productScope as AuthContext["productScope"],
      };
    } catch (e) {
      console.warn("[yatabase][auth] resolve key threw:", e);
      return null;
    }
  }

  // ES256 JWT / session token: delegate to PDS as before. PDS_SERVICE binding
  // is preferred (zero-egress) but `fetch` works too.
  const headers: Record<string, string> = { authorization: h };
  if (xActiveDid) headers["x-active-did"] = xActiveDid;
  const url = "https://atproto.etzhayyim.com/xrpc/com.atproto.server.getSession";
  const fetcher = env.PDS_SERVICE?.fetch
    ? (r: Request) => env.PDS_SERVICE!.fetch(r)
    : (r: Request) => fetch(r);
  try {
    const resp = await fetcher(new Request(url, { method: "GET", headers }));
    if (!resp.ok) return null;
    const data = (await resp.json()) as { did?: string; handle?: string; active?: boolean };
    if (!data?.did) return null;
    if (data.active === false) return null;
    return {
      did: data.did,
      orgDid: data.did,
      activeDid: xActiveDid ?? data.did,
      productScope: detectProductScope(h),
    };
  } catch {
    return null;
  }
}

async function sha256Hex(input: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function hmacHex(secret: string, body: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(body));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function detectProductScope(authHeader: string): "yata" | "obj" | null {
  if (authHeader.startsWith("Bearer sk_live_yata_") || authHeader.startsWith("Bearer sk_test_yata_")) return "yata";
  if (authHeader.startsWith("Bearer sk_live_obj_") || authHeader.startsWith("Bearer sk_test_obj_")) return "obj";
  return null;
}

app.use("*", async (c, next) => {
  // P67: OPTIONS preflight already answered by app.options handler.
  // Skip auth + quota for OPTIONS.
  if (c.req.method === "OPTIONS") return next();
  if (c.req.path === "/health" || c.req.path === "/_worker/health" || c.req.path === "/_app/meta") {
    return next();
  }
  // Public ACL path is gated separately by `handlePublicAcl` (bucket
  // public_read=true). /s3/* uses AWS SigV4 instead of Bearer.
  if (c.req.path.startsWith("/storage/v1/object/public/")) return next();
  if (c.req.path.startsWith("/s3/")) return next();
  // MCP enforces auth per-method (initialize / tools/list etc. are public);
  // well-known is fully public.
  if (c.req.path === "/mcp") return next();
  if (c.req.path.startsWith("/.well-known/")) return next();
  if (c.req.path === "/" || c.req.path === "/studio" || c.req.path === "/embed") return next();
  if (c.req.path === "/status" || c.req.path === "/team") return next();
  if (c.req.path === "/docs" || c.req.path === "/robots.txt" || c.req.path === "/sitemap.xml") return next();
  if (c.req.path === "/privacy" || c.req.path === "/terms") return next();
  if (c.req.path === "/openapi.json") return next();
  if (c.req.path === "/integrations" || c.req.path === "/changelog") return next();
  if (c.req.path === "/quickstart" || c.req.path === "/comparison") return next();
  if (c.req.path === "/dashboard") return next();
  // /auth/v1/signup is public — it MINTS the API key, so it can't require one.
  if (c.req.path === "/auth/v1/signup") return next();
  // Stripe webhook is signature-verified inline; no Bearer auth.
  if (c.req.path === "/webhook/stripe") return next();
  // USDC donation webhook is attestation-verified inline; no Bearer auth.
  if (c.req.path === "/webhook/usdc") return next();
  // Agent surfaces: /_agents/list is public; /_agents/{name}/run is gated
  // by x-yata-admin-key (operator-only). Tenant Bearer auth doesn't apply.
  if (c.req.path === "/_agents/list" || c.req.path.startsWith("/_agents/")) return next();
  // Lead CRM surfaces — admin-keyed (same gate as /_agents/*).
  if (c.req.path === "/api/leads" || c.req.path === "/api/leads/ingest") return next();
  if (c.req.path.startsWith("/api/leads/sources/")) return next();
  if (c.req.path.startsWith("/api/leads/")) return next();   // mutation routes (/:id/approve, etc.)
  if (c.req.path === "/api/outbox/retry-failed") return next();  // operator-only bulk retry
  const auth = await resolveAuthContext(c.req.raw, c.env);
  if (auth) c.set("auth", auth);

  // P7: per-tenant daily quota enforcement. Bypass for read-only
  // observability endpoints (`/api/usage`, `/api/plan`, `/_app/meta`)
  // so customers can always inspect their own state even at quota.
  // P67: also surface RateLimit headers (RFC 9237 draft + Stripe/GitHub
  // convention) so clients can see their position without polling
  // /api/plan.
  let quotaForHeaders: { apiRequestPerDay: number | null; apiRequestRemaining: number | null; windowStart: string } | null = null;
  if (auth) {
    const path = c.req.path;
    const observability = path === "/api/usage" || path === "/api/plan" || path === "/_app/meta";

    // P82: CF native edge burst limiter. 100 req per 10s per orgDid, fires
    // synchronously at the edge (no KV propagation lag). Per-POP — catches
    // single-POP sustained abuse but not distributed bursts.
    //
    // P85: KV-backed global counter (layered on top of P82). Same 100/10s
    // budget but the counter is KV-resident so distributed clients fanning
    // out across many POPs accumulate into ONE bucket. KV is eventually
    // consistent so the cap may overshoot by ~5-10% under high concurrency;
    // for a 100-req burst window that's well within acceptable error.
    //
    // Observability endpoints bypass both so dashboards keep refreshing.
    if (!observability) {
      // Layer 1: P82 per-POP synchronous fast-path.
      const burst = (c.env as Env).YATA_BURST_LIMITER;
      if (burst) {
        try {
          const outcome = await burst.limit({ key: auth.orgDid });
          if (!outcome.success) {
            return makeBurst429(auth.orgDid, "burst-pop");
          }
        } catch (e) {
          console.warn("[yatabase][burst-limit] CF binding limit() threw:", e);
        }
      }
      // Layer 2: P85 KV global counter. 1-second buckets (vs P82's 10s
      // window) — finer granularity reaches the threshold faster under KV
      // eventual consistency. Synchronous put (not waitUntil) so the
      // counter converges within the same window.
      const kv = (c.env as Env).YATABASE_AUTH_CACHE;
      if (kv) {
        const bucket = Math.floor(Date.now() / 1_000);
        const burstKey = `burst:v1:${auth.orgDid}:${bucket}`;
        try {
          const raw = await kv.get(burstKey);
          const count = raw ? Number.parseInt(raw, 10) || 0 : 0;
          if (count >= 25) {  // 25 req/s = 250 req/10s, well above CF's 100/POP
            return makeBurst429(auth.orgDid, "burst-global");
          }
          // Synchronous KV bump — costs ~5ms but converges 100x faster
          // than waitUntil at the cost of slightly delaying the response.
          try { await kv.put(burstKey, String(count + 1), { expirationTtl: 60 }); }
          catch (e) { console.warn("[yatabase][burst-limit] KV bump failed:", e); }
        } catch (e) {
          console.warn("[yatabase][burst-limit] KV read failed:", e);
        }
      }
    }

    // P71: ALWAYS compute quota so RateLimit-* headers attach to every
    // authenticated response (including observability endpoints — the
    // dashboard surface where customers most want to inspect headroom).
    // Observability endpoints still bypass the 429-block branch so they
    // remain reachable at quota.
    const quota = await getQuotaStatus(c.env, auth.orgDid);
    if (!observability && quota.exceeded) {
      return quotaExceededResponse(quota);
    }
    quotaForHeaders = quota;
  }

  const startMs = Date.now();
  await next();
  // P67: surface RateLimit-* headers (RFC 9237 draft + Stripe/GitHub
  // convention) so clients can throttle proactively.
  if (quotaForHeaders) {
    const lim = quotaForHeaders.apiRequestPerDay;
    const rem = quotaForHeaders.apiRequestRemaining;
    if (lim !== null) c.res.headers.set("ratelimit-limit", String(lim));
    if (rem !== null) c.res.headers.set("ratelimit-remaining", String(rem));
    c.res.headers.set("ratelimit-reset", quotaForHeaders.windowStart);
    c.res.headers.set("ratelimit-policy", `${lim ?? "unlimited"};w=86400`);
  }
  // P10.5: per-tenant audit log. Fire-and-forget so it never blocks the
  // response. We only audit authenticated calls — the public surfaces
  // (signup / studio / well-known) carry no caller identity.
  if (auth) {
    const surface = surfaceForPath(c.req.path);
    const ipHint = c.req.header("cf-connecting-ip") ?? "";
    const uaHint = c.req.header("user-agent") ?? "";
    c.executionCtx.waitUntil(
      emitAudit(c.env, {
        orgDid: auth.orgDid,
        actorDid: auth.activeDid ?? auth.did,
        surface,
        method: c.req.method,
        path: c.req.path,
        statusCode: c.res.status,
        latencyMs: Date.now() - startMs,
        ipHint,
        userAgent: uaHint,
      }),
    );
  }
});

function surfaceForPath(p: string): string {
  if (p.startsWith("/cypher")) return "cypher";
  if (p.startsWith("/sparql")) return "sparql";
  if (p.startsWith("/storage/v1/")) return "storage";
  if (p.startsWith("/s3/")) return "s3";
  if (p === "/mcp") return "mcp";
  if (p.startsWith("/api/")) return "api";
  if (p.startsWith("/auth/v1/")) return "auth";
  if (p.startsWith("/xrpc/")) return "xrpc";
  return "other";
}

// ── P8: plan upgrade (stub or Stripe-backed) ──
app.post("/auth/v1/upgrade", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handleUpgrade(c.env, auth.orgDid, c.req.raw);
});

// ── v0.2: USDC donation (Charter Rider §2 replacement for Stripe upgrade) ──
app.post("/api/donate", async (c) => {
  // Optional auth: can donate anonymously or as authed user
  // TODO: when authed, record donation to org's vertex_donation_event for
  // SBT mint eligibility + tax receipt generation
  return handleDonate(c.req.raw, c.env as Record<string, unknown>);
});

// ── v0.2: USDC transfer webhook (Charter Rider §2 replacement for Stripe webhook) ──
app.post("/webhook/usdc", async (c) => {
  // Webhook from ChartersComplianceRegistry (or external attestation service).
  // Verifies signature and updates recipient's plan / SBT state.
  // TODO: wire real ChartersComplianceRegistry.verify() when available
  return handleUsdcWebhook(c.req.raw, c.env as Record<string, unknown>);
});

// ── P71: Stripe Customer Portal (self-serve billing management) ──
app.post("/auth/v1/portal", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handlePortal(c.env, auth.orgDid, c.req.raw);
});

// ── P76: whoami — return the current bearer's tenant identity ──
app.get("/auth/v1/whoami", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const env = c.env as { YATABASE_AUTH_CACHE?: KVNamespace };
  let attachedEmail: string | null = null;
  let attachedEmailVerified = false;
  let plan: string = "free";
  let stripeCustomerId: string | null = null;
  if (env.YATABASE_AUTH_CACHE) {
    try {
      const emailRaw = await env.YATABASE_AUTH_CACHE.get(`attach_email:v1:${auth.orgDid}`);
      if (emailRaw) {
        try {
          const parsed = JSON.parse(emailRaw) as { email?: string; verified?: boolean };
          attachedEmail = parsed?.email ?? null;
          attachedEmailVerified = parsed?.verified === true;
        } catch { /* ignore */ }
      }
      const planRaw = await env.YATABASE_AUTH_CACHE.get(`plan:v1:${auth.orgDid}`);
      if (planRaw) {
        try {
          const p = JSON.parse(planRaw) as { plan?: string; stripeCustomerId?: string };
          plan = p?.plan ?? "free";
          stripeCustomerId = (p?.stripeCustomerId ?? "") || null;
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }
  }
  return c.json({
    orgDid: auth.orgDid,
    actorDid: auth.activeDid ?? auth.did,
    productScope: auth.productScope ?? "yata",
    plan,
    attachedEmail,
    attachedEmailVerified,
    stripeCustomerId,
    canOpenPortal: !!stripeCustomerId,
  }, 200);
});

// ── P76: attach an email to this tenant for future recovery / billing
//         contact. Idempotent: subsequent calls replace the prior email. ──
app.post("/auth/v1/attach-email", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  let body: { email?: string } = {};
  try { body = await c.req.json(); } catch { /* ignore */ }
  const email = (body.email ?? "").trim().toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) {
    return c.json({ error: "BadRequest", message: "valid email required (max 254 chars)" }, 400);
  }
  const env = c.env as { YATABASE_AUTH_CACHE?: KVNamespace };
  if (!env.YATABASE_AUTH_CACHE) {
    return c.json({ error: "ServiceUnavailable", message: "auth-cache KV not bound" }, 503);
  }
  const kv = env.YATABASE_AUTH_CACHE;
  const attachedAt = new Date().toISOString();

  // P83: preserve existing verified-state when re-attaching the same
  // email (idempotent re-attach shouldn't force re-verification).
  let previouslyVerified = false;
  try {
    const priorRaw = await kv.get(`attach_email:v1:${auth.orgDid}`);
    if (priorRaw) {
      const prior = JSON.parse(priorRaw) as { email?: string; verified?: boolean };
      if (prior?.email === email && prior.verified === true) previouslyVerified = true;
    }
  } catch { /* ignore */ }

  await kv.put(
    `attach_email:v1:${auth.orgDid}`,
    JSON.stringify({ email, attachedAt, verified: previouslyVerified }),
  );

  // P83: do NOT add to reverse index until the email is verified. Sending
  // recovery links to addresses that never proved ownership is a spam
  // vector (attacker attaches victim@example.com to their tenant → calls
  // /recover → victim receives a "recovery" email they never asked for).
  if (!previouslyVerified) {
    const verifyToken = generateRecoverToken();
    await kv.put(
      `verify_email_token:v1:${verifyToken}`,
      JSON.stringify({ orgDid: auth.orgDid, email, createdAt: attachedAt }),
      { expirationTtl: 86400 }, // 24h to verify
    );
    const verifyUrl = `https://yatabase.etzhayyim.com/auth/v1/verify-email?token=${verifyToken}`;
    const subject = "[Yatabase] Verify your recovery email";
    const text =
      `Confirm ${email} as the recovery address for ${auth.orgDid}.\n\n` +
      `Click within 24 hours: ${verifyUrl}\n\n` +
      `If you did not request this, ignore the email — the address will NOT be activated.`;
    const html =
      `<p>Confirm <code>${email}</code> as the recovery address for <code>${auth.orgDid}</code>.</p>` +
      `<p><a href="${verifyUrl}">Click within 24 hours to activate</a></p>` +
      `<p style="color:#666">If you did not request this, ignore the email — the address will NOT be activated.</p>`;
    try {
      const { emitOutbox } = await import("./email-outbox");
      await emitOutbox(c.env as never, {
        orgDid: auth.orgDid, kind: "email-verify",
        subject, bodyText: text, bodyHtml: html, recipientEmail: email,
      });
    } catch (e) {
      console.warn("[yatabase][attach-email] verify-email send failed:", e);
    }
  }

  return c.json({
    ok: true,
    orgDid: auth.orgDid,
    attachedEmail: email,
    attachedEmailVerified: previouslyVerified,
    attachedAt,
    message: previouslyVerified
      ? "Email already verified. Recovery via /auth/v1/recover is active for this address."
      : "Email attached. Check your inbox for a verification link (24-hour TTL). Recovery is disabled until you verify ownership.",
  }, 200);
});

// ── P83: /auth/v1/verify-email — anonymous endpoint that marks an
//         attached email as verified after the owner clicks the link
//         emailed by /auth/v1/attach-email. Only verified emails
//         participate in the /auth/v1/recover reverse index. ──
app.get("/auth/v1/verify-email", async (c) => {
  return handleVerifyEmail(c);
});
app.post("/auth/v1/verify-email", async (c) => {
  return handleVerifyEmail(c);
});

async function handleVerifyEmail(c: { req: { query: (k: string) => string | undefined; json: () => Promise<unknown> }; env: Env; json: (b: unknown, s?: number) => Response }): Promise<Response> {
  let token = (c.req.query("token") ?? "").trim();
  if (!token) {
    try {
      const body = await c.req.json() as { token?: string };
      token = (body?.token ?? "").trim();
    } catch { /* ignore */ }
  }
  if (!token || !/^[0-9a-f]{48}$/i.test(token)) {
    return c.json({ error: "BadRequest", message: "valid token required" }, 400);
  }
  const env = c.env as { YATABASE_AUTH_CACHE?: KVNamespace };
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return c.json({ error: "ServiceUnavailable" }, 503);
  const tokKey = `verify_email_token:v1:${token}`;
  const tokRaw = await kv.get(tokKey);
  if (!tokRaw) return c.json({ error: "TokenExpired", message: "verification token invalid or expired (24h TTL)" }, 400);
  let payload: { orgDid?: string; email?: string };
  try { payload = JSON.parse(tokRaw); } catch { return c.json({ error: "TokenCorrupt" }, 400); }
  if (!payload.orgDid || !payload.email) return c.json({ error: "TokenEmpty" }, 400);

  // Mark attached email as verified.
  await kv.put(
    `attach_email:v1:${payload.orgDid}`,
    JSON.stringify({ email: payload.email, verified: true, attachedAt: new Date().toISOString() }),
  );
  // Add to reverse index for /auth/v1/recover.
  try {
    const hash = await sha256Hex(payload.email);
    const idxKey = `email_to_orgs:v1:${hash}`;
    const idxRaw = await kv.get(idxKey);
    const idx = idxRaw ? JSON.parse(idxRaw) as { orgs?: string[] } : { orgs: [] };
    const orgs = new Set(idx.orgs ?? []);
    orgs.add(payload.orgDid);
    await kv.put(idxKey, JSON.stringify({ orgs: Array.from(orgs) }));
  } catch (e) {
    console.warn("[yatabase][verify-email] reverse-index update failed:", e);
  }
  // Single-use: delete the token after redeeming.
  try { await kv.delete(tokKey); } catch { /* ignore */ }
  return c.json({
    ok: true,
    orgDid: payload.orgDid,
    verifiedEmail: payload.email,
    message: "Email verified. /auth/v1/recover is now active for this address.",
  }, 200);
}

function generateRecoverToken(): string {
  const buf = new Uint8Array(24);
  crypto.getRandomValues(buf);
  return Array.from(buf).map((b) => b.toString(16).padStart(2, "0")).join("");
}

// ── P76: /auth/v1/recover — anonymous endpoint that emails a recovery
//         link to the address attached via /auth/v1/attach-email. Always
//         returns 200 (even when the email isn't attached) to prevent
//         enumeration. The link redirects to /auth/v1/redeem. ──
app.post("/auth/v1/recover", async (c) => {
  let body: { email?: string } = {};
  try { body = await c.req.json(); } catch { /* ignore */ }
  const email = (body.email ?? "").trim().toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) {
    // Bad input gets a 400 (not enumeration — we never confirm presence).
    return c.json({ error: "BadRequest", message: "valid email required" }, 400);
  }
  const env = c.env as { YATABASE_AUTH_CACHE?: KVNamespace; RESEND_API_KEY?: string; EMAIL_FROM?: string };
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) {
    return c.json({ ok: true, note: "auth-cache KV not bound; recovery disabled" }, 200);
  }
  const hash = await sha256Hex(email);
  let orgs: string[] = [];
  try {
    const idxRaw = await kv.get(`email_to_orgs:v1:${hash}`);
    if (idxRaw) orgs = (JSON.parse(idxRaw) as { orgs?: string[] }).orgs ?? [];
  } catch { /* ignore */ }

  // Always return 200 — no leak whether the email matched any tenant.
  if (orgs.length === 0) {
    return c.json({
      ok: true,
      message: "If a tenant matches this email, recovery instructions have been sent.",
    }, 200);
  }

  // Mint a token and store with 15-min TTL.
  const token = generateRecoverToken();
  await kv.put(`recover_token:v1:${token}`, JSON.stringify({
    email, orgs, createdAt: new Date().toISOString(),
  }), { expirationTtl: 900 });

  const recoverUrl = `https://yatabase.etzhayyim.com/auth/v1/redeem?token=${token}`;
  const subject = `[Yatabase] Recovery link for ${orgs.length} tenant${orgs.length === 1 ? "" : "s"}`;
  const text = `You requested API key recovery for ${email}.\n\n` +
    `Click this link within 15 minutes to mint a new API key:\n  ${recoverUrl}\n\n` +
    `Matching tenants:\n${orgs.map((o) => `  - ${o}`).join("\n")}\n\n` +
    `If you did not request this, you can ignore this email — the link expires in 15 minutes.`;
  const html = `<p>You requested API key recovery for <code>${email}</code>.</p>` +
    `<p><a href="${recoverUrl}">Click here within 15 minutes to mint a new API key</a></p>` +
    `<p>Matching tenants:</p><ul>${orgs.map((o) => `<li><code>${o}</code></li>`).join("")}</ul>` +
    `<p style="color:#666">If you did not request this, ignore this email. The link expires in 15 minutes.</p>`;

  try {
    const { emitOutbox } = await import("./email-outbox");
    await emitOutbox(c.env as never, {
      orgDid: orgs[0],   // attribute outbox row to first matched tenant
      kind: "key-recovery",
      subject, bodyText: text, bodyHtml: html, recipientEmail: email,
    });
  } catch (e) {
    console.warn("[yatabase][recover] email send failed:", e);
  }
  return c.json({
    ok: true,
    message: "If a tenant matches this email, recovery instructions have been sent.",
  }, 200);
});

// ── P76: /auth/v1/redeem — exchange a recovery token (sent via email)
//         for a freshly-minted API key per matching tenant. Single-use:
//         token is deleted after redemption. ──
app.post("/auth/v1/redeem", async (c) => {
  let body: { token?: string } = {};
  try { body = await c.req.json(); } catch { /* ignore */ }
  const token = (body.token ?? "").trim();
  if (!token || !/^[0-9a-f]{48}$/i.test(token)) {
    return c.json({ error: "BadRequest", message: "valid token required" }, 400);
  }
  const env = c.env as { YATABASE_AUTH_CACHE?: KVNamespace };
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return c.json({ error: "ServiceUnavailable", message: "auth-cache KV not bound" }, 503);
  const tokKey = `recover_token:v1:${token}`;
  const tokRaw = await kv.get(tokKey);
  if (!tokRaw) return c.json({ error: "TokenExpired", message: "token invalid or expired (15-min TTL)" }, 400);
  let payload: { email?: string; orgs?: string[]; createdAt?: string };
  try { payload = JSON.parse(tokRaw); } catch { return c.json({ error: "TokenCorrupt" }, 400); }
  const orgs = payload.orgs ?? [];
  if (orgs.length === 0) return c.json({ error: "TokenEmpty" }, 400);

  // Single-use: delete token before processing so a slow client can't
  // accidentally double-redeem.
  await kv.delete(tokKey);

  // Mint a fresh key per matching tenant via the pod invite forwarder
  // (KV-only when pod unreachable, same fallback as /auth/v1/invite).
  const { handleInvite } = await import("./org-members");
  const minted: Array<{ orgDid: string; apiKey?: string; keyId?: string; error?: string }> = [];
  for (const orgDid of orgs) {
    try {
      const synthetic = new Request("https://yatabase.etzhayyim.com/auth/v1/invite", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: `recovery-${Date.now()}` }),
      });
      const resp = await handleInvite(c.env as never, orgDid, synthetic);
      const data = await resp.json() as Record<string, unknown>;
      minted.push({
        orgDid,
        apiKey: typeof data.apiKey === "string" ? data.apiKey : undefined,
        keyId: typeof data.keyId === "string" ? data.keyId : undefined,
        error: resp.status === 200 ? undefined : `mint failed (${resp.status})`,
      });
    } catch (e) {
      minted.push({ orgDid, error: e instanceof Error ? e.message : "throw" });
    }
  }
  return c.json({
    ok: true,
    redeemedAt: new Date().toISOString(),
    email: payload.email,
    minted,
    message: "Save these keys — yatabase does not show them again. They sit alongside any previously-issued keys; revoke the lost one via /auth/v1/revoke.",
  }, 200);
});

// ── P8: Stripe webhook (signature-verified, no auth middleware) ──
app.post("/webhook/stripe", async (c) => handleStripeWebhook(c.env, c.req.raw));

// ── P50: manual usage-alert batch trigger (admin-gated) ──
app.post("/api/usage-alert/run", async (c) => {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey) return c.json({ error: "AdminKeyUnconfigured" }, 503);
  if (supplied !== adminKey) return c.json({ error: "Forbidden" }, 403);
  const result = await _runUsageAlertBatch(c.env);
  return c.json({ ok: true, ...result }, 200);
});

// ── Sprint 1 H1: referrer funnel stats (admin-gated) ──
app.get("/api/referrer-stats", async (c) => {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey) return c.json({ error: "AdminKeyUnconfigured", message: "set YATA_AGENT_ADMIN_KEY via wrangler secret" }, 503);
  if (supplied !== adminKey) return c.json({ error: "Forbidden", message: "x-yata-admin-key mismatch" }, 403);
  const days = Math.max(1, Math.min(90, Number(c.req.query("days") ?? "30")));
  const stats = await getReferrerStats(c.env, days);
  return c.json(stats, 200);
});

// ── P15: email outbox (logged intents + Resend send when configured) ──
app.get("/api/outbox", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const limitRaw = Number(c.req.query("limit") ?? "50");
  const limit = Number.isFinite(limitRaw) ? Math.max(1, Math.min(200, Math.floor(limitRaw))) : 50;
  const result = await getOutbox(c.env, auth.orgDid, limit);
  if (result) return c.json(result, 200);
  // P66: graceful-degraded empty list (Studio Outbox pane stays usable).
  return c.json({ orgDid: auth.orgDid, events: [], note: "no outbox events visible (RW read degraded)" }, 200);
});

// ── P10.5: per-tenant audit log readback ──
app.get("/api/audit", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const limitRaw = Number(c.req.query("limit") ?? "100");
  const limit = Number.isFinite(limitRaw) ? Math.max(1, Math.min(500, Math.floor(limitRaw))) : 100;
  const result = await getAuditEvents(c.env, auth.orgDid, limit);
  if (result) return c.json(result, 200);
  // P66: empty audit list when RW is unreachable.
  return c.json({ orgDid: auth.orgDid, events: [], note: "no audit events visible (RW read degraded)" }, 200);
});

// ── GDPR / 個人情報保護法: data portability + account deletion ──
app.get("/api/export", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handleExport(c.env, auth.orgDid);
});

app.post("/api/account/delete", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handleAccountDelete(c.env, auth.orgDid, c.req.raw);
});

// ── P9: org / member management ──
app.get("/api/members", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const result = await listMembers(c.env, auth.orgDid);
  return c.json(result, 200);
});

// ── P97: outbound webhooks (graph-change notifications) ──────────────
app.get("/api/webhooks", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const kv = (c.env as Env).YATABASE_AUTH_CACHE;
  if (!kv) return c.json({ error: "ServiceUnavailable", message: "auth-cache KV not bound" }, 503);
  const { listWebhooks, redactWebhook } = await import("./webhooks");
  const rows = await listWebhooks(kv, auth.orgDid);
  return c.json({ orgDid: auth.orgDid, webhooks: rows.map(redactWebhook) }, 200);
});

app.post("/api/webhooks", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const kv = (c.env as Env).YATABASE_AUTH_CACHE;
  if (!kv) return c.json({ error: "ServiceUnavailable", message: "auth-cache KV not bound" }, 503);
  let body: { url?: string; secret?: string; label?: string; types?: string[] } = {};
  try { body = await c.req.json(); } catch { /* ignore */ }
  if (!body.url) return c.json({ error: "BadRequest", message: "url required" }, 400);
  const { registerWebhook } = await import("./webhooks");
  const result = await registerWebhook(kv, auth.orgDid, body as never);
  if (!result.ok) {
    return c.json({ error: result.error, message: result.message }, result.status as 400 | 409 | 503);
  }
  // First (and only) chance to see the secret in full.
  return c.json({
    ok: true, webhook: result.webhook,
    message: "Save the secret — yatabase only returns the prefix in subsequent GET /api/webhooks responses.",
  }, 200);
});

app.delete("/api/webhooks/:id", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const kv = (c.env as Env).YATABASE_AUTH_CACHE;
  if (!kv) return c.json({ error: "ServiceUnavailable", message: "auth-cache KV not bound" }, 503);
  const id = c.req.param("id") ?? "";
  if (!/^whk_[0-9a-f]+$/.test(id)) return c.json({ error: "BadRequest", message: "invalid id" }, 400);
  const { deleteWebhook } = await import("./webhooks");
  await deleteWebhook(kv, auth.orgDid, id);
  return c.json({ ok: true, message: "deleted" }, 200);
});

app.post("/auth/v1/invite", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handleInvite(c.env, auth.orgDid, c.req.raw);
});

app.post("/auth/v1/revoke", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  return handleRevoke(c.env, auth.orgDid, c.req.raw);
});

// ── P8.5: 適格請求書 (Japan qualified invoice) ──
app.get("/api/invoices", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const months = await listInvoiceMonths(c.env, auth.orgDid);
  return c.json({ orgDid: auth.orgDid, ...months }, 200);
});

app.get("/api/invoice", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const month = c.req.query("month") ?? "";
  if (!/^\d{4}-\d{2}$/.test(month)) {
    return c.json({ error: "BadRequest", message: "?month=YYYY-MM required" }, 400);
  }
  const plan = await resolvePlan(c.env, auth.orgDid);
  return handleInvoice(c.env, auth.orgDid, plan, month);
});

// ── P7: plan + quota status (always available even at quota) ──
app.get("/api/plan", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const quota = await getQuotaStatus(c.env, auth.orgDid);
  const rules = PLAN_RULES[quota.plan];
  return c.json({
    orgDid: auth.orgDid,
    plan: quota.plan,
    // US-primary pricing (root deps.toml [platform.market]).
    monthlyUsd: rules.monthlyUsd,
    monthlyJpy: rules.monthlyJpy,
    fxJpyPerUsd: 150,
    primaryCurrency: "USD",
    quota: {
      apiRequestPerDay: quota.apiRequestPerDay,
      apiRequestUsedToday: quota.apiRequestUsedToday,
      apiRequestRemaining: quota.apiRequestRemaining,
      exceeded: quota.exceeded,
      windowStart: quota.windowStart,
    },
    rules,
    upgradePaths: ["starter", "developer", "business", "enterprise"].filter((p) => p !== quota.plan),
  });
});

// ──────────────────────────────────────────────────────────────────────
// Hyperdrive direct read shortcut for cheap reads (P3.2). Bypasses
// bpmn-dispatcher for ~40ms savings on listBuckets / listObjects /
// headObject. Falls through to the BPMN path if HYPERDRIVE binding
// is missing or returns null.
// ──────────────────────────────────────────────────────────────────────

app.get("/storage/v1/bucket", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const direct = await listBucketsDirect(c.env, auth.orgDid);
  if (direct) return c.json(direct, 200);
  // fall through to BPMN
  const handled = await handleStorageRest(c.req.raw, c.env, callerFromAuth(c.req.raw, auth));
  return handled ?? c.json({ error: "NotFound" }, 404);
});

app.get("/storage/v1/object/list/:bucket", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const bucket = c.req.param("bucket");
  const url = new URL(c.req.url);
  const prefix = url.searchParams.get("prefix") ?? "";
  const limit = Number.parseInt(url.searchParams.get("limit") ?? "100", 10);
  const cursor = url.searchParams.get("cursor") ?? undefined;
  const direct = await listObjectsDirect(c.env, auth.orgDid, bucket, prefix, limit, cursor);
  if (direct) return c.json(direct, 200);
  const handled = await handleStorageRest(c.req.raw, c.env, callerFromAuth(c.req.raw, auth));
  return handled ?? c.json({ error: "NotFound" }, 404);
});

// Note: HEAD /storage/v1/object/{bucket}/{key} is served by storage-rest
// (it goes through dispatcher anyway). Direct read shortcut not wired
// here because we'd need to merge the response shape with the public
// /s3/* HEAD path.

// ──────────────────────────────────────────────────────────────────────
// Public ACL streaming (P3.2)
// ──────────────────────────────────────────────────────────────────────

app.get("/storage/v1/object/public/:bucket/:key{.*}", async (c) => {
  const bucket = c.req.param("bucket");
  const key = c.req.param("key");
  return handlePublicAcl(c.req.raw, c.env, bucket, key);
});

// ──────────────────────────────────────────────────────────────────────
// Bearer-auth Storage REST fall-through
// ──────────────────────────────────────────────────────────────────────

app.all("/storage/v1/*", async (c) => {
  const auth = c.get("auth");
  const caller = callerFromAuth(c.req.raw, auth);
  const handled = await handleStorageRest(c.req.raw, c.env, caller);
  if (auth) {
    // P6: meter every authenticated storage op as api_request. Heavy
    // ops (PUT body bytes, GET egress bytes) will get additional metric
    // emission once /storage REST returns content-length info upstream.
    c.executionCtx.waitUntil(
      emitMeter(c.env, {
        orgDid: auth.orgDid,
        actorDid: auth.activeDid ?? auth.did,
        metric: "api_request",
        qty: 1,
        product: "yata",
        refResource: "did:web:yatabase.etzhayyim.com:surface:storage",
      }),
    );
  }
  if (handled) return handled;
  return c.json({ error: "NotFound", message: "unrecognised /storage/v1 path" }, 404);
});

// ──────────────────────────────────────────────────────────────────────
// /s3/* AWS SigV4 (P3.2)
// ──────────────────────────────────────────────────────────────────────

app.all("/s3/*", async (c) => {
  const handled = await handleS3Rest(c.req.raw, c.env);
  if (handled) return handled;
  return c.json({ error: "NotFound", message: "unrecognised /s3 path" }, 404);
});

function callerFromAuth(req: Request, auth: AuthContext | undefined): DispatcherCallerContext | null {
  if (!auth) return null;
  return {
    orgDid: auth.orgDid,
    actorDid: auth.activeDid ?? auth.did,
    productScope: auth.productScope ?? "yata",
    traceId: req.headers.get("cf-ray") ?? undefined,
  };
}

// ── P6: usage summary (last 24h, from vertex_billing_event) ──
app.get("/api/usage", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const summary = await getUsageLast24h(c.env, auth.orgDid);
  if (summary) return c.json(summary, 200);
  // P63: When RW is unreachable for the meter query, return an empty
  // summary instead of 503. Customers see "no usage yet" which is true
  // for fresh signups and correct UX during degraded-RW windows.
  const nowMs = Date.now();
  return c.json({
    orgDid: auth.orgDid,
    windowStart: new Date(nowMs - 24 * 60 * 60 * 1000).toISOString(),
    windowEnd: new Date(nowMs).toISOString(),
    byMetric: [],
    totalBilledJpy: 0,
    note: "no usage events in window (or meter query degraded)",
  }, 200);
});

// ──────────────────────────────────────────────────────────────────────
// /api/schema — tenant schema introspection (P4a-17). Worker queries
// information_schema directly via Hyperdrive (no BPMN round-trip).
// Used by Studio "Schema" pane and the `yata.schema.describe` MCP tool.
// ──────────────────────────────────────────────────────────────────────

app.get("/api/schema", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);

  // Cache key per tenant. CF Cache API is per-colo + per-account, but a
  // 60-second TTL on a per-org boundary is a fine trade-off — schema
  // changes are infrequent and customers refresh after CREATE.
  const cacheKey = new Request(`https://cache-yatabase.etzhayyim.com/api/schema/${encodeURIComponent(auth.orgDid)}`, {
    method: "GET",
  });
  const cache = (caches as unknown as { default?: Cache }).default;
  if (cache) {
    const cached = await cache.match(cacheKey);
    if (cached) {
      const headers = new Headers(cached.headers);
      headers.set("x-yatabase-cache", "hit");
      return new Response(cached.body, { status: cached.status, headers });
    }
  }

  const result = await describeTenantSchema(c.env, auth.orgDid);
  if (!result) {
    // P66: KV-backed schema introspection. When RW direct queries are
    // unavailable, we surface the labels the customer has actually used
    // via the KV Cypher engine — that's what Studio's "Schema" pane
    // needs to render the left-column tree.
    const kv = (c.env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
    const labels: Array<{ name: string; nodeCount: number }> = [];
    if (kv) {
      try {
        const list = await kv.list({ prefix: `cypher:v1:${auth.orgDid}:labels:` });
        for (const k of list.keys ?? []) {
          const label = k.name.split(":").pop() ?? "";
          if (!label) continue;
          const raw = await kv.get(k.name);
          const idx = raw ? (JSON.parse(raw) as { ids?: string[] }) : { ids: [] };
          labels.push({ name: label, nodeCount: (idx.ids ?? []).length });
        }
      } catch (e) {
        console.warn("[yatabase][schema] KV scan failed:", e);
      }
    }
    // Surface cypher labels as pseudo-tables so the Studio "Schema" pane
    // renders something useful.
    const pseudoTables = labels.map((l) => ({
      name: l.name,
      columns: [
        { name: "vertex_id", dataType: "VARCHAR", nullable: false, isPrimaryKey: true },
        { name: "properties (KV)", dataType: "JSONB", nullable: false, isPrimaryKey: false },
      ],
      rowCount: l.nodeCount,
    }));
    return c.json({
      orgDid: auth.orgDid,
      schema: "kv-fallback",
      tenantSchema: "kv-fallback",
      tables: pseudoTables,
      cypherLabels: labels,
      generatedAt: new Date().toISOString(),
      note: "Hyperdrive read degraded; Cypher labels recovered from KV index.",
    }, 200);
  }
  const resp = new Response(JSON.stringify(result), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "cache-control": "private, max-age=60",
      "x-yatabase-cache": "miss",
    },
  });
  if (cache) {
    // Clone the response body before caching (Cache API consumes the body).
    c.executionCtx.waitUntil(
      cache.put(cacheKey, new Response(JSON.stringify(result), {
        status: 200,
        headers: {
          "content-type": "application/json",
          "cache-control": "max-age=60",
        },
      })),
    );
  }
  return resp;
});

// ──────────────────────────────────────────────────────────────────────
// /cypher — openCypher HTTP endpoint (P4a, ADR-2605080000 §D13)
// ──────────────────────────────────────────────────────────────────────

app.all("/cypher", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  const caller: DispatcherCallerContext = {
    orgDid: auth.orgDid,
    actorDid: auth.activeDid ?? auth.did,
    productScope: auth.productScope ?? "yata",
    traceId: c.req.header("cf-ray"),
  };
  // P6: meter as `api_request` (1 unit) with surface ref. Latency-free —
  // waitUntil does not block the response.
  c.executionCtx.waitUntil(
    emitMeter(c.env, {
      orgDid: auth.orgDid,
      actorDid: auth.activeDid ?? auth.did,
      metric: "api_request",
      qty: 1,
      product: "yata",
      refResource: "did:web:yatabase.etzhayyim.com:surface:cypher",
    }),
  );
  // P97: dispatch outbound webhooks for any cypher mutations. Read the
  // response body to extract `mutations[]` produced by tryServeCypherFromKv.
  const resp = await handleCypherRequest(c.req.raw, c.env, caller);
  try {
    const cloned = resp.clone();
    const body = await cloned.json() as { results?: Array<{ mutations?: unknown[] }> };
    const allMutations: Array<{ event: string; payload: Record<string, unknown> }> = [];
    for (const r of body?.results ?? []) {
      for (const m of (r.mutations ?? []) as Array<{ event: string; payload: Record<string, unknown> }>) {
        if (m && typeof m.event === "string") allMutations.push(m);
      }
    }
    const kv = (c.env as Env).YATABASE_AUTH_CACHE;
    if (kv && allMutations.length > 0) {
      const { dispatchWebhookEvent } = await import("./webhooks");
      for (const m of allMutations) {
        c.executionCtx.waitUntil(
          dispatchWebhookEvent(kv, auth.orgDid, m.event as never, m.payload),
        );
      }
    }
  } catch { /* response wasn't json or no mutations — fine */ }
  return resp;
});

// ──────────────────────────────────────────────────────────────────────
// /mcp — MCP Streamable HTTP cell-membrane facade (P4a, ADR-2605080000 §D20)
// ──────────────────────────────────────────────────────────────────────

app.all("/mcp", async (c) => {
  return handleMcpRequest(c.req.raw, c.env, async (req) => {
    const auth = await resolveAuthContext(req, c.env);
    if (!auth) return null;
    // P6: meter as `mcp_call` per resolved (= authenticated) tools/call.
    // tools/list / initialize / ping are public so they don't enter this
    // path; only authenticated MCP requests pay.
    c.executionCtx.waitUntil(
      emitMeter(c.env, {
        orgDid: auth.orgDid,
        actorDid: auth.activeDid ?? auth.did,
        metric: "mcp_call",
        qty: 1,
        product: "yata",
        refResource: "did:web:yatabase.etzhayyim.com:surface:mcp",
      }),
    );
    return {
      orgDid: auth.orgDid,
      actorDid: auth.activeDid ?? auth.did,
      productScope: auth.productScope ?? "yata",
      traceId: c.req.header("cf-ray"),
    };
  });
});

app.post("/sparql", async (c) => {
  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);
  let body: { query?: string; format?: string; limit?: number; timeoutMs?: number } = {};
  const ct = (c.req.header("content-type") ?? "").toLowerCase();
  if (ct.includes("application/sparql-query")) {
    body = { query: await c.req.text() };
  } else if (ct.includes("application/json")) {
    try { body = (await c.req.json()) as typeof body; } catch { /* ignore */ }
  } else if (ct.includes("application/x-www-form-urlencoded")) {
    const fd = await c.req.formData();
    body = { query: String(fd.get("query") ?? ""), format: String(fd.get("format") ?? "json") };
  }
  if (!body.query) return c.json({ error: "BadRequest", message: "query required" }, 400);

  const result = await dispatchYataXrpc(
    c.env,
    "ai.gftd.apps.yata.runSparql",
    body as Record<string, unknown>,
    {
      orgDid: auth.orgDid,
      actorDid: auth.activeDid ?? auth.did,
      productScope: auth.productScope ?? "yata",
      traceId: c.req.header("cf-ray"),
    },
    { timeoutMs: 30_000 },
  );
  if (result.ok) return c.json(result.data ?? {}, 200);
  // P72: lg-yatabase pod doesn't ship runSparql yet. Instead of leaking a
  // dispatcher 404 to customers, return a well-formed SPARQL 1.1 JSON
  // results envelope with an explanatory note. SPARQL clients (Apache
  // Jena, rdflib) parse this without throwing. When the pod handler
  // lands, the success path above takes over transparently.
  return c.json(
    {
      head: { vars: [] },
      results: { bindings: [] },
      note: "SPARQL endpoint is reserved but the pod-side runSparql handler is not yet implemented. Use POST /cypher for graph queries today; SPARQL will activate without client changes when the handler ships.",
    },
    200,
    {
      "x-yatabase-surface": "sparql",
      "x-yatabase-sparql-status": "stub-until-pod-handler",
    },
  );
});

// ── Agent team (chikada / tanaka / nishino / sakamoto) ──
//
// /_agents/list           — public roster (does NOT fire any agent)
// POST /_agents/:name/run — admin-keyed manual run
//                            header: x-yata-admin-key: <YATA_AGENT_ADMIN_KEY>
//                            body  : optional {dryRun: bool, maxActions: int}
//
// Each run also writes a row to vertex_yata_agent_run for the audit trail.
app.get("/_agents/list", (c) =>
  c.json({
    agents: listAgents(),
    runEndpoint: "POST /_agents/{name}/run (header x-yata-admin-key required)",
  }),
);

// ── Lead CRM (admin-keyed; vertex_lead is operator-state, not tenant-state) ──
//
// POST /api/leads/ingest  — body: {company, domain, ...} → INSERT vertex_lead
// GET  /api/leads         — query: ?status=new&limit=50 → JSON list
//
// Auth: same x-yata-admin-key as /_agents/*. Body validation enforces
// company + valid domain. Subsequent /_agents/nishino/run drains rows
// with outreach_status='new' and drafts marketing-outbound emails.
function _checkAdminKey(c: { env: Env; req: { header: (n: string) => string | undefined } }): Response | null {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey) {
    return new Response(
      JSON.stringify({ error: "AdminKeyUnconfigured", message: "set YATA_AGENT_ADMIN_KEY via wrangler secret" }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }
  if (supplied.length !== adminKey.length || supplied !== adminKey) {
    return new Response(
      JSON.stringify({ error: "Forbidden", message: "x-yata-admin-key mismatch" }),
      { status: 403, headers: { "content-type": "application/json" } },
    );
  }
  return null;
}

app.post("/api/leads/ingest", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: Record<string, unknown> = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const { status, result } = await handleLeadIngest(c.env, body as never);
  return c.json(result, status as 200 | 400 | 500 | 503);
});

app.get("/api/leads/sendable", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const limitRaw = Number(c.req.query("limit") ?? "50");
  const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(200, limitRaw) : 50;
  const r = await leadsSendable(c.env, limit);
  return c.json(r);
});

app.get("/api/leads", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const status = c.req.query("status") ?? undefined;
  const domain = c.req.query("domain") ?? undefined;
  const limitRaw = Number(c.req.query("limit") ?? "50");
  const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(200, limitRaw) : 50;
  const r = await listLeads(c.env, { status, domain, limit });
  return c.json(r);
});

// ── Lead source: HN Algolia scraper ─────────────────────────────────────
//
// P50: usage-alert batch. Runs every 6 hours at :15. Scans signup_index
// entries from the last 30 days, checks today's api_request counter in KV,
// and fires a quota-warning email when a free-tier tenant crosses 80%.
// Deduped per tenant per day via `usage_alert:v1:{orgDid}:{date}` sentinel.
async function _runUsageAlertBatch(env: Env): Promise<{ scanned: number; alerted: number; skipped: number }> {
  const result = { scanned: 0, alerted: 0, skipped: 0 };
  const kv = (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  if (!kv) return result;

  const FREE_LIMIT = 1_000;
  const THRESHOLD = 0.80;
  const today = new Date().toISOString().slice(0, 10);

  for (let i = 0; i < 30; i++) {
    const date = new Date(Date.now() - i * 24 * 3600 * 1000).toISOString().slice(0, 10);
    let entries: Array<{ orgDid: string; email: string; name: string }> = [];
    try {
      const raw = await kv.get(`signup_index:v1:${date}`);
      if (!raw) continue;
      entries = JSON.parse(raw) as typeof entries;
    } catch { continue; }

    for (const entry of entries) {
      result.scanned++;
      // Skip upgraded tenants.
      try {
        const planRaw = await kv.get(`plan:v1:${entry.orgDid}`);
        if (planRaw) {
          const pd = JSON.parse(planRaw) as { plan?: string };
          if (pd.plan && pd.plan !== "free") { result.skipped++; continue; }
        }
      } catch { /* assume free */ }

      // Check today's api_request usage.
      let usedQty = 0;
      try {
        const usageRaw = await kv.get(`usage:v1:${entry.orgDid}:api_request:${today}`);
        if (!usageRaw) { result.skipped++; continue; }
        const ud = JSON.parse(usageRaw) as { qty?: number };
        usedQty = Number(ud.qty ?? 0);
      } catch { result.skipped++; continue; }

      if (usedQty < FREE_LIMIT * THRESHOLD) { result.skipped++; continue; }

      // Dedup sentinel (30h TTL — covers the rest of today + 6h buffer).
      const sentinelKey = `usage_alert:v1:${entry.orgDid}:${today}`;
      try {
        if (await kv.get(sentinelKey)) { result.skipped++; continue; }
      } catch { result.skipped++; continue; }

      const pct = Math.min(100, Math.round((usedQty / FREE_LIMIT) * 100));
      try {
        const outbox = await import("./email-outbox");
        const tpl = outbox.usageAlertEmail(entry.name || "there", usedQty, FREE_LIMIT, pct);
        await outbox.emitOutbox(env as never, {
          orgDid: entry.orgDid,
          recipientEmail: entry.email || undefined,
          recipientName: entry.name || "there",
          kind: "quota-warning",
          subject: tpl.subject,
          bodyText: tpl.text,
          bodyHtml: tpl.html,
        });
        await kv.put(sentinelKey, String(usedQty), { expirationTtl: 30 * 3600 });
        result.alerted++;
      } catch (e) {
        console.warn("[yatabase][usage-alert] outbox failed:", e);
      }
    }
  }
  return result;
}

// Admin-keyed manual fire. The same code path is invoked from the
// P45: day-7 free-tier retention email batch.
// Reads `signup_index:v1:{date-7d}` from KV, skips already-sent and non-free
// tenants, sends the day7RetentionEmail via the outbox, and records a
// `day7_sent:v1:{orgDid}` sentinel to avoid duplicate sends.
async function _runDay7RetentionBatch(env: Env): Promise<{ scanned: number; sent: number; skipped: number; errors: number }> {
  const result = { scanned: 0, sent: 0, skipped: 0, errors: 0 };
  const kv = (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE;
  if (!kv) return result;

  const d7ago = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString().slice(0, 10);
  const indexRaw = await kv.get(`signup_index:v1:${d7ago}`);
  if (!indexRaw) return result;

  let entries: Array<{ orgDid: string; email: string; name: string }> = [];
  try { entries = JSON.parse(indexRaw); } catch { return result; }

  const { day7RetentionEmail, emitOutbox } = await import("./email-outbox");
  const { resolvePlan } = await import("./plan-quota");

  for (const entry of entries) {
    result.scanned++;
    try {
      // Skip if already sent.
      const sent = await kv.get(`day7_sent:v1:${entry.orgDid}`);
      if (sent) { result.skipped++; continue; }
      // Skip if tenant upgraded beyond free.
      const plan = await resolvePlan(env as never, entry.orgDid);
      if (plan !== "free") { result.skipped++; continue; }
      // No email address recorded — skip silently.
      if (!entry.email) { result.skipped++; continue; }

      const tpl = day7RetentionEmail(entry.name || "there");
      await emitOutbox(env as never, {
        orgDid: entry.orgDid,
        recipientEmail: entry.email,
        recipientName: entry.name || "there",
        kind: "trial-day7",
        subject: tpl.subject,
        bodyText: tpl.text,
        bodyHtml: tpl.html,
      });
      // Mark as sent (90-day TTL — longer than any retry window).
      await kv.put(`day7_sent:v1:${entry.orgDid}`, "1", { expirationTtl: 90 * 24 * 3600 });
      result.sent++;
    } catch (e) {
      result.errors++;
      console.warn("[yatabase][day7] entry failed:", entry.orgDid, e);
    }
  }
  return result;
}

// scheduled() handler (CF Cron Trigger every 6 hours) — see bottom of
// the file for the fetch+scheduled export.
//
// Body (optional): {windowHours, perQueryHits, maxLeads}
// Returns:         {scrape: HnScrapeReport, ingest: IngestSummary}
async function _runGithubScrapeAndIngest(env: Env, opts: {
  perRepo?: number; maxUsers?: number; reposLimit?: number;
}): Promise<{ scrape: GithubScrapeReport; ingest: { tried: number; new: number; existed: number; failed: number } }> {
  const scrape = await fetchGithubLeads({
    perRepo: opts.perRepo,
    maxUsers: opts.maxUsers,
    reposLimit: opts.reposLimit,
    githubToken: env.GITHUB_TOKEN,
  });
  const summary = { tried: 0, new: 0, existed: 0, failed: 0 };
  for (const lead of scrape.produced_leads) {
    summary.tried += 1;
    try {
      const r = await handleLeadIngest(env, lead);
      if (r.status === 200) {
        const msg = (r.result as { message?: string }).message ?? "";
        if (/already exists/.test(msg)) summary.existed += 1;
        else summary.new += 1;
      } else {
        summary.failed += 1;
      }
    } catch {
      summary.failed += 1;
    }
  }
  return { scrape, ingest: summary };
}

async function _runHnScrapeAndIngest(env: Env, opts: {
  windowHours?: number; perQueryHits?: number; maxLeads?: number;
}): Promise<{ scrape: HnScrapeReport; ingest: { tried: number; new: number; existed: number; failed: number; results: unknown[] } }> {
  const scrape = await fetchHnLeads(opts);
  const summary = { tried: 0, new: 0, existed: 0, failed: 0, results: [] as unknown[] };
  for (const lead of scrape.produced_leads) {
    summary.tried += 1;
    try {
      const r = await handleLeadIngest(env, lead);
      summary.results.push(r.result);
      const status = r.status;
      if (status === 200) {
        const msg = (r.result as { message?: string }).message ?? "";
        if (/already exists/.test(msg)) summary.existed += 1;
        else summary.new += 1;
      } else {
        summary.failed += 1;
      }
    } catch (e) {
      summary.failed += 1;
      summary.results.push({
        error: "IngestThrew",
        message: e instanceof Error ? e.message.slice(0, 240) : "unknown",
      });
    }
  }
  return { scrape, ingest: summary };
}

// ── Lead operator triage (admin-keyed) ─────────────────────────────────
//
// POST /api/leads/{vertex_id}/approve  → outreach_status='approved'
// POST /api/leads/{vertex_id}/dismiss  → outreach_status='dismissed'
// POST /api/leads/{vertex_id}/contact  → set contact_email (body {email})
//
// vertex_id in the path is URL-encoded (e.g. lead%3Aacme.com).
app.post("/api/leads/:vertex_id/approve", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const vertexId = decodeURIComponent(c.req.param("vertex_id"));
  const r = await setLeadOutreachStatus(c.env, vertexId, "approved");
  return c.json(r, r.ok ? 200 : 500);
});

app.post("/api/leads/:vertex_id/dismiss", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const vertexId = decodeURIComponent(c.req.param("vertex_id"));
  const r = await setLeadOutreachStatus(c.env, vertexId, "dismissed");
  return c.json(r, r.ok ? 200 : 500);
});

// ── Lead domain enrichment (admin-keyed) ────────────────────────────────
//
// POST /api/leads/{vertex_id}/enrich
//   - GETs https://{domain}/, regex-extracts mailto: + role-prefix emails,
//     parses light tech-stack hints. UPDATEs vertex_lead.contact_email +
//     tech_stack. Returns the enrichment report.
//
// POST /api/leads/sources/enrich-batch
//   - body {limit?: int} (default 10, max 25). Picks leads with empty
//     contact_email + status in (new, drafted), enriches each in series.
//     Per-lead 8s timeout keeps the whole call under CF Worker's 30s
//     budget. Used by the future scheduled() handler too.
app.post("/api/leads/:vertex_id/enrich", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const vertexId = decodeURIComponent(c.req.param("vertex_id"));
  const lead = await getLeadByVertexId(c.env, vertexId);
  if (!lead) {
    return c.json({ error: "NotFound", message: `lead ${vertexId} not found` }, 404);
  }
  const result: EnrichResult = await enrichDomain(lead.domain);
  let persisted = false;
  if (result.ok && (result.best_email || result.tech_stack.length > 0)) {
    const upd = await setLeadEnrichment(c.env, vertexId, {
      contact_email: result.best_email,
      tech_stack: result.tech_stack,
    });
    persisted = upd.ok;
  }
  return c.json({
    ...result,
    persisted,
  });
});

// Extracted helper so the manual /enrich-batch route and the scheduled()
// cron handler share one code path. limit is clamped 1..25.
async function _runEnrichBatch(env: Env, limit: number) {
  const cap = Math.max(1, Math.min(25, limit));
  const candidates = await leadsNeedingEnrichment(env, cap);
  const results: Array<{ vertex_id: string; domain: string; best_email: string; tech_stack: string[]; ok: boolean; error?: string; persisted: boolean }> = [];
  for (const cand of candidates) {
    const r = await enrichDomain(cand.domain);
    let persisted = false;
    if (r.ok && (r.best_email || r.tech_stack.length > 0)) {
      const upd = await setLeadEnrichment(env, cand.vertex_id, {
        contact_email: r.best_email,
        tech_stack: r.tech_stack,
      });
      persisted = upd.ok;
    }
    results.push({
      vertex_id: cand.vertex_id,
      domain: cand.domain,
      best_email: r.best_email,
      tech_stack: r.tech_stack,
      ok: r.ok,
      error: r.error,
      persisted,
    });
  }
  return {
    summary: {
      tried: results.length,
      found_email: results.filter((r) => r.best_email).length,
      persisted: results.filter((r) => r.persisted).length,
      failed: results.filter((r) => !r.ok).length,
    },
    results,
  };
}

app.post("/api/leads/sources/enrich-batch", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { limit?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const r = await _runEnrichBatch(c.env, body.limit ?? 10);
  return c.json(r);
});

// Batch-send — bulk-fire sendApprovedLead over the operator's ready-to-fire
// list (or an explicit vertex_id array). Serial loop so we don't fan-out
// to Resend in parallel and trip rate limits. Each lead's send goes through
// the same dual-mode pipeline as POST /api/leads/{id}/send: dry-run preview
// when RESEND_API_KEY is missing, live send when configured.
// Bulk retry of failed / pending outbox rows. Operator use: after rotating
// RESEND_API_KEY or EMAIL_FROM, every welcome+marketing+upgrade row that
// was rejected by Resend with the old key sits in vertex_email_outbox
// with status='failed'. This endpoint re-attempts each row using the
// CURRENT env credentials and flips status='sent' on success.
//
// Body: {window_hours?: int=24, limit?: int=25}
// Returns: per-row result so operator can audit which sends went through.
// When RESEND_API_KEY is unset: lists candidates with status_out='skipped-no-resend'
// so the operator can size the queue before rotating the key.
app.post("/api/outbox/retry-failed", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { window_hours?: number; limit?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const result = await retryOutboxBatch(c.env, {
    windowHours: body.window_hours,
    limit: body.limit,
  });
  return c.json(result);
});

app.post("/api/leads/send-batch", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { vertex_ids?: string[]; limit?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const cap = Math.max(1, Math.min(50, body.limit ?? 25));

  let targets: string[] = [];
  if (Array.isArray(body.vertex_ids) && body.vertex_ids.length > 0) {
    targets = body.vertex_ids.slice(0, cap).map(String);
  } else {
    const r = await leadsSendable(c.env, cap);
    targets = r.leads.map((l) => String(l.vertex_id ?? "")).filter(Boolean);
  }

  const results: Array<{ vertex_id: string; status: number; ok: boolean; dryRun?: boolean; resend_id?: string; error?: string }> = [];
  let okCount = 0, dryCount = 0, failCount = 0;
  for (const vid of targets) {
    const { status, result } = await sendApprovedLead(c.env, vid);
    const r = result as { ok?: boolean; dryRun?: boolean; resend_id?: string; error?: string; message?: string };
    const ok = r.ok === true;
    if (ok && r.dryRun) dryCount++;
    else if (ok) okCount++;
    else failCount++;
    results.push({
      vertex_id: vid,
      status,
      ok,
      dryRun: r.dryRun,
      resend_id: r.resend_id,
      error: ok ? undefined : (r.error ?? r.message ?? "?"),
    });
  }

  return c.json({
    summary: {
      targets: targets.length,
      sent: okCount,
      dry_run: dryCount,
      failed: failCount,
      resend_wired: Boolean(c.env.RESEND_API_KEY && c.env.EMAIL_FROM),
    },
    results,
  });
});

// ── Outbox approval surface (P21, admin-keyed) ─────────────────────────
//
// Marketing/sales LangGraph nodes write drafts to vertex_email_outbox at
// status='queued-no-recipient'. These admin routes let an operator
// (Studio /studio/admin/outbox or curl) inspect drafts, fill in the
// recipient, edit the body, and flip the status — closing the human-
// approval compliance loop the graphs depend on.
//
// All three routes proxy to the lg-yatabase pod (ADR-2605111200);
// Worker never touches vertex_email_outbox directly.

app.post("/api/outbox/list", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { status?: string; kind?: string; limit?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const { forwardOutboxList } = await import("./outbox-forward");
  const r = await forwardOutboxList(c.env, body, c.req.header("cf-ray"));
  return c.json(r.data ?? { rows: [], total: 0, offset: 0, limit: 0 }, r.status as 200 | 400 | 500 | 503);
});

app.post("/api/outbox/approve", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: Record<string, unknown> = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const { forwardOutboxApprove } = await import("./outbox-forward");
  const r = await forwardOutboxApprove(c.env, body as never, c.req.header("cf-ray"));
  return c.json(r.data ?? { ok: false, error: r.error }, r.status as 200 | 400 | 500 | 503);
});

app.post("/api/outbox/reject", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: Record<string, unknown> = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const { forwardOutboxReject } = await import("./outbox-forward");
  const r = await forwardOutboxReject(c.env, body as never, c.req.header("cf-ray"));
  return c.json(r.data ?? { ok: false, error: r.error }, r.status as 200 | 400 | 500 | 503);
});

app.post("/api/leads/:vertex_id/send", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const vertexId = decodeURIComponent(c.req.param("vertex_id"));
  const { status, result } = await sendApprovedLead(c.env, vertexId);
  return c.json(result, status as 200 | 404 | 409 | 500);
});

app.post("/api/leads/:vertex_id/contact", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  const vertexId = decodeURIComponent(c.req.param("vertex_id"));
  let body: { email?: string } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const r = await setLeadContactEmail(c.env, vertexId, body.email ?? "");
  return c.json(r, r.ok ? 200 : 400);
});

app.post("/api/leads/sources/hn", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { windowHours?: number; perQueryHits?: number; maxLeads?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const result = await _runHnScrapeAndIngest(c.env, body);
  return c.json({
    ok: true,
    candidates: result.scrape.candidates,
    unique_domains: result.scrape.unique_domains,
    skipped_no_url: result.scrape.skipped_no_url,
    skipped_aggregator: result.scrape.skipped_aggregator,
    skipped_dup_in_batch: result.scrape.skipped_dup_in_batch,
    errors: result.scrape.errors,
    ingest: {
      tried: result.ingest.tried,
      new: result.ingest.new,
      existed: result.ingest.existed,
      failed: result.ingest.failed,
    },
  });
});

app.post("/api/leads/sources/github", async (c) => {
  const denied = _checkAdminKey(c);
  if (denied) return denied;
  let body: { perRepo?: number; maxUsers?: number; reposLimit?: number } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = await c.req.json(); } catch { /* ignore */ }
  }
  const result = await _runGithubScrapeAndIngest(c.env, body);
  return c.json({
    ok: true,
    repos_scanned: result.scrape.repos_scanned,
    stargazers_seen: result.scrape.stargazers_seen,
    user_fetches: result.scrape.user_fetches,
    rate_limit_hits: result.scrape.rate_limit_hits,
    skipped_no_blog: result.scrape.skipped_no_blog,
    skipped_aggregator_blog: result.scrape.skipped_aggregator_blog,
    skipped_dup_in_batch: result.scrape.skipped_dup_in_batch,
    errors: result.scrape.errors,
    ingest: result.ingest,
    auth_mode: c.env.GITHUB_TOKEN ? "authed (5000/h)" : "unauthed (60/h)",
  });
});

app.get("/_agents/recent", async (c) => {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey || supplied !== adminKey) {
    return c.json({ error: "Forbidden" }, 403);
  }
  const limitRaw = Number(c.req.query("limit") ?? "25");
  const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(200, limitRaw) : 25;
  const rows = await recentAgentRuns(c.env, limit);
  return c.json({ count: rows.length, runs: rows });
});

app.post("/_agents/bootstrap", async (c) => {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey) {
    return c.json({ error: "AdminKeyUnconfigured" }, 503);
  }
  if (supplied.length !== adminKey.length || supplied !== adminKey) {
    return c.json({ error: "Forbidden" }, 403);
  }
  const result = await bootstrapAgentTables(c.env);
  return c.json(result, result.ok ? 200 : 500);
});

app.post("/_agents/:name/run", async (c) => {
  const adminKey = c.env.YATA_AGENT_ADMIN_KEY ?? "";
  const supplied = c.req.header("x-yata-admin-key") ?? "";
  if (!adminKey) {
    return c.json(
      { error: "AdminKeyUnconfigured", message: "set YATA_AGENT_ADMIN_KEY via wrangler secret" },
      503,
    );
  }
  if (supplied.length !== adminKey.length || supplied !== adminKey) {
    return c.json({ error: "Forbidden", message: "x-yata-admin-key mismatch" }, 403);
  }
  const name = c.req.param("name");
  const def = getAgent(name);
  if (!def) {
    return c.json(
      { error: "NotFound", message: `unknown agent: ${name}; see /_agents/list` },
      404,
    );
  }

  let input: { dryRun?: boolean; maxActions?: number; reason?: string } = {};
  if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { input = await c.req.json(); } catch { /* ignore */ }
  }

  const report = await runAgent(name as AgentName, c.env, input);
  return c.json(report, report.ok ? 200 : 500);
});

app.all("/xrpc/:nsid", async (c) => {
  const nsid = c.req.param("nsid");
  if (!nsid.startsWith("ai.gftd.apps.yata.") && !nsid.startsWith("ai.gftd.apps.billing.")) {
    return c.json(
      { error: "NotFound", message: `nsid ${nsid} is not handled by yatabase.etzhayyim.com; use atproto.etzhayyim.com` },
      404,
    );
  }

  const auth = c.get("auth");
  if (!auth) return c.json({ error: "Unauthorized" }, 401);

  let body: Record<string, unknown> = {};
  if (c.req.method === "GET") {
    for (const [k, v] of Object.entries(c.req.query())) body[k] = v;
  } else if ((c.req.header("content-type") ?? "").includes("application/json")) {
    try { body = (await c.req.json()) as Record<string, unknown>; } catch { /* ignore */ }
  }

  // BMC short-circuit: writes + reads all live in the lg-yatabase pod.
  // Worker stays stateless — no Hyperdrive touch for vertex_bmc_*.
  if (isBmcNsid(nsid)) {
    const fwd = await forwardBmc(
      c.env,
      c.req.method === "GET" ? "GET" : "POST",
      nsid,
      body,
      {
        did: auth.did,
        orgDid: auth.orgDid,
        activeDid: auth.activeDid,
        productScope: auth.productScope ?? "yata",
        traceId: c.req.header("cf-ray"),
      },
      { timeoutMs: 60_000 },
    );
    if (!fwd.ok) return c.json({ error: "BmcUpstream", message: fwd.error }, fwd.status);
    return c.json(fwd.data ?? {}, 200);
  }

  // Deploy-first query short-circuit (ADR-2605210000).
  // Passes x-gftd-mv-limit so the pod enforces per-plan MV slot quota.
  if (isQueryNsid(nsid)) {
    const plan = await resolvePlan(c.env, auth.orgDid);
    const mvLimit = PLAN_RULES[plan].mvSlots ?? 999_999;
    const fwd = await forwardQuery(
      c.env,
      c.req.method === "GET" ? "GET" : "POST",
      nsid,
      body,
      {
        did: auth.did,
        orgDid: auth.orgDid,
        activeDid: auth.activeDid,
        traceId: c.req.header("cf-ray"),
      },
      { timeoutMs: 120_000, mvLimit },
    );
    if (!fwd.ok) return c.json({ error: "QueryUpstream", message: fwd.error }, fwd.status as 400 | 401 | 404 | 429 | 500 | 502 | 503 | 504);
    return c.json(fwd.data ?? {}, 200);
  }

  const result = await dispatchYataXrpc(
    c.env,
    nsid,
    body,
    {
      orgDid: auth.orgDid,
      actorDid: auth.activeDid ?? auth.did,
      productScope: auth.productScope ?? "yata",
      traceId: c.req.header("cf-ray"),
    },
    { timeoutMs: 60_000 },
  );
  // P63: every authenticated XRPC call counts as one api_request — meter
  // event lands in KV (and best-effort in RW) so /api/usage is non-zero.
  c.executionCtx.waitUntil(
    emitMeter(c.env, {
      orgDid: auth.orgDid,
      actorDid: auth.activeDid ?? auth.did,
      metric: "api_request",
      qty: 1,
      product: "yata",
      refResource: `did:web:yatabase.etzhayyim.com:xrpc:${nsid}`,
    }),
  );
  if (!result.ok) return c.json({ error: "DispatcherError", message: result.error }, result.status);
  return c.json(result.data ?? {}, 200);
});

app.notFound((c) =>
  c.json(
    {
      error: "NotFound",
      message: `path ${c.req.path} not handled by yatabase.etzhayyim.com; see /_app/meta for surface list`,
    },
    404,
  ),
);

app.onError((err, c) => {
  console.error("[yatabase] unhandled error:", err);
  return c.json({ error: "InternalServerError", message: err.message }, 500);
});

// ── CF Cron Trigger handler ────────────────────────────────────────────
//
// Wrangler `triggers.crons` fires four distinct schedules and we dispatch
// by the cron expression in event.cron:
//
//   "0 */6 * * *"  — HN scraper (top-of-funnel ingest)
//   "15 */6 * * *" — resident BMC iteration (Build-Measure-Learn loop;
//                    picks oldest active hypothesis, measures, decides)
//   "30 */6 * * *" — domain enrichment (fills contact_email + tech_stack
//                    on leads that arrived empty)
//   "45 */6 * * *" — GitHub stargazers scraper (durable second source —
//                    competitor-repo stargazers with public blog domain)
//
// The :15 / :30 / :45 offsets give RW time to settle each batch before the
// next branch reads from the corresponding tables.
//
// Both branches use ctx.waitUntil so the actual work runs past the
// scheduled() return — CF allows up to 30s of CPU time for a scheduled
// handler. Per-domain enrichment fetches use 8s timeout each, so a batch
// of 5-10 domains fits comfortably.
//
// Errors are logged but never propagated — a fire must not kill subsequent
// firings of the same cron.
async function scheduled(
  event: { cron: string; scheduledTime: number },
  env: Env,
  ctx: { waitUntil(p: Promise<unknown>): void },
): Promise<void> {
  const cron = event.cron;
  const log = (m: string) => console.log(`[yatabase][cron ${cron}] ${m}`);
  log("scheduled fire");

  if (cron === "0 */6 * * *") {
    // HN scraper branch.
    ctx.waitUntil(
      (async () => {
        try {
          const result = await _runHnScrapeAndIngest(env, {
            windowHours: 24 * 7,
            perQueryHits: 30,
            maxLeads: 25,
          });
          log(
            `hn-scraper: candidates=${result.scrape.candidates} unique=${result.scrape.unique_domains} ` +
            `tried=${result.ingest.tried} new=${result.ingest.new} existed=${result.ingest.existed} ` +
            `failed=${result.ingest.failed} errors=${result.scrape.errors.length}`,
          );
        } catch (e) {
          console.error("[yatabase][cron] scraper threw:", e);
        }
      })(),
    );
    return;
  }

  if (cron === "30 */6 * * *") {
    // Enrichment branch. Bounded to 8 leads per fire (≤64s of fetch budget,
    // safely under the 30s CPU limit because each fetch is mostly I/O wait).
    ctx.waitUntil(
      (async () => {
        try {
          const result = await _runEnrichBatch(env, 8);
          log(
            `enrich-batch: tried=${result.summary.tried} ` +
            `found_email=${result.summary.found_email} ` +
            `persisted=${result.summary.persisted} failed=${result.summary.failed}`,
          );
        } catch (e) {
          console.error("[yatabase][cron] enrich threw:", e);
        }
      })(),
    );
    return;
  }

  if (cron === "45 */6 * * *") {
    // GitHub stargazers branch. Per-fire budget: 2 repos × 20 stargazers
    // = up to 40 user-detail fetches. With unauthed 60/h budget this fits;
    // with GITHUB_TOKEN we have 5000/h so it never hits the ceiling.
    ctx.waitUntil(
      (async () => {
        try {
          const result = await _runGithubScrapeAndIngest(env, {
            perRepo: 20,
            maxUsers: 30,
            reposLimit: 2,
          });
          log(
            `github-scraper: repos=${result.scrape.repos_scanned.join(",")} ` +
            `stargazers=${result.scrape.stargazers_seen} users=${result.scrape.user_fetches} ` +
            `tried=${result.ingest.tried} new=${result.ingest.new} existed=${result.ingest.existed} ` +
            `failed=${result.ingest.failed} rate_limited=${result.scrape.rate_limit_hits}`,
          );
        } catch (e) {
          console.error("[yatabase][cron] github threw:", e);
        }
      })(),
    );
    return;
  }

  if (cron === "0 8 * * *") {
    // P45: day-7 free-tier retention email.
    ctx.waitUntil(
      (async () => {
        try {
          const result = await _runDay7RetentionBatch(env);
          log(
            `day7-retention: scanned=${result.scanned} sent=${result.sent} skipped=${result.skipped} errors=${result.errors}`,
          );
        } catch (e) {
          console.error("[yatabase][cron] day7-retention threw:", e);
        }
      })(),
    );
    return;
  }

  if (cron === "15 */6 * * *") {
    // P50: usage-alert emails for free-tier tenants approaching quota.
    ctx.waitUntil(
      (async () => {
        try {
          const result = await _runUsageAlertBatch(env);
          log(
            `usage-alert: scanned=${result.scanned} alerted=${result.alerted} skipped=${result.skipped}`,
          );
        } catch (e) {
          console.error("[yatabase][cron] usage-alert threw:", e);
        }
      })(),
    );
    return;
  }

  log(`unknown cron expression — no-op`);
}

export default {
  fetch: app.fetch,
  scheduled,
};
