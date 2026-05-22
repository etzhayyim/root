import didDoc from "../did.json";

/**
 * etzhayyim did:web Worker + apex reverse proxy
 *
 * Three responsibilities:
 *
 * 1) Entity DID Document — served at `https://etzhayyim.com/.well-known/did.json`
 *    per the W3C did:web spec. Resolves `did:web:etzhayyim.com`.
 *
 * 2) Per-actor DID Document — served at
 *    `https://etzhayyim.com/actor/<handle>/did.json`. Resolves
 *    `did:web:etzhayyim.com:actor:<handle>` per W3C did:web colon-to-slash
 *    path syntax. Per ADR-2605212030 §D2, the canonical public-facing
 *    DID is `did:web:<handle>.etzhayyim.com` (subdomain form); the
 *    path-based form here is the immediate stand-in until wildcard DNS
 *    + a wildcard CF route are provisioned. Both forms MUST resolve to
 *    the same actor (bidirectional pointer in the returned document).
 *
 * 3) Apex landing & all other paths — reverse-proxied to UPSTREAM_HOST
 *    (default `yoro.etzhayyim.com`). This unblocks `https://etzhayyim.com/`
 *    while a dedicated etzhayyim landing page is being authored. yoro
 *    is a SvelteKit app served from Cloudflare; assets use relative URLs
 *    so the proxy is transparent.
 *
 * Route binding (wrangler.toml):
 *   pattern = "etzhayyim.com/*"
 *   zone_name = "etzhayyim.com"
 *
 * Excluded from proxy (always served locally by this Worker):
 *   - /.well-known/did.json                — entity DID Document
 *   - /actor/<handle>/did.json             — per-actor DID Document
 *   - future: /.well-known/atproto-did, /.well-known/security.txt, etc.
 */

const UPSTREAM_HOST = "yoro.etzhayyim.com";

// Service binding name — populated from wrangler.toml [[services]] block.
interface Env {
  YORO: Fetcher;
  // Phase α P1 (ADR-2605212030): chain config for per-actor DID resolution.
  // Set in wrangler.toml [vars] once EtzhayyimAuthz is deployed to Base Sepolia.
  AUTHZ_CONTRACT_ADDRESS?: string;
  BASE_RPC_URL?: string;
  CHAIN_ID?: string;
  // Per-NSID-family XRPC upstream origins (populated from wrangler.toml [vars]).
  // New actors are added here, NOT as new subdomains — this Worker is the
  // single etzhayyim.com endpoint per ADR-2605212030 §D2.
  XRPC_UNISPSC_UPSTREAM?: string;
}

// ─── XRPC routing ───────────────────────────────────────────────────────
//
// All `/xrpc/{NSID}` requests are routed by NSID *prefix* to the upstream
// declared in env. Keeping this as a static map (rather than a generic
// "look up the NSID owner" call) means the Worker stays a single fetch hop
// and a misconfigured upstream is a deploy-time error, not a runtime one.

interface NsidRoute {
  prefix: string;
  upstream: keyof Env; // must point to a string-valued Env field
}

const XRPC_ROUTES: NsidRoute[] = [
  { prefix: "ai.gftd.apps.unispsc.", upstream: "XRPC_UNISPSC_UPSTREAM" },
];

function findXrpcRoute(nsid: string): NsidRoute | null {
  for (const r of XRPC_ROUTES) {
    if (nsid.startsWith(r.prefix)) return r;
  }
  return null;
}

async function proxyXrpc(
  request: Request,
  upstream: string,
  nsid: string,
): Promise<Response> {
  const incoming = new URL(request.url);
  const target = new URL(upstream);
  // Preserve the canonical XRPC path so the upstream sees the same NSID.
  target.pathname = `/xrpc/${nsid}`;
  target.search = incoming.search;

  const fwd = new Headers(request.headers);
  fwd.delete("host");
  fwd.set("x-forwarded-host", "etzhayyim.com");
  fwd.set("x-forwarded-proto", "https");
  fwd.set("x-etzhayyim-nsid", nsid);

  try {
    const upstreamResp = await fetch(target.toString(), {
      method: request.method,
      headers: fwd,
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : request.body,
      redirect: "manual",
    });
    const respHeaders = new Headers(upstreamResp.headers);
    for (const h of STRIPPED_RESPONSE_HEADERS) respHeaders.delete(h);
    respHeaders.set("x-proxied-by", "etzhayyim-did-web");
    respHeaders.set("x-proxied-upstream", upstream);
    respHeaders.set(
      "strict-transport-security",
      "max-age=31536000; includeSubDomains",
    );
    return new Response(upstreamResp.body, {
      status: upstreamResp.status,
      statusText: upstreamResp.statusText,
      headers: respHeaders,
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: "UpstreamUnreachable",
        message:
          err instanceof Error ? err.message : "xrpc upstream fetch failed",
        nsid,
      }),
      {
        status: 502,
        headers: {
          "content-type": "application/json; charset=utf-8",
          "x-proxied-by": "etzhayyim-did-web",
        },
      },
    );
  }
}

// ─── Per-actor DID Document ─────────────────────────────────────────────

// W3C-compliant handle: lowercase alnum + hyphen, 1-63 chars, no leading/
// trailing hyphen. Matches DNS label rules (so the subdomain form
// `<handle>.etzhayyim.com` is also a valid DNS name).
const HANDLE_REGEX = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;

function buildPerActorDidDoc(handle: string, env: Env): Record<string, unknown> {
  const pathBasedDid = `did:web:etzhayyim.com:actor:${handle}`;
  const subdomainDid = `did:web:${handle}.etzhayyim.com`;
  const alsoKnownAs: string[] = [subdomainDid];

  // When chain integration lands, embed the did:erc725:base form by reading
  // EtzhayyimAuthz.resolveDwebHandle(keccak256("<handle>.etzhayyim.com")).
  // For the scaffold we expose the planned format with a placeholder rootId.
  if (env.AUTHZ_CONTRACT_ADDRESS) {
    alsoKnownAs.push(
      `did:erc725:base:${env.AUTHZ_CONTRACT_ADDRESS}#__rootId-pending-chain-lookup__`,
    );
  }

  return {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/suites/jws-2020/v1",
    ],
    id: pathBasedDid,
    alsoKnownAs,
    // verificationMethod, authentication, etc. populated from on-chain Root.activeKey
    // when chain integration lands. Phase α P1 scaffold returns an empty array
    // so the document validates against W3C DID Core minimal requirements.
    verificationMethod: [],
    service: [
      {
        id: `${pathBasedDid}#etzhayyim-authz`,
        type: "EtzhayyimAuthzResolver",
        serviceEndpoint: env.AUTHZ_CONTRACT_ADDRESS
          ? `https://authz.etzhayyim.com/xrpc/org.etzhayyim.authz.resolveRoot?dwebHandle=${encodeURIComponent(handle)}.etzhayyim.com`
          : null,
      },
    ],
    _meta: {
      adr: "2605212030",
      phase: "α P1 scaffold",
      note: env.AUTHZ_CONTRACT_ADDRESS
        ? "rootId placeholder in alsoKnownAs[1] is pending on-chain lookup wiring"
        : "AUTHZ_CONTRACT_ADDRESS not configured; alsoKnownAs[did:erc725:base] omitted",
    },
  };
}

// Headers we strip from the upstream response before sending to the client.
// `set-cookie` is dropped because the cookie domain would be wrong
// (yoro.etzhayyim.com), and we don't want cross-domain cookie shenanigans.
const STRIPPED_RESPONSE_HEADERS = new Set([
  "set-cookie",
  "content-security-policy",      // upstream CSP may reference yoro.etzhayyim.com
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

  // If upstream returned a redirect with a yoro.etzhayyim.com Location, rewrite it
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
    // 1) Entity DID Document — local, no upstream call.
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
    // 2) Per-actor DID Document — `/actor/<handle>/did.json`.
    //    W3C: did:web:etzhayyim.com:actor:<handle>
    //    See buildPerActorDidDoc for the document shape (Phase α P1).
    // ──────────────────────────────────────────────────────────────────
    {
      const m = url.pathname.match(/^\/actor\/([^/]+)\/did\.json$/);
      if (m) {
        if (request.method !== "GET" && request.method !== "HEAD") {
          return new Response("Method Not Allowed", {
            status: 405,
            headers: { allow: "GET, HEAD" },
          });
        }
        const handle = decodeURIComponent(m[1]).toLowerCase();
        if (!HANDLE_REGEX.test(handle)) {
          return new Response(
            JSON.stringify({ error: "HandleInvalid", message: "handle must be 1-63 chars, lowercase alnum + hyphen, no leading/trailing hyphen" }),
            { status: 400, headers: { "content-type": "application/json; charset=utf-8" } },
          );
        }
        const doc = buildPerActorDidDoc(handle, env);
        return new Response(JSON.stringify(doc, null, 2) + "\n", {
          status: 200,
          headers: {
            "content-type": "application/did+json; charset=utf-8",
            // Shorter cache window than the entity doc; per-actor state can
            // change (key rotation, deactivation) and we want quicker invalidation.
            "cache-control": "public, max-age=60, must-revalidate",
            "access-control-allow-origin": "*",
            "x-content-type-options": "nosniff",
            "strict-transport-security": "max-age=31536000; includeSubDomains",
          },
        });
      }
    }

    // ──────────────────────────────────────────────────────────────────
    // 3) XRPC routing — `/xrpc/{NSID}` proxied by NSID prefix to the
    //    registered upstream (langserver pod, MCP gateway, etc.). One
    //    Worker handles every actor; new actors are added by appending
    //    to XRPC_ROUTES rather than spinning up a new subdomain.
    // ──────────────────────────────────────────────────────────────────
    {
      const m = url.pathname.match(/^\/xrpc\/([A-Za-z0-9._-]+)$/);
      if (m) {
        const nsid = m[1];
        const route = findXrpcRoute(nsid);
        if (!route) {
          return new Response(
            JSON.stringify({
              error: "MethodNotImplemented",
              message: `no upstream registered for NSID '${nsid}'`,
            }),
            {
              status: 501,
              headers: { "content-type": "application/json; charset=utf-8" },
            },
          );
        }
        const upstream = env[route.upstream] as string | undefined;
        if (!upstream) {
          return new Response(
            JSON.stringify({
              error: "UpstreamNotConfigured",
              message: `env.${String(route.upstream)} is empty`,
              nsid,
            }),
            {
              status: 503,
              headers: { "content-type": "application/json; charset=utf-8" },
            },
          );
        }
        return proxyXrpc(request, upstream, nsid);
      }
    }

    // ──────────────────────────────────────────────────────────────────
    // 4) All other paths — reverse-proxy to the yoro Worker via service
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
} satisfies ExportedHandler<Env>;
