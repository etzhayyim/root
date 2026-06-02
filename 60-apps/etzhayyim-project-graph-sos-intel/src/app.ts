// graph-sos-intel.etzhayyim.com — graph System-of-Systems intelligence actor
// Thin-edge dispatcher: inventory cron + briefing cron in LangServer BPMN-contract + Python.
// 3 methods: health / listRelations / listFindings

interface SecretBinding { get(): Promise<string>; }
interface Env {
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
  APP_NANOID?: string;
}
interface ExportedHandler<E> { fetch(req: Request, env: E): Promise<Response>; }

const NSID_PREFIX = "com.etzhayyim.apps.graphSosIntel.";
const ACTOR_DID = "did:web:graph-sos-intel.etzhayyim.com";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: ACTOR_DID,
        nanoid: env.APP_NANOID ?? "gs0s1nt7",
        execution: "edge-proxy+agentgateway-mcp+langserver",
        cron: [
          "R/PT15M: inventory vertex/edge/mv/idx → vertex_graph_sos_intel_snapshot",
          "R/PT6H:  topology briefing → vertex_graph_sos_intel_finding",
        ],
        methods: ["health", "listRelations", "listFindings"],
      });
    }

    const nsid = url.searchParams.get("nsid") ??
      url.pathname.replace(/^\/xrpc\//, "");
    if (!nsid.startsWith(NSID_PREFIX)) {
      return json({ error: "NotFound" }, 404);
    }

    return proxyToDispatcher(env, nsid, req);
  },
} satisfies ExportedHandler<Env>;

async function proxyToDispatcher(env: Env, nsid: string, req: Request): Promise<Response> {
  const dispatcherUrl = env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const secret = typeof env.DISPATCHER_INTERNAL_SECRET === "string"
    ? env.DISPATCHER_INTERNAL_SECRET
    : await env.DISPATCHER_INTERNAL_SECRET?.get() ?? "";
  const target = `${dispatcherUrl}/xrpc/${nsid}`;
  const headers = new Headers(req.headers);
  headers.set("x-etzhayyim-internal-secret", secret);
  headers.set("x-etzhayyim-actor-did", ACTOR_DID);
  return fetch(target, { method: req.method, headers, body: req.body });
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}
