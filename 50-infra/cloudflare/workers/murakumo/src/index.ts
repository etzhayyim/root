/**
 * murakumo CF Worker — etzhayyim kotoba rewrite (v5.0.0).
 *
 * Per ADR-2605191358 step 2 — replaces the legacy Kysely+Hyperdrive→RisingWave
 * path with `@etzhayyim/sdk` over AT MST + IPFS (when needed) + Base L2. The
 * inference job state machine is event-sourced through two lexicons:
 *   - com.etzhayyim.murakumo.inferenceJob       (immutable header)
 *   - com.etzhayyim.murakumo.inferenceJobEvent  (append-only status events)
 *
 * Platform API keys (`sk_live_*`) are looked up via
 *   com.etzhayyim.murakumo.apiKey (rkey = lowercase hex sha-256 of raw key).
 *
 * Non-substrate concerns (Hono routing, Service-Auth JWT, chat-anon HMAC token,
 * LiteLLM HTTP proxy + SSE keepalive, R2 fleet roster, cron) are preserved
 * verbatim from the upstream worker.
 *
 * Substrate hard rules enforced:
 *   - NO @atproto/api / viem / kysely / @etzhayyim/kotodama-host-sdk direct imports
 *   - NO HYPERDRIVE binding
 *   - All durable state goes through @etzhayyim/sdk
 */

import { Hono, type MiddlewareHandler } from "hono";
import { Etzhayyim } from "@etzhayyim/sdk";
import { MODEL_ALIASES, MODEL_REGISTRY } from "./model-registry.js";
import { CHAT_HTML } from "./chat-html.js";

// ─── Env ────────────────────────────────────────────────────────────

interface Env {
  R2: R2Bucket;
  /** CF Tunnel CNAME to LiteLLM gateway (judah:4000 or equivalent). */
  LITELLM_URL?: string;
  /** LiteLLM master_key (ansible litellm role). */
  LITELLM_MASTER?: string;
  /** Backward-compatible alias for older local configs. */
  LITELLM_MASTER_KEY?: string;
  /** OpenRouter API key for deepseek routing. */
  OPENROUTER_API_KEY?: string;
  /** Emergency break-glass only (ADR-0023 legacy; deprecated). */
  MURAKUMO_API_KEY?: string;
  /** Dev-only insecure fallback. Never set in production. */
  DEV_INSECURE_API_KEY?: string;
  /** HMAC secret for ephemeral browser-chat tokens issued at `/`. */
  MURAKUMO_CHAT_SECRET?: string;

  // ── Etzhayyim SDK config ──
  /** DID this worker writes records under. e.g. did:web:murakumo.etzhayyim.com. */
  MURAKUMO_DID?: string;
  /** Explicit PDS URL override. If unset, SDK resolves via DID document. */
  MURAKUMO_PDS_URL?: string;
  /** Resumable PDS session JSON: {did, handle, accessJwt, refreshJwt}. */
  MURAKUMO_PDS_SESSION?: string;
  /** Fallback handle+password JSON {handle, password} if no session is set. */
  MURAKUMO_PDS_AUTH?: string;
}

// ─── Constants ──────────────────────────────────────────────────────

const CHAT_TOKEN_TTL_MS = 3_600_000; // 1h
const CHAT_TOKEN_PREFIX = "mkc_";
const INFERENCE_TIMEOUT_MS = 300_000;
const STREAM_KEEPALIVE_MS = 20_000;
const HEALTH_TIMEOUT_MS = 5_000;
const ROSTER_CACHE_TTL_MS = 30_000;
const API_KEY_CACHE_TTL_MS = 60_000;
const OPENAI_MODEL_LIST_CREATED_AT = 1_711_929_600;

const COLLECTION_API_KEY = "com.etzhayyim.murakumo.apiKey";
const COLLECTION_JOB = "com.etzhayyim.murakumo.inferenceJob";
const COLLECTION_JOB_EVENT = "com.etzhayyim.murakumo.inferenceJobEvent";

const DEFAULT_MURAKUMO_DID = "did:web:murakumo.etzhayyim.com";

// ─── Etzhayyim SDK lazy singleton ───────────────────────────────────

let sdkInstance: Etzhayyim | null = null;

function sdk(env: Env): Etzhayyim {
  if (sdkInstance) return sdkInstance;
  const did = env.MURAKUMO_DID ?? DEFAULT_MURAKUMO_DID;
  const session = env.MURAKUMO_PDS_SESSION
    ? (JSON.parse(env.MURAKUMO_PDS_SESSION) as {
        did: string;
        handle: string;
        accessJwt: string;
        refreshJwt: string;
      })
    : undefined;
  const auth = !session && env.MURAKUMO_PDS_AUTH
    ? (JSON.parse(env.MURAKUMO_PDS_AUTH) as {
        handle: string;
        password: string;
      })
    : undefined;
  sdkInstance = new Etzhayyim({
    did,
    pdsUrl: env.MURAKUMO_PDS_URL,
    session,
    auth,
  });
  return sdkInstance;
}

// ─── Service Auth JWT verification (Phase 3B, ADR-2605152100) ───────

const _JWKS_URL = "https://authn.etzhayyim.com/.well-known/jwks.json";
const _JWKS_TTL_MS = 3_600_000;
let _jwksCache: { keys: JsonWebKey[]; fetchedAt: number } | null = null;
const _SVC_JWT_ISS_ALLOWLIST = new Set([
  "did:web:kotodama.etzhayyim.com",
]);
const _SVC_JWT_AUD = "did:web:murakumo.etzhayyim.com";

async function _fetchJwks(): Promise<JsonWebKey[] | null> {
  if (_jwksCache && Date.now() - _jwksCache.fetchedAt < _JWKS_TTL_MS)
    return _jwksCache.keys;
  try {
    const resp = await fetch(_JWKS_URL);
    if (!resp.ok) return null;
    const data = (await resp.json()) as { keys?: JsonWebKey[] };
    if (!data.keys?.length) return null;
    _jwksCache = { keys: data.keys, fetchedAt: Date.now() };
    return data.keys;
  } catch {
    return null;
  }
}

function _b64urlToBytes(s: string): Uint8Array {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  return Uint8Array.from(
    atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad),
    (c) => c.charCodeAt(0)
  );
}

async function verifyServiceAuthJwt(
  token: string
): Promise<{ iss: string; aud: string } | null> {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, sigB64] = parts;
  try {
    const payload = JSON.parse(
      new TextDecoder().decode(_b64urlToBytes(payloadB64))
    ) as { iss?: string; aud?: string; exp?: number };
    if (!payload.iss || !payload.aud || !payload.exp) return null;
    if (payload.exp * 1000 < Date.now()) return null;
    if (!_SVC_JWT_ISS_ALLOWLIST.has(payload.iss)) return null;
    if (payload.aud !== _SVC_JWT_AUD) return null;
    const keys = await _fetchJwks();
    if (!keys?.length) return null;
    const cryptoKey = await crypto.subtle.importKey(
      "jwk",
      keys[0],
      { name: "ECDSA", namedCurve: "P-256" },
      false,
      ["verify"]
    );
    const signingInput = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const valid = await crypto.subtle.verify(
      { name: "ECDSA", hash: "SHA-256" },
      cryptoKey,
      _b64urlToBytes(sigB64) as BufferSource,
      signingInput
    );
    return valid ? { iss: payload.iss, aud: payload.aud } : null;
  } catch {
    return null;
  }
}

// ─── Ephemeral chat token (HMAC-SHA256) ─────────────────────────────

function b64urlEncode(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64urlDecode(s: string): Uint8Array {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + pad;
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
}
async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}
async function signChatToken(secret: string): Promise<string> {
  const payload = JSON.stringify({ exp: Date.now() + CHAT_TOKEN_TTL_MS });
  const payloadB64 = b64urlEncode(new TextEncoder().encode(payload));
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(payloadB64)
  );
  return `${CHAT_TOKEN_PREFIX}${payloadB64}.${b64urlEncode(sig)}`;
}
async function verifyChatToken(secret: string, token: string): Promise<boolean> {
  if (!token.startsWith(CHAT_TOKEN_PREFIX)) return false;
  const [payloadB64, sigB64] = token.slice(CHAT_TOKEN_PREFIX.length).split(".");
  if (!payloadB64 || !sigB64) return false;
  try {
    const key = await hmacKey(secret);
    const ok = await crypto.subtle.verify(
      "HMAC",
      key,
      b64urlDecode(sigB64) as BufferSource,
      new TextEncoder().encode(payloadB64)
    );
    if (!ok) return false;
    const payload = JSON.parse(
      new TextDecoder().decode(b64urlDecode(payloadB64))
    ) as { exp?: number };
    return typeof payload.exp === "number" && payload.exp > Date.now();
  } catch {
    return false;
  }
}

// ─── API key (sk_live_*) lookup — via @etzhayyim/sdk ────────────────

interface ApiKeyRecord {
  ownerDid: string;
  scopes?: string[];
  status: "active" | "revoked";
  createdTsMs: number;
}

const apiKeyCache = new Map<
  string,
  { ownerDid: string; scopes: string[]; at: number } | null
>();

async function sha256Hex(s: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function verifyPlatformApiKey(
  env: Env,
  rawKey: string
): Promise<{ ownerDid: string; scopes: string[] } | null> {
  const keyHash = await sha256Hex(rawKey);
  const cached = apiKeyCache.get(keyHash);
  if (
    cached !== undefined &&
    cached &&
    Date.now() - cached.at < API_KEY_CACHE_TTL_MS
  ) {
    return { ownerDid: cached.ownerDid, scopes: cached.scopes };
  }
  try {
    const { records } = await sdk(env).read<ApiKeyRecord>({
      collection: COLLECTION_API_KEY,
      rkey: keyHash,
      fetchBlobs: false,
    });
    const rec = records[0];
    if (!rec || rec.value.status !== "active") {
      apiKeyCache.set(keyHash, null);
      return null;
    }
    const ownerDid = rec.value.ownerDid;
    const scopes = (rec.value.scopes ?? ["read"]).map((s) => s.trim()).filter(Boolean);
    if (!ownerDid.startsWith("did:")) {
      apiKeyCache.set(keyHash, null);
      return null;
    }
    apiKeyCache.set(keyHash, { ownerDid, scopes, at: Date.now() });
    return { ownerDid, scopes };
  } catch {
    return null;
  }
}

// ─── Auth ────────────────────────────────────────────────────────────

interface AuthContext {
  kind: "internal" | "platform" | "break-glass" | "chat-anon";
  ownerDid?: string;
  scopes?: string[];
}

async function authenticate(
  env: Env,
  request: Request
): Promise<AuthContext | null> {
  const authHeader = request.headers.get("Authorization");
  if (authHeader) {
    const token = authHeader.replace(/^Bearer\s+/i, "");
    const jwtClaims = await verifyServiceAuthJwt(token);
    if (jwtClaims) return { kind: "internal" };
  }
  const xApiKey = request.headers.get("x-api-key");
  const providedKey =
    authHeader?.replace(/^Bearer\s+/i, "") || xApiKey || "";
  if (!providedKey) return null;
  if (providedKey.startsWith(CHAT_TOKEN_PREFIX) && env.MURAKUMO_CHAT_SECRET) {
    if (await verifyChatToken(env.MURAKUMO_CHAT_SECRET, providedKey))
      return { kind: "chat-anon" };
    return null;
  }
  if (
    providedKey.startsWith("sk_live_") ||
    providedKey.startsWith("sk_test_")
  ) {
    const result = await verifyPlatformApiKey(env, providedKey);
    if (!result) return null;
    const ok = result.scopes.some(
      (s) => s === "*" || s === "murakumo:inference" || s === "murakumo"
    );
    if (!ok) return null;
    return {
      kind: "platform",
      ownerDid: result.ownerDid,
      scopes: result.scopes,
    };
  }
  if (env.MURAKUMO_API_KEY && providedKey === env.MURAKUMO_API_KEY)
    return { kind: "break-glass" };
  if (env.DEV_INSECURE_API_KEY && providedKey === env.DEV_INSECURE_API_KEY)
    return { kind: "break-glass" };
  return null;
}

const requireAuth: MiddlewareHandler<{
  Bindings: Env;
  Variables: { auth: AuthContext };
}> = async (c, next) => {
  const auth = await authenticate(c.env, c.req.raw);
  if (!auth)
    return c.json(
      { error: "unauthorized", message: "invalid or missing api key" },
      401
    );
  c.set("auth", auth);
  if (auth.ownerDid) c.header("x-owner-did", auth.ownerDid);
  await next();
};

// ─── Fleet roster (R2 + in-memory cache) ────────────────────────────

interface PerNodeHealth {
  name: string;
  ip?: string;
  model?: string;
  healthy: boolean;
  latencyMs?: number;
  error?: string;
}

interface FleetRoster {
  v: number;
  ts: string;
  epoch: number;
  healthPct: number;
  nodesHealthy: number;
  nodesTotal: number;
  nodes: PerNodeHealth[];
  litellm: { reachable: boolean; latencyMs?: number; error?: string };
}

let cachedRoster: { data: FleetRoster; fetchedAt: number } | null = null;

async function getRoster(env: Env): Promise<FleetRoster | null> {
  const now = Date.now();
  if (cachedRoster && now - cachedRoster.fetchedAt < ROSTER_CACHE_TTL_MS) {
    return cachedRoster.data;
  }
  try {
    const obj = await env.R2.get("fleet-roster.json");
    if (!obj) return null;
    const data = await obj.json<FleetRoster>();
    cachedRoster = { data, fetchedAt: now };
    return data;
  } catch {
    return null;
  }
}

// ─── Fleet node mapping (Mac-mini fleet, ADR-2605191346) ────────────

const NODE_IP_MAP: Record<string, string> = {
  // RunPod (etzhayyim legacy — kept while transition; etzhayyim moves to Mac-mini fleet only)
  vyp99t9px7h4dl: "runpod-ada-primary",
  // Mac-mini fleet (Tier-1 per ADR-2605191346)
  "192.168.1.61": "judah",
  "192.168.1.51": "benjamin",
  "192.168.1.49": "joseph",
  "192.168.1.60": "issachar",
  "192.168.1.59": "simeon",
  "192.168.1.52": "dan",
  "192.168.1.64": "naphtali",
  "192.168.1.65": "levi",
  "192.168.1.67": "zebulun",
  "192.168.1.54": "asher",
};
const FLEET_NODES = Object.values(NODE_IP_MAP);
const FLEET_MODEL_MAP: Record<string, string> = {
  "gemma-4-e2b-it": "gemma4-e4b",
  "gemma4:e2b": "gemma4-e4b",
  "gemma4-e2b": "gemma4-e4b",
  "gemma4-e4b": "gemma4-e4b",
  "gemma-4-e4b-it": "gemma4-e4b",
  "qwen3-30b": "qwen3.5-9b",
  "qwen3.5-9b": "qwen3.5-9b",
  "qwen3.5-9b-instruct": "qwen3.5-9b",
  "gpt-4o-mini": "gpt-4o-mini",
  default: "deepseek/deepseek-chat",
  "tier0-general": "deepseek/deepseek-chat",
  "tier0-structured": "deepseek/deepseek-chat",
};

function extractNodeName(apiBase: string): string {
  if (apiBase.includes("openrouter.ai")) return "openrouter";
  const rp = apiBase.match(/api\.runpod\.ai\/v2\/([a-z0-9]+)/);
  if (rp) return NODE_IP_MAP[rp[1]] ?? `runpod-${rp[1]}`;
  const ip = apiBase.match(/\/\/(\d+\.\d+\.\d+\.\d+)/);
  return ip ? NODE_IP_MAP[ip[1]] ?? ip[1] : "unknown";
}

function remapModelForFleet(model: string): string {
  if (!model) return "deepseek/deepseek-chat";
  return FLEET_MODEL_MAP[model] ?? model;
}

function buildOpenAiModelList(): {
  object: "list";
  data: Array<Record<string, unknown>>;
} {
  const canonicalModels = Object.entries(MODEL_REGISTRY)
    .filter(([, def]) => def.available)
    .map(([id, def]) => ({
      id,
      object: "model",
      created: OPENAI_MODEL_LIST_CREATED_AT,
      owned_by: "murakumo",
      ownedBy: "murakumo",
      permission: [],
      root: def.cfModel,
      parent: null,
      backend: def.ollamaModel ? "litellm" : "murakumo",
      max_tokens: def.maxTokens,
      context_window: def.contextWindow,
    }));

  const aliasModels = Object.entries(MODEL_ALIASES)
    .filter(([, canonicalId]) => MODEL_REGISTRY[canonicalId]?.available)
    .map(([aliasId, canonicalId]) => {
      const def = MODEL_REGISTRY[canonicalId]!;
      return {
        id: aliasId,
        object: "model",
        created: OPENAI_MODEL_LIST_CREATED_AT,
        owned_by: "murakumo",
        ownedBy: "murakumo",
        permission: [],
        root: canonicalId,
        parent: canonicalId,
        backend: def.ollamaModel ? "litellm" : "murakumo",
        max_tokens: def.maxTokens,
        context_window: def.contextWindow,
      };
    });

  return { object: "list", data: [...canonicalModels, ...aliasModels] };
}

function litellmAuthKey(env: Env): string {
  return env.LITELLM_MASTER ?? env.LITELLM_MASTER_KEY ?? "";
}

// ─── Hono app ────────────────────────────────────────────────────────

const app = new Hono<{ Bindings: Env; Variables: { auth: AuthContext } }>();

// ─── LiteLLM proxy with SSE keepalive ───────────────────────────────

async function proxyToLitellm(
  env: Env,
  path: string,
  request: Request,
  bodyBuffer?: ArrayBuffer | null
): Promise<Response> {
  const proxyStart = Date.now();
  const forwardHeaders = new Headers({ "Content-Type": "application/json" });
  const authKey = litellmAuthKey(env);
  if (authKey) forwardHeaders.set("Authorization", `Bearer ${authKey}`);

  let body: ArrayBuffer | null =
    bodyBuffer !== undefined ? bodyBuffer : null;
  if (body === null && request.body) body = await request.arrayBuffer();

  let targetUrl = env.LITELLM_URL ? `${env.LITELLM_URL}${path}` : "";

  let isStream = false;
  if (body) {
    try {
      const decoded = JSON.parse(new TextDecoder().decode(body)) as Record<
        string,
        unknown
      >;
      if (path === "/v1/chat/completions" && typeof decoded.model === "string") {
        const remapped = remapModelForFleet(decoded.model);
        decoded.model = remapped;
        if (
          remapped.startsWith("deepseek/") ||
          remapped.startsWith("openrouter/")
        ) {
          targetUrl = `https://openrouter.ai/api${path}`;
          if (env.OPENROUTER_API_KEY) {
            forwardHeaders.set("Authorization", `Bearer ${env.OPENROUTER_API_KEY}`);
          }
        }
        body = new TextEncoder().encode(JSON.stringify(decoded)).buffer as ArrayBuffer;
      }
      isStream = decoded?.stream === true;
    } catch {
      // Pass non-JSON bodies unchanged.
    }
  }

  if (!targetUrl) {
    return new Response(
      JSON.stringify({
        error: "litellm_not_configured",
        detail: "LITELLM_URL is not set and no alternate route found",
      }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const resp = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body,
      signal: AbortSignal.timeout(INFERENCE_TIMEOUT_MS),
    });

    const latencyMs = Date.now() - proxyStart;

    if (isStream && resp.ok && resp.body) {
      const upstream = resp.body;
      const wrapped = new ReadableStream<Uint8Array>({
        async start(controller) {
          const encoder = new TextEncoder();
          const reader = upstream.getReader();
          let closed = false;
          let lastByteAt = Date.now();
          const heartbeat = setInterval(() => {
            if (closed) return;
            if (Date.now() - lastByteAt >= STREAM_KEEPALIVE_MS) {
              try {
                controller.enqueue(
                  encoder.encode(`: keepalive ${Date.now()}\n\n`)
                );
                lastByteAt = Date.now();
              } catch {
                /* already closed */
              }
            }
          }, STREAM_KEEPALIVE_MS);
          try {
            while (true) {
              const { value, done } = await reader.read();
              if (done) break;
              controller.enqueue(value);
              lastByteAt = Date.now();
            }
          } catch (err) {
            try {
              controller.enqueue(
                encoder.encode(
                  `data: {"error":"stream_interrupt","detail":${JSON.stringify(String(err))}}\n\n`
                )
              );
            } catch {
              /* closed */
            }
          } finally {
            closed = true;
            clearInterval(heartbeat);
            try {
              controller.close();
            } catch {
              /* closed */
            }
          }
        },
        cancel() {
          try {
            upstream.cancel();
          } catch {
            /* upstream already gone */
          }
        },
      });

      return new Response(wrapped, {
        status: resp.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          "X-Accel-Buffering": "no",
          "x-murakumo-backend": "litellm-stream",
          "x-murakumo-latency-ms": String(latencyMs),
        },
      });
    }

    return new Response(resp.body, {
      status: resp.status,
      headers: {
        "Content-Type": resp.headers.get("Content-Type") || "application/json",
        "x-murakumo-backend": "litellm",
        "x-murakumo-latency-ms": String(latencyMs),
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "litellm_unavailable", detail: String(err) }),
      {
        status: 503,
        headers: {
          "Content-Type": "application/json",
          "x-murakumo-latency-ms": String(Date.now() - proxyStart),
        },
      }
    );
  }
}

// ─── Async jobs — event-sourced via @etzhayyim/sdk ──────────────────
//
// State machine (3 records per job):
//   seq=0  status=pending   (inferenceJob header + initial event)
//   seq=1  status=running   (LiteLLM call started)
//   seq=2  status=done|failed  (with content/tokens/error)
//
// Read pattern: getRecord(inferenceJob, jobId) + listRecords(inferenceJobEvent, prefix=`${jobId}~`)
// then reduce events in seq order to derive latest state. No UPDATE.

function padSeq(n: number): string {
  return String(n).padStart(2, "0");
}

interface JobEventRecord {
  jobId: string;
  seq: number;
  status: "pending" | "running" | "done" | "failed";
  tsMs: number;
  startedTsMs?: number;
  completedTsMs?: number;
  latencyMs?: number;
  responseContent?: string;
  responseReasoning?: string;
  finishReason?: string;
  promptTokens?: number;
  completionTokens?: number;
  error?: string;
}

interface JobHeaderRecord {
  jobId: string;
  owner: string;
  modelId: string;
  promptPreview: string;
  requestBody: string;
  createdTsMs: number;
}

async function emitJobEvent(
  env: Env,
  ev: JobEventRecord
): Promise<void> {
  await sdk(env).write({
    collection: COLLECTION_JOB_EVENT,
    rkey: `${ev.jobId}~${padSeq(ev.seq)}`,
    record: ev as unknown as Record<string, unknown>,
  });
}

async function runJob(env: Env, jobId: string, requestBody: string): Promise<void> {
  console.log(`[runJob] start ${jobId}`);
  if (!env.LITELLM_URL) {
    console.warn("[runJob] LITELLM_URL not set");
    return;
  }
  const startedAt = Date.now();
  try {
    await emitJobEvent(env, {
      jobId,
      seq: 1,
      status: "running",
      tsMs: startedAt,
      startedTsMs: startedAt,
    });
  } catch (err) {
    console.error(`[runJob] running-event write failed:`, err);
    return;
  }

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(requestBody) as Record<string, unknown>;
  } catch {
    parsed = {};
  }
  if (typeof parsed.model === "string") {
    parsed.model = remapModelForFleet(parsed.model);
  }
  const streamedBody = JSON.stringify({ ...parsed, stream: true });

  let targetUrl = env.LITELLM_URL ? `${env.LITELLM_URL}/v1/chat/completions` : "";
  let authHeader = `Bearer ${env.LITELLM_MASTER ?? ""}`;
  if (
    typeof parsed.model === "string" &&
    (parsed.model.startsWith("deepseek/") || parsed.model.startsWith("openrouter/"))
  ) {
    targetUrl = "https://openrouter.ai/api/v1/chat/completions";
    if (env.OPENROUTER_API_KEY) {
      authHeader = `Bearer ${env.OPENROUTER_API_KEY}`;
    }
  }
  if (!targetUrl) {
    console.error(`[runJob] missing route for model ${parsed.model}`);
    return;
  }

  let content = "";
  let reasoning = "";
  let finishReason = "";
  let errorMsg = "";
  let pTokens = 0;
  let cTokens = 0;
  try {
    const resp = await fetch(targetUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authHeader },
      body: streamedBody,
      signal: AbortSignal.timeout(INFERENCE_TIMEOUT_MS),
    });
    if (!resp.ok || !resp.body) {
      errorMsg = `http ${resp.status}`;
    } else {
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let nl: number;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (!line || line.startsWith(":") || !line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") continue;
          try {
            const j = JSON.parse(payload);
            const d = j?.choices?.[0]?.delta ?? {};
            if (typeof d.content === "string") content += d.content;
            if (typeof d.reasoning_content === "string")
              reasoning += d.reasoning_content;
            const fr = j?.choices?.[0]?.finish_reason;
            if (fr) finishReason = String(fr);
            if (j?.usage) {
              pTokens = Number(j.usage.prompt_tokens ?? pTokens);
              cTokens = Number(j.usage.completion_tokens ?? cTokens);
            }
          } catch {
            /* skip malformed */
          }
        }
      }
    }
  } catch (err) {
    errorMsg = String(err);
  }

  const completedAt = Date.now();
  const finalStatus: "done" | "failed" = errorMsg ? "failed" : "done";
  try {
    await emitJobEvent(env, {
      jobId,
      seq: 2,
      status: finalStatus,
      tsMs: completedAt,
      completedTsMs: completedAt,
      latencyMs: completedAt - startedAt,
      responseContent: content,
      responseReasoning: reasoning,
      finishReason,
      promptTokens: pTokens,
      completionTokens: cTokens,
      error: errorMsg,
    });
    console.log(
      `[runJob] ${jobId} -> ${finalStatus} (${completedAt - startedAt}ms, ${cTokens} tok)`
    );
  } catch (err) {
    console.error(`[runJob] final-event write failed:`, err);
  }
}

// ─── Public endpoints ───────────────────────────────────────────────

app.get("/health", async (c) => {
  const roster = await getRoster(c.env);
  if (!roster) return c.json({ status: "unknown", gateway: "ok", fleet: null });
  return c.json({
    status: roster.healthPct >= 50 ? "ok" : "degraded",
    gateway: "ok",
    fleet: {
      healthPct: roster.healthPct,
      nodesHealthy: roster.nodesHealthy,
      nodesTotal: roster.nodesTotal,
      litellm: roster.litellm,
      lastCheck: roster.ts,
    },
  });
});

app.get("/_app/meta", async (c) => {
  const roster = await getRoster(c.env);
  return c.json({
    name: "murakumo",
    nanoid: "m9r4k8m0",
    version: "5.0.0",
    backend: "litellm",
    substrate: "etzhayyim-sdk",
    capabilities: ["llm-inference"],
    p999_target_ms: 3000,
    fleet: roster
      ? {
          healthPct: roster.healthPct,
          nodesHealthy: roster.nodesHealthy,
          nodesTotal: roster.nodesTotal,
          nodes: roster.nodes,
          litellm: roster.litellm,
          staleMs: Date.now() - roster.epoch,
          lastCheck: roster.ts,
        }
      : null,
  });
});

app.get("/.well-known/agent.json", (c) => {
  return c.json(
    {
      "@context": ["https://schema.org", "https://w3id.org/erc8004/v1"],
      "@type": "Agent",
      id: DEFAULT_MURAKUMO_DID,
      name: "Murakumo Inference Fleet",
      description:
        "etzhayyim Murakumo Mac-mini fleet (ADR-2605191346) + LiteLLM gateway. kotoba per ADR-2605191358.",
      url: "https://murakumo.etzhayyim.com",
      mcpEndpoint: "https://murakumo.etzhayyim.com/v1",
      capabilities: ["llm-inference", "text-generation", "mcp-tools-call"],
    },
    200,
    { "cache-control": "public, max-age=300" }
  );
});

app.get("/", async (c) => {
  const token = c.env.MURAKUMO_CHAT_SECRET
    ? await signChatToken(c.env.MURAKUMO_CHAT_SECRET)
    : "";
  const html = CHAT_HTML.replace(/__MURAKUMO_CHAT_TOKEN__/g, token);
  return c.html(html);
});

// ─── Jobs API ───────────────────────────────────────────────────────

app.post("/v1/jobs", requireAuth, async (c) => {
  const bodyText = await c.req.text();
  let parsed: Record<string, unknown> = {};
  try {
    parsed = JSON.parse(bodyText) as Record<string, unknown>;
  } catch {
    return c.json({ error: "invalid_json" }, 400);
  }
  const jobId = crypto.randomUUID();
  const now = Date.now();
  const auth = c.get("auth");
  const ownerTag = auth?.ownerDid ?? auth?.kind ?? "unknown";
  const messages = Array.isArray(parsed.messages) ? parsed.messages : [];
  const userMsg = messages.find(
    (m): m is { role: string; content?: unknown } =>
      typeof m === "object" && m !== null && (m as { role?: unknown }).role === "user"
  );
  const preview = String((userMsg as { content?: unknown })?.content ?? "").slice(0, 200);

  try {
    await sdk(c.env).write({
      collection: COLLECTION_JOB,
      rkey: jobId,
      record: {
        jobId,
        owner: ownerTag,
        modelId: String(parsed.model ?? ""),
        promptPreview: preview,
        requestBody: bodyText,
        createdTsMs: now,
      },
    });
    await emitJobEvent(c.env, {
      jobId,
      seq: 0,
      status: "pending",
      tsMs: now,
    });
  } catch (err) {
    console.error("[POST /v1/jobs] write failed:", err);
    return c.json({ error: "sdk_write_failed", detail: String(err) }, 503);
  }

  c.executionCtx.waitUntil(
    runJob(c.env, jobId, bodyText).catch((err) => console.error("[job]", err))
  );
  return c.json({ job_id: jobId, status: "pending", poll_url: `/v1/jobs/${jobId}` }, 202);
});

type MergedJob = Partial<JobHeaderRecord> & Partial<JobEventRecord>;

function reduceJob(
  header: JobHeaderRecord,
  events: Array<{ value: JobEventRecord }>
): MergedJob {
  const sorted = [...events].sort((a, b) => a.value.seq - b.value.seq);
  let merged: MergedJob = { ...header };
  for (const ev of sorted) {
    merged = { ...merged, ...ev.value };
  }
  return merged;
}

app.get("/v1/jobs/:id", requireAuth, async (c) => {
  const id = c.req.param("id");
  const e = sdk(c.env);
  const headerRes = await e.read<JobHeaderRecord>({
    collection: COLLECTION_JOB,
    rkey: id,
    fetchBlobs: false,
  });
  const header = headerRes.records[0];
  if (!header) return c.json({ error: "not_found" }, 404);
  const eventsRes = await e.read<JobEventRecord>({
    collection: COLLECTION_JOB_EVENT,
    prefix: `${id}~`,
    limit: 100,
    fetchBlobs: false,
  });
  return c.json(reduceJob(header.value, eventsRes.records));
});

app.get("/v1/jobs", requireAuth, async (c) => {
  const limit = Math.min(Math.max(Number(c.req.query("limit") ?? "20"), 1), 100);
  const e = sdk(c.env);
  const headerRes = await e.read<JobHeaderRecord>({
    collection: COLLECTION_JOB,
    limit,
    fetchBlobs: false,
  });
  // N+1 read for the latest event of each job. Acceptable at MVP scale (limit ≤ 100);
  // production should use a mst-projector snapshot per ADR-2605191358 §Consequences.
  const jobs = await Promise.all(
    headerRes.records.map(async (rec) => {
      const ev = await e.read<JobEventRecord>({
        collection: COLLECTION_JOB_EVENT,
        prefix: `${rec.value.jobId}~`,
        limit: 10,
        fetchBlobs: false,
      });
      return reduceJob(rec.value, ev.records);
    })
  );
  return c.json({ jobs });
});

// ─── OpenAI-compatible API (LiteLLM passthrough) ────────────────────

app.get("/api/openai/v1/models", requireAuth, (c) =>
  c.json(buildOpenAiModelList())
);
app.post("/api/openai/v1/chat/completions", requireAuth, async (c) =>
  proxyToLitellm(c.env, "/v1/chat/completions", c.req.raw)
);
app.get("/v1/models", requireAuth, (c) => c.json(buildOpenAiModelList()));
app.post("/v1/chat/completions", requireAuth, async (c) =>
  proxyToLitellm(c.env, "/v1/chat/completions", c.req.raw)
);

app.get("/internal/capacity", async (c) => {
  const roster = await getRoster(c.env);
  return c.json({
    idleNative: roster?.nodesHealthy ?? 0,
    idleBrowser: 0,
    totalPollWorkers: roster?.nodesTotal ?? 0,
    backend: "litellm",
  });
});

// Zeebe-driven cron tick (timer-start BPMN R/PT5M).
app.post("/xrpc/com.etzhayyim.apps.murakumo.cronTick", async (c) => {
  c.executionCtx.waitUntil(
    runFleetHealthCheck(c.env).catch((err) =>
      console.error("[murakumo-cron] Zeebe cron tick failed:", err)
    )
  );
  return c.json({ ok: true, dispatched: true });
});

app.all("*", (c) => c.json({ error: "not_found", path: c.req.path }, 404));

// ─── Fleet health scheduler (LiteLLM readiness → R2 roster) ─────────

interface LitellmReadiness {
  status?: string;
  litellm_version?: string;
  [k: string]: unknown;
}
interface LitellmModelDeployment {
  model_name?: string;
  litellm_params?: { api_base?: string; model?: string; [k: string]: unknown };
  [k: string]: unknown;
}

async function probeLitellm(env: Env): Promise<{
  reachable: boolean;
  latencyMs?: number;
  error?: string;
  version?: string;
  deployments?: LitellmModelDeployment[];
}> {
  if (!env.LITELLM_URL) return { reachable: false, error: "LITELLM_URL not set" };
  const start = Date.now();
  const authKey = litellmAuthKey(env);
  const auth: Record<string, string> = authKey
    ? { Authorization: `Bearer ${authKey}` }
    : {};
  try {
    const [readyResp, modelsResp] = await Promise.all([
      fetch(`${env.LITELLM_URL}/health/readiness`, {
        headers: auth,
        signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
      }),
      fetch(`${env.LITELLM_URL}/v1/model/info`, {
        headers: auth,
        signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
      }),
    ]);
    const latencyMs = Date.now() - start;
    if (!readyResp.ok)
      return { reachable: false, latencyMs, error: `readiness http ${readyResp.status}` };
    const ready = (await readyResp.json()) as LitellmReadiness;
    if (ready.status !== "healthy")
      return { reachable: false, latencyMs, error: `readiness status=${ready.status}` };
    const deployments = modelsResp.ok
      ? ((await modelsResp.json()) as { data?: LitellmModelDeployment[] }).data ?? []
      : [];
    return { reachable: true, latencyMs, version: ready.litellm_version, deployments };
  } catch (err) {
    return { reachable: false, latencyMs: Date.now() - start, error: String(err) };
  }
}

async function runFleetHealthCheck(env: Env): Promise<void> {
  const probe = await probeLitellm(env);

  const perNode = new Map<string, PerNodeHealth>();
  for (const [ip, name] of Object.entries(NODE_IP_MAP)) {
    perNode.set(name, { name, ip, healthy: false });
  }

  if (probe.reachable && probe.deployments) {
    const seenByNode = new Map<string, string[]>();
    for (const d of probe.deployments) {
      const apiBase = String(d.litellm_params?.api_base ?? "");
      const name = extractNodeName(apiBase);
      const model = String(d.model_name ?? d.litellm_params?.model ?? "");
      const models = seenByNode.get(name) ?? [];
      if (model && !models.includes(model)) models.push(model);
      seenByNode.set(name, models);
      const cur = perNode.get(name) ?? { name, healthy: false };
      perNode.set(name, {
        ...cur,
        healthy: true,
        model: models.join(",") || cur.model,
      });
    }
  }

  const nodes = FLEET_NODES.map((n) => perNode.get(n)!).concat(
    [...perNode.values()].filter((v) => !FLEET_NODES.includes(v.name))
  );
  const nodesHealthy = nodes.filter((n) => n.healthy).length;
  const nodesTotal = nodes.length;

  const roster: FleetRoster = {
    v: 2,
    ts: new Date().toISOString(),
    epoch: Date.now(),
    healthPct: nodesTotal > 0 ? Math.round((nodesHealthy / nodesTotal) * 100) : 0,
    nodesHealthy,
    nodesTotal,
    nodes,
    litellm: {
      reachable: probe.reachable,
      latencyMs: probe.latencyMs,
      error: probe.error,
    },
  };

  cachedRoster = null;
  const monitorKey = `monitor/${new Date().toISOString().slice(0, 16)}.json`;
  await Promise.all([
    env.R2.put("fleet-roster.json", JSON.stringify(roster), {
      httpMetadata: { contentType: "application/json" },
    }),
    env.R2.put(
      monitorKey,
      JSON.stringify({ sampledAt: roster.ts, roster, version: probe.version }),
      { httpMetadata: { contentType: "application/json" } }
    ),
  ]);

  console.log(
    `[murakumo-cron] litellm=${
      probe.reachable
        ? `ok v${probe.version} (${probe.latencyMs}ms)`
        : `down: ${probe.error}`
    } nodes=${nodesHealthy}/${nodesTotal}`
  );
}

export default {
  fetch: app.fetch,
  async scheduled(
    _event: ScheduledEvent,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    ctx.waitUntil(
      runFleetHealthCheck(env).catch((err) =>
        console.error("[murakumo-cron] scheduled fallback failed:", err)
      )
    );
  },
};
