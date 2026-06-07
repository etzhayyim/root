// mailer.etzhayyim.com thin edge facade. Mailer business logic runs in AgentGateway MCP + pod-side LangServer.

interface SecretBinding { get(): Promise<string>; }
interface Env { ASSETS?: Fetcher; DISPATCHER_URL?: string; DISPATCHER_INTERNAL_SECRET?: string | SecretBinding; APP_NANOID?: string; }

const APP = "mailer";
const ACTOR = "did:web:mailer.etzhayyim.com";
const NSID_PREFIX = "ai.etzhayyim.apps.mailer.";
const PDS_ORIGIN = "https://atproto.etzhayyim.com";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: ACTOR,
        nanoid: env.APP_NANOID ?? "a8wwtz73",
        execution: "edge-assets+xrpc-proxy+bpmn+langserver",
        businessLogic: "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/mailer.py",
        bpmn: "etzhayyim-root/00-contracts/bpmn/ai/etzhayyim/mailer",
      });
    }

    if (url.pathname === "/api/emails") return proxyToDispatcher(env, "ai.etzhayyim.apps.mailer.listEmails", queryBody(url));
    if (url.pathname === "/api/bindings") return proxyToDispatcher(env, "ai.etzhayyim.apps.mailer.listBindings", queryBody(url));
    if (url.pathname === "/api/stats") return proxyToDispatcher(env, "ai.etzhayyim.apps.mailer.stats", {});

    const nsid = url.pathname.startsWith("/xrpc/") ? url.pathname.slice("/xrpc/".length) : "";
    if (nsid.startsWith(NSID_PREFIX) && (req.method === "POST" || req.method === "GET")) {
      const body = await bodyWithQuery(req, url);
      if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);
      return proxyToDispatcher(env, nsid, body);
    }
    if (url.pathname.startsWith("/xrpc/")) return proxyToPds(req);
    if (env.ASSETS) return env.ASSETS.fetch(req);
    return json({ error: "NotFound", message: `${APP} not found` }, 404);
  },
} satisfies ExportedHandler<Env>;

function queryBody(url: URL): Record<string, unknown> { const body: Record<string, unknown> = {}; for (const [k, v] of url.searchParams) body[k] = v; return body; }
async function bodyWithQuery(req: Request, url: URL): Promise<Record<string, unknown>> { let body: Record<string, unknown> = {}; if (req.method === "POST") { const text = await req.text(); try { body = text ? JSON.parse(text) : {}; } catch { return { __invalidJson: true }; } } for (const [k, v] of url.searchParams) if (!(k in body)) body[k] = v; return body; }
async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> { const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, ""); const headers: Record<string, string> = { "content-type": "application/json" }; const trust = await internalTrustSecret(env); if (trust) headers["x-internal-trust"] = trust; const resp = await fetch(`${base}/xrpc/${nsid}`, { method: "POST", headers, body: JSON.stringify(body) }); const text = await resp.text(); return new Response(text, { status: resp.status, headers: { "content-type": resp.headers.get("content-type") ?? "application/json", "cache-control": "no-store" } }); }
async function proxyToPds(req: Request): Promise<Response> { const inUrl = new URL(req.url); const outUrl = new URL(inUrl.pathname + inUrl.search, PDS_ORIGIN); const headers = new Headers(req.headers); headers.delete("host"); headers.delete("content-length"); const method = req.method.toUpperCase(); const body = method === "GET" || method === "HEAD" ? undefined : await req.arrayBuffer(); const resp = await fetch(outUrl, { method, headers, body: body && body.byteLength > 0 ? body : undefined }); const outHeaders = new Headers(resp.headers); outHeaders.set("access-control-allow-origin", "*"); return new Response(resp.body, { status: resp.status, headers: outHeaders }); }
async function internalTrustSecret(env: Env): Promise<string> { const binding = env.DISPATCHER_INTERNAL_SECRET; if (!binding) return ""; try { return typeof binding === "string" ? binding : await binding.get(); } catch { return ""; } }
function json(body: unknown, status = 200): Response { return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } }); }
