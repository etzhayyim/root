import { createAuthedEtzhayyim, extractBearerToken } from "@etzhayyim/sdk-auth";
import * as otakiageRwFree from "@etzhayyim/otakiage-kotoba";
interface Env { ACTOR_DID: string; PDS_URL: string; L2_RPC_URL: string; PDS_ACCESS_JWT?: string; PDS_REFRESH_JWT?: string; }
type Handler = (e: Etzhayyim, input: unknown) => Promise<unknown>;
const NSID_BASE = "com.etzhayyim.otakiage";
interface RouteConfig { method: "POST" | "GET"; handler: Handler; }
const routes: Record<string, RouteConfig> = {
  [`${NSID_BASE}.submitItem`]: { method: "POST", handler: (e, input) => otakiageRwFree.submitItem(e, input as any) },
  [`${NSID_BASE}.getItem`]: { method: "GET", handler: (e, input) => otakiageRwFree.getItem(e, input as any) },
  [`${NSID_BASE}.listItems`]: { method: "GET", handler: (e, input) => otakiageRwFree.listItems(e, input as any) },
  [`${NSID_BASE}.requestReuse`]: { method: "POST", handler: (e, input) => otakiageRwFree.requestReuse(e, input as any) },
  [`${NSID_BASE}.handover`]: { method: "POST", handler: (e, input) => otakiageRwFree.handover(e, input as any) },
  [`${NSID_BASE}.expire`]: { method: "POST", handler: (e, input) => otakiageRwFree.expire(e, input as any) },
  [`${NSID_BASE}.requestRitual`]: { method: "POST", handler: (e, input) => otakiageRwFree.requestRitual(e, input as any) },
  [`${NSID_BASE}.ritualize`]: { method: "POST", handler: (e, input) => otakiageRwFree.ritualize(e, input as any) },
  [`${NSID_BASE}.issueCertificate`]: { method: "POST", handler: (e, input) => otakiageRwFree.issueCertificate(e, input as any) },
  [`${NSID_BASE}.anchorCertificate`]: { method: "POST", handler: (e, input) => otakiageRwFree.anchorCertificate(e, input as any) },
  [`${NSID_BASE}.scheduleMatsuri`]: { method: "POST", handler: (e, input) => otakiageRwFree.scheduleMatsuri(e, input as any) },
  [`${NSID_BASE}.coverage`]: { method: "GET", handler: (e, input) => otakiageRwFree.coverage(e, input as any) },
  [`${NSID_BASE}.agentChat`]: { method: "POST", handler: (e, input) => otakiageRwFree.agentChat(e, input as any) },
};
function mapStatus(status?: string): number { return status === "notFound" || status?.includes("notFound") ? 404 : status === "rejected" || status?.includes("invalid") ? 400 : 200; }
function jsonResponse(body: unknown, status: number = 200, init?: ResponseInit): Response { return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...init?.headers }, ...init }); }
export default { async fetch(req: Request, env: Env): Promise<Response> { const url = new URL(req.url); if (!url.pathname.startsWith("/xrpc/")) return jsonResponse({ error: "NotFound" }, 404); const nsid = url.pathname.slice("/xrpc/".length); const route = routes[nsid]; if (!route) return jsonResponse({ error: "MethodNotFound", nsid }, 404); if (req.method !== route.method) return jsonResponse({ error: "MethodNotAllowed" }, 405); const bearerToken = extractBearerToken(req);
    const e = createAuthedEtzhayyim({ env, bearerToken }); try { const input = route.method === "POST" ? await req.json().catch(() => ({})) : Object.fromEntries(url.searchParams.entries()); const result = await route.handler(e, input); return jsonResponse(result, mapStatus((result as any)?.status)); } catch (err) { return jsonResponse({ error: "InternalError", message: err instanceof Error ? err.message : String(err) }, 500); } }} satisfies ExportedHandler<Env>;
