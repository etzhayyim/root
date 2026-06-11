// mamoru.etzhayyim.com — L3 dispatcher CF Worker.
//
// Surfaces:
//   /health, /_app/meta                              edge probes (no auth)
//   /webhook/github                                  GitHub App push webhook (HMAC-256)
//   /xrpc/com.etzhayyim.apps.mamoru.scanCommit             procedure (Bearer auth)
//   /xrpc/com.etzhayyim.apps.mamoru.scanRepo               procedure (Bearer auth)
//   /xrpc/com.etzhayyim.apps.mamoru.listIncidents          query     (Bearer auth)
//   /xrpc/com.etzhayyim.apps.mamoru.getIncident            query     (Bearer auth)
//   /xrpc/com.etzhayyim.apps.mamoru.resolveIncident        procedure (Bearer auth)
//
// Auth: Bearer sk_live_* / ES256 JWT → PDS service binding /_internal/resolve-auth
// Dispatch: forwards to bpmn-dispatcher with x-internal-trust HMAC.
//
// No LLM call, no Hyperdrive write — all compute in mitama-mamoru-pool (ADR-2605080600).

import { Hono } from "hono";

type Env = {
  MAMORU_VERSION?: string;
  MAMORU_ACTOR_DID?: string;
  BPMN_DISPATCHER_URL: string;
  GITHUB_WEBHOOK_SECRET?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
  PDS_SERVICE?: { fetch(req: Request): Promise<Response> };
  ASSETS?: { fetch(req: Request): Promise<Response> };
};

// ── GitHub Secret Scanning Partner Program public key cache ──────────

interface GHPublicKey {
  key_identifier: string;
  key: string;
  is_current: boolean;
}

let _ghSsKeyCache: { keys: GHPublicKey[]; fetchedAt: number } | null = null;
const GH_SS_KEY_CACHE_TTL_MS = 5 * 60 * 1000; // 5 min — keys rotate rarely

async function fetchGHSecretScanningKeys(): Promise<GHPublicKey[]> {
  const now = Date.now();
  if (_ghSsKeyCache && now - _ghSsKeyCache.fetchedAt < GH_SS_KEY_CACHE_TTL_MS) {
    return _ghSsKeyCache.keys;
  }
  const res = await fetch("https://api.github.com/meta/public_keys/secret_scanning", {
    headers: { "User-Agent": "mamoru-secret-guardian/1.0" },
  });
  if (!res.ok) throw new Error(`GitHub public key fetch failed: ${res.status}`);
  const data = await res.json<{ public_keys: GHPublicKey[] }>();
  _ghSsKeyCache = { keys: data.public_keys, fetchedAt: now };
  return data.public_keys;
}

async function importSpkiPem(pem: string): Promise<CryptoKey> {
  const b64 = pem.replace(/-----[^-]+-----/g, "").replace(/\s/g, "");
  const der = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  return crypto.subtle.importKey("spki", der, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
}

async function verifyGHSecretScanningSignature(
  rawBody: string,
  keyId: string,
  sigB64: string,
): Promise<boolean> {
  try {
    const keys = await fetchGHSecretScanningKeys();
    const entry = keys.find((k) => k.key_identifier === keyId);
    if (!entry) return false;
    const cryptoKey = await importSpkiPem(entry.key);
    const sigBytes = Uint8Array.from(atob(sigB64), (c) => c.charCodeAt(0));
    return crypto.subtle.verify(
      { name: "ECDSA", hash: "SHA-256" },
      cryptoKey,
      sigBytes,
      new TextEncoder().encode(rawBody),
    );
  } catch {
    return false;
  }
}

interface AuthContext {
  did: string;
  orgDid: string;
  activeDid?: string;
}

declare module "hono" {
  interface ContextVariableMap {
    auth?: AuthContext;
  }
}

const ACTOR_DID_DEFAULT = "did:web:mamoru.etzhayyim.com";
const NSID_PREFIX = "com.etzhayyim.apps.mamoru";
const PROCEDURES = new Set(["scanCommit", "scanRepo", "resolveIncident", "processSecretAlert"]);
const QUERIES = new Set(["listIncidents", "getIncident"]);

const app = new Hono<{ Bindings: Env }>();

// ── probes ───────────────────────────────────────────────────────────

app.get("/health", (c) =>
  c.json({ ok: true, app: "mamoru", ts: new Date().toISOString() }),
);

app.get("/_worker/health", (c) =>
  c.json({ ok: true, app: "mamoru", ts: new Date().toISOString() }),
);

app.get("/_app/meta", (c) =>
  c.json({
    app: "etzhayyim-project-mamoru",
    did: c.env.MAMORU_ACTOR_DID ?? ACTOR_DID_DEFAULT,
    version: c.env.MAMORU_VERSION ?? "0.1.0",
    layer: "L3-dispatcher",
    surfaces: [
      "/webhook/github",
      "/xrpc/com.etzhayyim.apps.mamoru.scanCommit",
      "/xrpc/com.etzhayyim.apps.mamoru.scanRepo",
      "/xrpc/com.etzhayyim.apps.mamoru.listIncidents",
      "/xrpc/com.etzhayyim.apps.mamoru.getIncident",
      "/xrpc/com.etzhayyim.apps.mamoru.resolveIncident",
    ],
    backend: c.env.BPMN_DISPATCHER_URL,
    federable: false,
  }),
);

// ── GitHub App webhook ───────────────────────────────────────────────

app.post("/webhook/github", async (c) => {
  const event = c.req.header("x-github-event") ?? "";
  const secret = c.env.GITHUB_WEBHOOK_SECRET;

  let payload: Record<string, unknown>;
  if (secret) {
    const bodyBuf = await c.req.arrayBuffer();
    const sig = c.req.header("x-hub-signature-256") ?? "";
    if (!await verifyGitHubHmac(bodyBuf, sig, secret)) {
      return c.json({ error: "InvalidSignature" }, 401);
    }
    payload = JSON.parse(new TextDecoder().decode(bodyBuf)) as Record<string, unknown>;
  } else {
    payload = await c.req.json<Record<string, unknown>>();
  }

  if (event === "push") return handleGitHubPush(c, payload);
  if (event === "repository" && payload.action === "publicized") return handleGitHubPublicized(c, payload);
  return c.json({ ok: true, skipped: true });
});

// ── GitHub Secret Scanning Partner Program webhook ────────────────────
// GitHub pre-detects tokens matching our registered patterns in ALL public
// repos and POSTs here. We verify ECDSA-P256 signature, hash the raw token,
// then forward to the pod via processSecretAlert for validity probe + persist.

app.post("/webhook/github-secret-scanning", async (c) => {
  const keyId = c.req.header("github-public-key-identifier") ?? "";
  const sig   = c.req.header("github-public-key-signature") ?? "";
  if (!keyId || !sig) {
    return c.json({ error: "MissingSignatureHeaders" }, 400);
  }

  const rawBody = await c.req.text();
  const valid = await verifyGHSecretScanningSignature(rawBody, keyId, sig);
  if (!valid) {
    return c.json({ error: "InvalidSignature" }, 401);
  }

  type GHAlert = { token: string; type: string; url: string; source?: string };
  let ghAlerts: GHAlert[];
  try {
    ghAlerts = JSON.parse(rawBody) as GHAlert[];
    if (!Array.isArray(ghAlerts)) throw new Error("not array");
  } catch {
    return c.json({ error: "InvalidPayload" }, 400);
  }

  // Hash raw tokens before forwarding — raw values must not be logged.
  const alerts = await Promise.all(
    ghAlerts.map(async (a) => ({
      tokenType: a.type,
      sourceUrl: a.url,
      source: a.source ?? "git",
      tokenHash: await sha256hex(a.token),
      token: a.token, // forwarded over internal trust channel only
    })),
  );

  const xrpcBody = { alerts };
  const dispatcherUrl = c.env.BPMN_DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const target = `${dispatcherUrl}/xrpc/${NSID_PREFIX}.processSecretAlert`;
  const internalSecret = c.env.DISPATCHER_INTERNAL_SECRET ?? "";
  const hmacHeader = internalSecret ? await computeHmac(JSON.stringify(xrpcBody), internalSecret) : "dev";

  const resp = await fetch(target, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-trust": hmacHeader,
      "x-etzhayyim-actor-did": c.env.MAMORU_ACTOR_DID ?? ACTOR_DID_DEFAULT,
    },
    body: JSON.stringify(xrpcBody),
  });

  // GitHub requires HTTP 200 to acknowledge. On backend error, accept + log.
  if (!resp.ok) {
    console.error(`processSecretAlert dispatch failed: ${resp.status}`);
  }
  return c.json({ ok: true, processed: alerts.length });
});

// Triggered when a repo is made public — scan full commit history.
async function handleGitHubPublicized(
  c: Parameters<Parameters<typeof app.post>[1]>[0],
  payload: Record<string, unknown>,
): Promise<Response> {
  const repo = (payload.repository as Record<string, unknown>) ?? {};
  const repoId = String(repo.full_name ?? repo.id ?? "unknown");

  const xrpcBody = { repoId, provider: "github", trigger: "publicized" };
  const dispatcherUrl = c.env.BPMN_DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const target = `${dispatcherUrl}/xrpc/${NSID_PREFIX}.scanRepo`;
  const internalSecret = c.env.DISPATCHER_INTERNAL_SECRET ?? "";
  const hmacHeader = internalSecret ? await computeHmac(JSON.stringify(xrpcBody), internalSecret) : "dev";

  const resp = await fetch(target, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-trust": hmacHeader,
      "x-etzhayyim-actor-did": c.env.MAMORU_ACTOR_DID ?? ACTOR_DID_DEFAULT,
    },
    body: JSON.stringify(xrpcBody),
  });

  if (!resp.ok) return c.json({ error: "DispatchFailed", status: resp.status }, 502);
  const result = await resp.json<Record<string, unknown>>();
  return c.json({ ok: true, trigger: "repo-publicized", repoId, ...result });
}

async function handleGitHubPush(
  c: Parameters<Parameters<typeof app.post>[1]>[0],
  payload: Record<string, unknown>,
): Promise<Response> {
  const repo = (payload.repository as Record<string, unknown>) ?? {};
  const repoId = String(repo.full_name ?? repo.id ?? "unknown");
  const commitSha = String(payload.after ?? "");
  const commits = (payload.commits as unknown[]) ?? [];

  if (!commitSha || commitSha === "0000000000000000000000000000000000000000") {
    return c.json({ ok: true, skipped: true, reason: "branch-delete" });
  }

  // For each commit, call scanCommit. For push events we use the head commit diff.
  // In a real deployment the LangGraph pod fetches the diff via GitHub API.
  // Here we pass an empty diffPayload as a trigger; the pod fetches the real diff.
  const headCommit = (commits[commits.length - 1] ?? {}) as Record<string, unknown>;
  const authorEmail = String(
    (headCommit.author as Record<string, unknown> | undefined)?.email ?? ""
  );
  const authorEmailHash = authorEmail
    ? await sha256hex(authorEmail)
    : undefined;

  const xrpcBody = {
    repoId,
    commitSha,
    diffPayload: btoa(""), // empty trigger; pod fetches real diff via GitHub API
    provider: "github",
    ...(authorEmailHash ? { authorEmailHash } : {}),
  };

  const dispatcherUrl = c.env.BPMN_DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const target = `${dispatcherUrl}/xrpc/${NSID_PREFIX}.scanCommit`;
  const internalSecret = c.env.DISPATCHER_INTERNAL_SECRET ?? "";
  const hmacHeader = internalSecret
    ? await computeHmac(JSON.stringify(xrpcBody), internalSecret)
    : "dev";

  const resp = await fetch(target, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-trust": hmacHeader,
      "x-etzhayyim-actor-did": c.env.MAMORU_ACTOR_DID ?? ACTOR_DID_DEFAULT,
    },
    body: JSON.stringify(xrpcBody),
  });

  if (!resp.ok) {
    return c.json({ error: "DispatchFailed", status: resp.status }, 502);
  }
  const result = await resp.json<Record<string, unknown>>();
  return c.json({ ok: true, ...result });
}

// ── auth middleware ───────────────────────────────────────────────────

async function resolveAuth(req: Request, env: Env): Promise<AuthContext | null> {
  const h = req.headers.get("authorization") ?? "";
  if (!h.startsWith("Bearer ")) return null;
  const token = h.slice(7).trim();
  if (!token) return null;

  // Try PDS service binding first
  if (env.PDS_SERVICE) {
    try {
      const res = await env.PDS_SERVICE.fetch(
        new Request("https://atproto.etzhayyim.com/_internal/resolve-auth", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        }),
      );
      if (res.ok) {
        const data = await res.json<AuthContext>();
        return data;
      }
    } catch {
      // fall through to JWT decode
    }
  }

  // Minimal JWT decode (no signature verification — trust is from x-internal-trust on pod side)
  try {
    const parts = token.split(".");
    if (parts.length === 3) {
      const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
      if (payload.iss) {
        return { did: payload.iss, orgDid: payload.org ?? "anon" };
      }
    }
  } catch {
    // ignore
  }
  return null;
}

// ── XRPC routing ─────────────────────────────────────────────────────

async function dispatchXrpc(
  c: Parameters<Parameters<typeof app.post>[1]>[0],
  method: string,
  body: unknown,
  auth: AuthContext,
): Promise<Response> {
  const dispatcherUrl = c.env.BPMN_DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const target = `${dispatcherUrl}/xrpc/${NSID_PREFIX}.${method}`;
  const internalSecret = c.env.DISPATCHER_INTERNAL_SECRET ?? "";
  const bodyStr = JSON.stringify(body);
  const hmacHeader = internalSecret ? await computeHmac(bodyStr, internalSecret) : "dev";

  const isQuery = QUERIES.has(method);
  const resp = await fetch(isQuery ? `${target}?${new URLSearchParams(body as Record<string, string>)}` : target, {
    method: isQuery ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      "x-internal-trust": hmacHeader,
      "x-etzhayyim-actor-did": auth.did,
      "x-etzhayyim-org-did": auth.orgDid,
      "x-etzhayyim-trace-id": crypto.randomUUID(),
    },
    ...(isQuery ? {} : { body: bodyStr }),
  });

  const data = await resp.json<unknown>();
  return c.json(data as Record<string, unknown>, resp.status as 200);
}

// ── procedure endpoints ───────────────────────────────────────────────

app.post("/xrpc/:method", async (c) => {
  const fullNsid = c.req.param("method");
  const methodName = fullNsid.startsWith(NSID_PREFIX + ".")
    ? fullNsid.slice(NSID_PREFIX.length + 1)
    : null;

  if (!methodName || !PROCEDURES.has(methodName)) {
    return c.json({ error: "MethodNotFound" }, 404);
  }

  const auth = await resolveAuth(c.req.raw, c.env);
  if (!auth) return c.json({ error: "AuthRequired" }, 401);

  const body = await c.req.json<unknown>();
  return dispatchXrpc(c, methodName, body, auth);
});

// ── query endpoints ───────────────────────────────────────────────────

app.get("/xrpc/:method", async (c) => {
  const fullNsid = c.req.param("method");
  const methodName = fullNsid.startsWith(NSID_PREFIX + ".")
    ? fullNsid.slice(NSID_PREFIX.length + 1)
    : null;

  if (!methodName || !QUERIES.has(methodName)) {
    return c.json({ error: "MethodNotFound" }, 404);
  }

  const auth = await resolveAuth(c.req.raw, c.env);
  if (!auth) return c.json({ error: "AuthRequired" }, 401);

  const params = Object.fromEntries(c.req.query());
  return dispatchXrpc(c, methodName, params, auth);
});

// ── SPA fallback ─────────────────────────────────────────────────────
// Serve index.html for all non-API paths so SPA client-side routing works.

app.get("*", async (c) => {
  if (c.env.ASSETS) {
    return c.env.ASSETS.fetch(c.req.raw);
  }
  return c.text("Not Found", 404);
});

// ── crypto helpers ────────────────────────────────────────────────────

async function sha256hex(input: string): Promise<string> {
  const buf = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(input),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function computeHmac(data: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function verifyGitHubHmac(
  body: ArrayBuffer,
  sigHeader: string,
  secret: string,
): Promise<boolean> {
  if (!sigHeader.startsWith("sha256=")) return false;
  const expected = sigHeader.slice(7);
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, body);
  const actual = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  // Constant-time compare
  if (actual.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < actual.length; i++) {
    diff |= actual.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return diff === 0;
}

export default app;
