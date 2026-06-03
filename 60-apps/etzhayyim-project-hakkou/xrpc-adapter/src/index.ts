import {
  createAuthedEtzhayyim,
  extractBearerToken,
  type Etzhayyim,
} from "@etzhayyim/sdk-auth";
import * as hakkouRwFree from "@etzhayyim/hakkou-rw-free";

interface Env { ACTOR_DID: string; PDS_URL: string; L2_RPC_URL: string; }
  PDS_ACCESS_JWT?: string;
  PDS_REFRESH_JWT?: string;
type Handler = (e: Etzhayyim, input: unknown) => Promise<unknown>;
const NSID_BASE = "com.etzhayyim.hakkou";
interface RouteConfig { method: "POST" | "GET"; handler: Handler; }

const routes: Record<string, RouteConfig> = {
  [`${NSID_BASE}.startFerment`]: { method: "POST", handler: (e, input) => hakkouRwFree.startFerment(e, input as any) },
  [`${NSID_BASE}.getFerment`]: { method: "GET", handler: (e, input) => hakkouRwFree.getFerment(e, input as any) },
  [`${NSID_BASE}.updateFermentStatus`]: { method: "POST", handler: (e, input) => hakkouRwFree.updateFermentStatus(e, input as any) },
};

function mapStatus(status?: string): number { if (status === "rejected" || status === "notFound") return 400; return 200; }
function jsonResponse(body: unknown, status: number = 200, init?: ResponseInit): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...init?.headers }, ...init });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/xrpc/")) return jsonResponse({ error: "NotFound" }, 404);
    const nsid = url.pathname.slice("/xrpc/".length);
    const route = routes[nsid];
    if (!route) return jsonResponse({ error: "MethodNotFound", nsid }, 404);
    if (req.method !== route.method) return jsonResponse({ error: "MethodNotAllowed" }, 405);

    const e = new Etzhayyim({ did: env.ACTOR_DID, pdsUrl: env.PDS_URL, l2RpcUrl: env.L2_RPC_URL });
    let input: unknown;
    try {
      input = route.method === "POST" ? await req.json().catch(() => ({})) : Object.fromEntries(url.searchParams.entries());
      const typed = input as Record<string, unknown>;
      ["limit", "offset", "seq"].forEach(k => { if (typed[k]) typed[k] = Number(typed[k]); });
    } catch (err) {
      return jsonResponse({ error: "InvalidInput", message: `Failed to parse ${route.method === "POST" ? "JSON" : "query params"}` }, 400);
    }

    try {
      const result = await route.handler(e, input);
      return jsonResponse(result, mapStatus((result as any)?.status));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return jsonResponse({ error: "InternalError", message, nsid }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
