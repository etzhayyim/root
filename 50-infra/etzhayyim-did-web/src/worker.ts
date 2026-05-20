import didDoc from "../did.json";

/**
 * etzhayyim did:web Worker + apex reverse proxy
 *
 * Two responsibilities:
 *
 * 1) DID Document — served at `https://etzhayyim.com/.well-known/did.json`
 *    per the W3C did:web spec.
 *
 * 2) Apex landing & all other paths — reverse-proxied to UPSTREAM_HOST
 *    (default `yoro.gftd.ai`). This unblocks `https://etzhayyim.com/`
 *    while a dedicated etzhayyim landing page is being authored. yoro
 *    is a SvelteKit app served from Cloudflare; assets use relative URLs
 *    so the proxy is transparent.
 *
 * Route binding (wrangler.toml):
 *   pattern = "etzhayyim.com/*"
 *   zone_name = "etzhayyim.com"
 *
 * Excluded from proxy (always served locally by this Worker):
 *   - /.well-known/did.json                — DID Document
 *   - future: /.well-known/atproto-did, /.well-known/security.txt, etc.
 */

const UPSTREAM_HOST = "yoro.gftd.ai";

// Service binding name — populated from wrangler.toml [[services]] block.
interface Env {
  YORO: Fetcher;
}

// Headers we strip from the upstream response before sending to the client.
// `set-cookie` is dropped because the cookie domain would be wrong
// (yoro.gftd.ai), and we don't want cross-domain cookie shenanigans.
const STRIPPED_RESPONSE_HEADERS = new Set([
  "set-cookie",
  "content-security-policy",      // upstream CSP may reference yoro.gftd.ai
  "content-security-policy-report-only",
  "strict-transport-security",    // we set our own
  "alt-svc",
]);

function buildUpstreamRequest(request: Request): Request {
  const upstreamUrl = new URL(request.url);
  upstreamUrl.hostname = UPSTREAM_HOST;
  upstreamUrl.protocol = "https:";
  upstreamUrl.port = "";

  const fwdHeaders = new Headers(request.headers);
  fwdHeaders.delete("host");
  fwdHeaders.set("x-forwarded-host", "etzhayyim.com");
  fwdHeaders.set("x-forwarded-proto", "https");

  return new Request(upstreamUrl.toString(), {
    method: request.method,
    headers: fwdHeaders,
    body: request.body,
    redirect: "manual",
  });
}

function rewriteUpstreamResponse(upstream: Response): Response {
  const headers = new Headers(upstream.headers);
  for (const h of STRIPPED_RESPONSE_HEADERS) headers.delete(h);

  // Our own HSTS — long max-age, includeSubDomains so did:web subdomain
  // resolution stays HTTPS-only.
  headers.set("strict-transport-security", "max-age=31536000; includeSubDomains");

  // Mark proxy hop so debugging is easier.
  headers.set("x-proxied-by", "etzhayyim-did-web");
  headers.set("x-proxied-upstream", UPSTREAM_HOST);

  // If upstream returned a redirect with a yoro.gftd.ai Location, rewrite it
  // to keep the user on etzhayyim.com.
  const loc = headers.get("location");
  if (loc) {
    try {
      const locUrl = new URL(loc, `https://${UPSTREAM_HOST}/`);
      if (locUrl.hostname === UPSTREAM_HOST) {
        locUrl.hostname = "etzhayyim.com";
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

    // ──────────────────────────────────────────────────────────────────
    // 1) DID Document — local, no upstream call.
    // ──────────────────────────────────────────────────────────────────
    if (url.pathname === "/.well-known/did.json") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return new Response("Method Not Allowed", {
          status: 405,
          headers: { allow: "GET, HEAD" },
        });
      }
      return new Response(JSON.stringify(didDoc, null, 2) + "\n", {
        status: 200,
        headers: {
          "content-type": "application/did+json; charset=utf-8",
          "cache-control": "public, max-age=300, must-revalidate",
          "access-control-allow-origin": "*",
          "x-content-type-options": "nosniff",
          "strict-transport-security": "max-age=31536000; includeSubDomains",
        },
      });
    }

    // ──────────────────────────────────────────────────────────────────
    // 2) All other paths — reverse-proxy to the yoro Worker via service
    // binding (env.YORO). This bypasses the CF edge/Bot Management block
    // that public-HTTP fetch hits inside the same zone.
    // ──────────────────────────────────────────────────────────────────
    try {
      const upstream = await env.YORO.fetch(buildUpstreamRequest(request));
      return rewriteUpstreamResponse(upstream);
    } catch (err) {
      return new Response(
        `Service binding fetch to magatama-yoro failed: ${err instanceof Error ? err.message : String(err)}`,
        {
          status: 502,
          headers: {
            "content-type": "text/plain; charset=utf-8",
            "x-proxied-by": "etzhayyim-did-web",
            "x-proxied-upstream": "service:magatama-yoro",
          },
        }
      );
    }
  },
} satisfies ExportedHandler;
