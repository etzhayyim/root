import { createAuthedEtzhayyim, extractBearerToken } from "@etzhayyim/sdk-auth";
import * as sbomRwFree from "@etzhayyim/sbom-kotoba";
interface Env { ACTOR_DID: string; PDS_URL: string; L2_RPC_URL: string; PDS_ACCESS_JWT?: string; PDS_REFRESH_JWT?: string; }
type Handler = (e: Etzhayyim, input: unknown) => Promise<unknown>;
const NSID_BASE = "com.etzhayyim.apps.sbom";
interface RouteConfig { method: "POST" | "GET"; handler: Handler; }
const routes: Record<string, RouteConfig> = {
  [`${NSID_BASE}.registerArtifact`]: { method: "POST", handler: (e, input) => sbomRwFree.registerArtifact(e, input as any) },
  [`${NSID_BASE}.getArtifact`]: { method: "GET", handler: (e, input) => sbomRwFree.getArtifact(e, input as any) },
  [`${NSID_BASE}.registerComponent`]: { method: "POST", handler: (e, input) => sbomRwFree.registerComponent(e, input as any) },
  [`${NSID_BASE}.listComponents`]: { method: "GET", handler: (e, input) => sbomRwFree.listComponents(e, input as any) },
  [`${NSID_BASE}.cveIngestOsv`]: { method: "POST", handler: (e, input) => sbomRwFree.cveIngestOsv(e, input as any) },
  [`${NSID_BASE}.registerVulnMatch`]: { method: "POST", handler: (e, input) => sbomRwFree.registerVulnMatch(e, input as any) },
  [`${NSID_BASE}.listVulnMatches`]: { method: "GET", handler: (e, input) => sbomRwFree.listVulnMatches(e, input as any) },
  [`${NSID_BASE}.registerPatchPolicy`]: { method: "POST", handler: (e, input) => sbomRwFree.registerPatchPolicy(e, input as any) },
  [`${NSID_BASE}.registerPatchAction`]: { method: "POST", handler: (e, input) => sbomRwFree.registerPatchAction(e, input as any) },
  [`${NSID_BASE}.getBlastRadius`]: { method: "GET", handler: (e, input) => sbomRwFree.getBlastRadius(e, input as any) },
  [`${NSID_BASE}.getSlaTimer`]: { method: "GET", handler: (e, input) => sbomRwFree.getSlaTimer(e, input as any) },
  [`${NSID_BASE}.listOverdueVulnMatches`]: { method: "GET", handler: (e, input) => sbomRwFree.listOverdueVulnMatches(e, input as any) },
  [`${NSID_BASE}.getArtifactDependents`]: { method: "GET", handler: (e, input) => sbomRwFree.getArtifactDependents(e, input as any) },
  [`${NSID_BASE}.analyzeApp`]: { method: "GET", handler: (e, input) => sbomRwFree.analyzeApp(e, input as any) },
  [`${NSID_BASE}.recall`]: { method: "POST", handler: (e, input) => sbomRwFree.recall(e, input as any) },
  [`${NSID_BASE}.updateComponentSupplier`]: { method: "POST", handler: (e, input) => sbomRwFree.updateComponentSupplier(e, input as any) },
  [`${NSID_BASE}.health`]: { method: "GET", handler: (e, input) => sbomRwFree.health(e, input as any) },
};
function mapStatus(status?: string): number { return status?.includes("notFound") ? 404 : status?.includes("invalid") || status === "rejected" ? 400 : 200; }
function jsonResponse(body: unknown, status: number = 200, init?: ResponseInit): Response { return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...init?.headers }, ...init }); }
export default { async fetch(req: Request, env: Env): Promise<Response> { const url = new URL(req.url); if (!url.pathname.startsWith("/xrpc/")) return jsonResponse({ error: "NotFound" }, 404); const nsid = url.pathname.slice("/xrpc/".length); const route = routes[nsid]; if (!route) return jsonResponse({ error: "MethodNotFound", nsid }, 404); if (req.method !== route.method) return jsonResponse({ error: "MethodNotAllowed" }, 405); const bearerToken = extractBearerToken(req);
    const e = createAuthedEtzhayyim({ env, bearerToken }); try { const input = route.method === "POST" ? await req.json().catch(() => ({})) : Object.fromEntries(url.searchParams.entries()); const result = await route.handler(e, input); return jsonResponse(result, mapStatus((result as any)?.status)); } catch (err) { return jsonResponse({ error: "InternalError", message: err instanceof Error ? err.message : String(err) }, 500); } }} satisfies ExportedHandler<Env>;
