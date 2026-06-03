/**
 * etzhayyim XRPC reverse-proxy
 *
 * Routes inbound requests on the etzhayyim.com zone to the matching
 * etzhayyim.com-zoned upstream workers via service bindings. Lets the
 * etzhayyim.com namespace serve the existing AT Protocol / Bluesky
 * stack without redeploying the upstreams.
 *
 *   atproto.etzhayyim.com  → etzhayyim-pds-2603241700 (PDS)
 *   bsky.etzhayyim.com     → etzhayyim-appview        (AppView)
 *   authn.etzhayyim.com    → etzhayyim-auth           (Passkey)
 *   mcp.etzhayyim.com      → etzhayyim-agentgateway   (MCP router)
 *
 * Per-host hostname rewrite: the upstream expects its canonical etzhayyim.com
 * host (e.g. it may check Host / Origin / CORS allow-lists). The proxy
 * rewrites the URL hostname before invoking the binding so the upstream
 * sees the same request shape it would on its native zone.
 */

interface Env {
  PDS: Fetcher;
  APPVIEW: Fetcher;
  AUTHN: Fetcher;
  MCP: Fetcher;
}

const HOST_MAP: Record<string, { upstream: keyof Env; rewriteHost: string }> = {
  "atproto.etzhayyim.com": { upstream: "PDS",     rewriteHost: "atproto.etzhayyim.com" },
  "bsky.etzhayyim.com":    { upstream: "APPVIEW", rewriteHost: "bsky.etzhayyim.com" },
  "authn.etzhayyim.com":   { upstream: "AUTHN",   rewriteHost: "authn.etzhayyim.com" },
  "mcp.etzhayyim.com":     { upstream: "MCP",     rewriteHost: "mcp.etzhayyim.com" },
};

const STRIPPED_RESPONSE_HEADERS = new Set<string>([
  "set-cookie",
  "content-security-policy",
  "content-security-policy-report-only",
  "strict-transport-security",
  "alt-svc",
]);

function buildUpstreamRequest(request: Request, rewriteHost: string): Request {
  const upstreamUrl = new URL(request.url);
  upstreamUrl.hostname = rewriteHost;
  upstreamUrl.protocol = "https:";
  upstreamUrl.port = "";

  const fwdHeaders = new Headers(request.headers);
  fwdHeaders.delete("host");
  fwdHeaders.set("x-forwarded-host", new URL(request.url).hostname);
  fwdHeaders.set("x-forwarded-proto", "https");

  return new Request(upstreamUrl.toString(), {
    method: request.method,
    headers: fwdHeaders,
    body: request.body,
    redirect: "manual",
  });
}

function rewriteUpstreamResponse(upstream: Response, originalHost: string, rewriteHost: string): Response {
  const headers = new Headers(upstream.headers);
  for (const h of STRIPPED_RESPONSE_HEADERS) headers.delete(h);

  headers.set("strict-transport-security", "max-age=31536000; includeSubDomains");
  headers.set("x-proxied-by", "etzhayyim-xrpc-proxy");
  headers.set("x-proxied-upstream", rewriteHost);

  // Rewrite redirect Location header back to the etzhayyim host so the
  // client stays on the etzhayyim.com namespace.
  const loc = headers.get("location");
  if (loc) {
    try {
      const locUrl = new URL(loc, `https://${rewriteHost}/`);
      if (locUrl.hostname === rewriteHost) {
        locUrl.hostname = originalHost;
        headers.set("location", locUrl.toString());
      }
    } catch {
      /* relative or malformed — leave alone */
    }
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const route = HOST_MAP[url.hostname];

    if (!route) {
      return new Response(`No upstream binding for host: ${url.hostname}`, {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    try {
      const upstream = await env[route.upstream].fetch(
        buildUpstreamRequest(request, route.rewriteHost),
      );
      return rewriteUpstreamResponse(upstream, url.hostname, route.rewriteHost);
    } catch (err) {
      return new Response(
        `Service binding fetch failed (${route.upstream} → ${route.rewriteHost}): ${err instanceof Error ? err.message : String(err)}`,
        {
          status: 502,
          headers: {
            "content-type": "text/plain; charset=utf-8",
            "x-proxied-by": "etzhayyim-xrpc-proxy",
            "x-proxied-upstream": `service:${String(route.upstream)}`,
          },
        },
      );
    }
  },
} satisfies ExportedHandler<Env>;
