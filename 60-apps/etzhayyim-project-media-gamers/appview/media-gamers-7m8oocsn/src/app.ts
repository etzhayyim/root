// media-gamers.etzhayyim.com thin edge facade.
//
// LangGraph graphs (health, ingestCharts, generateGuide, autopilot) are
// proxied to lg-media-gamers via dispatcher.etzhayyim.com cloudflared tunnel.
// commitGuide is handled locally: writes AT record to PDS and returns rkey.

interface SecretBinding {
  get(): Promise<string>;
}

interface Fetcher {
  fetch(req: Request): Promise<Response>;
}

interface Env {
  ASSETS?: Fetcher;
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
  PDS_URL?: string;
  APP_NANOID?: string;
}

interface ExportedHandler<E> {
  fetch(req: Request, env: E): Promise<Response>;
}

const APP = "media-gamers";
const ACTOR_DID = "did:web:media-gamers.etzhayyim.com";
const REPO_DID = "did:web:a7m8oocs.etzhayyim.com";
const DEFAULT_NANOID = "a7m8oocs";
const NSID_PREFIX = "com.etzhayyim.apps.media_gamers.";
// MCP adapter routes via capability_worker='a7m8oocs' (nanoid, DNS-safe).
// Rewrite com.etzhayyim.apps.a7m8oocs.* → com.etzhayyim.apps.media_gamers.* before routing.
const NSID_PREFIX_ALIAS = "com.etzhayyim.apps.a7m8oocs.";

// NSIDs handled locally in the CF Worker (not forwarded to dispatcher).
const LOCAL_NSIDS = new Set([
  "com.etzhayyim.apps.media_gamers.guide.commitGuide",
  "com.etzhayyim.apps.media_gamers.knowledge.commitKnowledgeGuide",
]);

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (isMetaPath(url.pathname)) {
      return json({
        ok: true,
        actor: ACTOR_DID,
        nanoid: env.APP_NANOID ?? DEFAULT_NANOID,
        execution: "lg-media-gamers",
        graphs: ["health", "ingest_charts", "guide_generator", "autopilot"],
        langserverUrl: "http://lg-media-gamers.mitama-udf.svc.cluster.local:8000",
      });
    }

    if (url.pathname === "/embed") {
      return html(embedHtml());
    }

    let nsid = url.pathname.startsWith("/xrpc/") ? url.pathname.slice("/xrpc/".length) : "";
    if (nsid.startsWith(NSID_PREFIX_ALIAS)) {
      nsid = NSID_PREFIX + nsid.slice(NSID_PREFIX_ALIAS.length);
    }
    if (nsid.startsWith(NSID_PREFIX) && (req.method === "POST" || req.method === "GET")) {
      const body = await bodyWithQuery(req, url);
      if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);

      if (LOCAL_NSIDS.has(nsid)) {
        return handleLocal(env, nsid, body);
      }
      return proxyToDispatcher(env, nsid, body);
    }

    if (env.ASSETS) return env.ASSETS.fetch(req);
    return json({ error: "NotFound", message: `${APP} not found` }, 404);
  },
} satisfies ExportedHandler<Env>;

// ── local handlers ────────────────────────────────────────────────────

async function handleLocal(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> {
  if (nsid === "com.etzhayyim.apps.media_gamers.guide.commitGuide") {
    return handleCommitGuide(env, body);
  }
  if (nsid === "com.etzhayyim.apps.media_gamers.knowledge.commitKnowledgeGuide") {
    return handleCommitKnowledgeGuide(env, body);
  }
  return json({ error: "NotFound" }, 404);
}

async function handleCommitGuide(env: Env, body: Record<string, unknown>): Promise<Response> {
  const gameSlug = String(body.gameSlug ?? "");
  const guideType = String(body.guideType ?? "beginner-guide");
  const gameName = String(body.gameName ?? "");
  const title = String(body.title ?? "");
  const guideBody = String(body.body ?? "");
  const qualityScore = Number(body.qualityScore ?? 0);
  const translations = Array.isArray(body.translations) ? body.translations : [];

  if (!gameSlug || !guideBody) {
    return json({ error: "InvalidInput", message: "gameSlug and body are required" }, 400);
  }

  const rkey = `${gameSlug}-${guideType}-${Date.now()}`.slice(0, 128).replace(/[^a-z0-9-]/g, "-");
  const record = {
    $type: "com.etzhayyim.apps.media_gamers.guide",
    gameSlug,
    guideType,
    gameName,
    title,
    body: guideBody,
    qualityScore,
    translationCount: translations.length,
    lang: "en",
    generatedBy: String(body.generatedBy ?? "lg-media-gamers"),
    createdAt: new Date().toISOString(),
  };

  const pdsBase = (env.PDS_URL ?? "https://atproto.etzhayyim.com").replace(/\/+$/, "");
  try {
    const resp = await fetch(`${pdsBase}/xrpc/com.atproto.repo.createRecord`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-kotodama-verified": "true",
        "x-etzhayyim-org-id": "anon",
      },
      body: JSON.stringify({ repo: REPO_DID, collection: "com.etzhayyim.apps.media_gamers.guide", rkey, record }),
    });
    const text = await resp.text();
    let result: Record<string, unknown> = {};
    try { result = JSON.parse(text); } catch { result = { raw: text }; }
    return json({ ok: resp.ok, rkey, uri: `at://${REPO_DID}/com.etzhayyim.apps.media_gamers.guide/${rkey}`, pdsStatus: resp.status, ...result });
  } catch (err) {
    return json({ ok: false, rkey, error: String(err).slice(0, 200) }, 500);
  }
}

async function handleCommitKnowledgeGuide(env: Env, body: Record<string, unknown>): Promise<Response> {
  const title = String(body.title ?? "");
  const guideBody = String(body.body ?? "");
  const sourceQuery = String(body.sourceQuery ?? "");

  const rkey = `kg-${Date.now()}`.slice(0, 64);
  const record = {
    $type: "com.etzhayyim.apps.media_gamers.guide",
    guideType: "knowledge-guide",
    title,
    body: guideBody,
    sourceQuery,
    generatedBy: "lg-media-gamers",
    createdAt: new Date().toISOString(),
  };

  const pdsBase = (env.PDS_URL ?? "https://atproto.etzhayyim.com").replace(/\/+$/, "");
  try {
    const resp = await fetch(`${pdsBase}/xrpc/com.atproto.repo.createRecord`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-kotodama-verified": "true",
        "x-etzhayyim-org-id": "anon",
      },
      body: JSON.stringify({ repo: REPO_DID, collection: "com.etzhayyim.apps.media_gamers.guide", rkey, record }),
    });
    const text = await resp.text();
    let result: Record<string, unknown> = {};
    try { result = JSON.parse(text); } catch { result = { raw: text }; }
    return json({ ok: resp.ok, rkey, uri: `at://${REPO_DID}/com.etzhayyim.apps.media_gamers.guide/${rkey}`, pdsStatus: resp.status, ...result });
  } catch (err) {
    return json({ ok: false, rkey, error: String(err).slice(0, 200) }, 500);
  }
}

// ── dispatcher proxy ──────────────────────────────────────────────────

async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await internalTrustSecret(env);
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${base}/xrpc/${nsid}`, { method: "POST", headers, body: JSON.stringify(body) });
  const text = await resp.text();
  return new Response(text, {
    status: resp.status,
    headers: {
      "content-type": resp.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

// ── helpers ───────────────────────────────────────────────────────────

function isMetaPath(pathname: string): boolean {
  return pathname === "/health" || pathname === "/healthz" || pathname === "/readyz" || pathname === "/_app/meta";
}

async function bodyWithQuery(req: Request, url: URL): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (req.method === "POST") {
    const text = await req.text();
    try {
      body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch {
      return { __invalidJson: true };
    }
  }
  for (const [key, value] of url.searchParams) {
    if (!(key in body)) body[key] = value;
  }
  return body;
}

async function internalTrustSecret(env: Env): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch {
    return "";
  }
}

function embedHtml(): string {
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Media Gamers</title>
<style>body{font-family:system-ui;margin:0;padding:16px;background:#0f0f23;color:#e0e0e0}h1{font-size:1.2rem;color:#6c5ce7}</style></head>
<body>
<h1>Media Gamers</h1>
<p>AI-powered gaming intelligence — LangGraph autopilot every 30 min.</p>
<script>window.parent?.postMessage({type:'etzhayyim:embed:ready',nanoid:'a7m8oocs'},'*')</script>
</body></html>`;
}

function html(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}
