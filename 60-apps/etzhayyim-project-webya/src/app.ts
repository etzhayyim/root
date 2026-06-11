// webya.etzhayyim.com — homepage generation for 士業 + 一般企業 (ウェブ屋)
// T3 CF Worker: edge XRPC dispatcher + custom-domain HTML page serving.
// Business logic: LangGraph Server (createSite/reviseSite) + LangServer
// (domain.provision, domain.checkAllPending, seo.auditAllSites, query helpers).
// Page serving at edge via Hyperdrive SELECT on vertex_webya_page.html_content.

import { createKyselyDb } from "@etzhayyim/kotodama-host-sdk";

interface SecretBinding { get(): Promise<string>; }
interface HyperdriveBinding { connectionString: string; }
interface Env {
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
  HYPERDRIVE?: HyperdriveBinding;
  APP_NANOID?: string;
}
interface ExportedHandler<E> { fetch(req: Request, env: E): Promise<Response>; }

const NSID_PREFIX = "com.etzhayyim.apps.webya.";
const ACTOR_DID = "did:web:webya.etzhayyim.com";
const WEBYA_HOST = "webya.etzhayyim.com";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const host = url.hostname;

    // Health + meta (always on primary host)
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: ACTOR_DID,
        nanoid: env.APP_NANOID ?? "w3bya001",
        execution: "edge-bpmn+langgraph-granian",
        bpmn: "etzhayyim-root/00-contracts/bpmn/com/etzhayyim/webya",
        langgraph: "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/webya_site_generation.py",
        methods: [
          "createSite", "reviseSite",
          "provisionDomain",
          "getSite", "getSitePreview", "listSites",
          "coverage",
        ],
        routing: {
          "createSite": "langgraph",
          "reviseSite": "langgraph",
          "default": "langserver",
        },
      });
    }

    // XRPC proxy → bpmn-dispatcher (primary host only)
    if (host === WEBYA_HOST) {
      const nsid = url.pathname.startsWith("/xrpc/")
        ? url.pathname.slice("/xrpc/".length)
        : "";
      if (nsid.startsWith(NSID_PREFIX) && (req.method === "POST" || req.method === "GET")) {
        const body = await bodyWithQuery(req, url);
        if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);
        return proxyToDispatcher(env, nsid, body);
      }

      // Subdomain page serving: {slug}.webya.etzhayyim.com
      // (handled via wildcard CF for SaaS fallback hostname — not this Worker's route)
      return json({ error: "NotFound" }, 404);
    }

    // Custom-domain page serving:
    // - {slug}.webya.etzhayyim.com subdomains routed here via CF for SaaS
    // - client custom domains (e.g. example.com) via CF for SaaS CNAME
    if (env.HYPERDRIVE) {
      return serveSitePage(env, host, url.pathname);
    }

    return json({ error: "NotFound" }, 404);
  },
} satisfies ExportedHandler<Env>;

// Resolve site + page HTML from RisingWave, serve as text/html.
// Lookup priority:
//   1. exact custom_domain match (e.g. example.com)
//   2. subdomain slug match (e.g. tokyolaw-webya.etzhayyim.com → slug=tokyolaw)
async function serveSitePage(env: Env, host: string, pathname: string): Promise<Response> {
  try {
    const db = createKyselyDb((env as any).HYPERDRIVE);

    // Resolve site_id from host
    let siteId: string | null = null;

    // Try custom domain first
    const domainRow = await db
      .selectFrom("vertex_webya_domain" as any)
      .select(["site_id"] as any)
      .where("custom_domain" as any, "=", host)
      .where("ssl_status" as any, "=", "active")
      .limit(1)
      .executeTakeFirst() as any;

    if (domainRow) {
      siteId = domainRow.site_id;
    } else {
      // Try subdomain slug: {slug}.webya.etzhayyim.com
      const subdomain = host.endsWith(`.${WEBYA_HOST}`)
        ? host.slice(0, -(`.${WEBYA_HOST}`.length))
        : null;
      if (subdomain) {
        const siteRow = await db
          .selectFrom("vertex_webya_site" as any)
          .select(["vertex_id"] as any)
          .where("slug" as any, "=", subdomain)
          .where("status" as any, "=", "published")
          .limit(1)
          .executeTakeFirst() as any;
        if (siteRow) siteId = siteRow.vertex_id;
      }
    }

    if (!siteId) return htmlError(404, "Site not found");

    // Resolve page: root path → index, else path-based slug
    const pageSlug = pathname === "/" || pathname === "" ? "index" : pathname.replace(/^\//, "");

    const pageRow = await db
      .selectFrom("vertex_webya_page" as any)
      .select(["html_content", "page_title"] as any)
      .where("site_id" as any, "=", siteId)
      .where("slug" as any, "=", pageSlug)
      .limit(1)
      .executeTakeFirst() as any;

    if (!pageRow?.html_content) {
      // Fallback: try index page if slug not found
      if (pageSlug !== "index") {
        const indexRow = await db
          .selectFrom("vertex_webya_page" as any)
          .select(["html_content", "page_title"] as any)
          .where("site_id" as any, "=", siteId)
          .where("slug" as any, "=", "index")
          .limit(1)
          .executeTakeFirst() as any;
        if (indexRow?.html_content) {
          return html(indexRow.html_content);
        }
      }
      return htmlError(404, "Page not found");
    }

    return html(pageRow.html_content);
  } catch (err) {
    return htmlError(500, "Internal server error");
  }
}

async function bodyWithQuery(req: Request, url: URL): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (req.method === "POST") {
    const text = await req.text();
    try { body = text ? (JSON.parse(text) as Record<string, unknown>) : {}; }
    catch { return { __invalidJson: true }; }
  }
  for (const [k, v] of url.searchParams.entries()) {
    if (!(k in body)) body[k] = v;
  }
  return body;
}

async function proxyToDispatcher(
  env: Env,
  nsid: string,
  body: Record<string, unknown>,
): Promise<Response> {
  const dispatcherUrl = env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com";
  const secret = typeof env.DISPATCHER_INTERNAL_SECRET === "object"
    ? await env.DISPATCHER_INTERNAL_SECRET.get()
    : (env.DISPATCHER_INTERNAL_SECRET ?? "");
  const res = await fetch(`${dispatcherUrl}/xrpc/${nsid}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-internal-secret": secret },
    body: JSON.stringify(body),
  });
  const data = await res.text();
  return new Response(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function html(content: string): Response {
  return new Response(content, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
    },
  });
}

function htmlError(status: number, message: string): Response {
  return new Response(
    `<!doctype html><html><head><title>${status}</title></head><body><h1>${status}</h1><p>${message}</p></body></html>`,
    { status, headers: { "Content-Type": "text/html; charset=utf-8" } },
  );
}
