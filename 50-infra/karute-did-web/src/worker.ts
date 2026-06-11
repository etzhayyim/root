import didDoc from "../did.json";

/**
 * karute did:web Worker
 *
 * Three responsibilities:
 *
 *   1) DID Document — served at `https://karute.etzhayyim.com/.well-known/did.json`
 *      per the W3C did:web spec. Resolves `did:web:karute.etzhayyim.com`.
 *
 *   2) XRPC dispatch — `/xrpc/*` is forwarded to the LangServer Pod
 *      (default `https://karu7t3e.etzhayyim.com`, overridable via
 *      XRPC_KARUTE_UPSTREAM var). The Worker is intentionally thin —
 *      it does not validate XRPC payloads; the Pod side performs lexicon
 *      validation against @etzhayyim/lexicons-bundle.
 *
 *   3) Static frontend — every other path is reverse-proxied to the
 *      Svelte SuperApp bundle on Cloudflare Pages (KARUTE_STATIC_UPSTREAM).
 *
 * Per ADR-2605231900 (deployment topology) + ADR-2605231100 (karute EMR
 * Phase 1) + ADR-2605181100 (PHI envelope rule — this Worker MUST NOT
 * decrypt records; it only routes).
 */

interface Env {
  XRPC_KARUTE_UPSTREAM?: string;
  KARUTE_STATIC_UPSTREAM?: string;
}

const DID_CACHE_SECONDS = 300;

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // (1) DID Document
    if (url.pathname === "/.well-known/did.json") {
      return new Response(JSON.stringify(didDoc), {
        status: 200,
        headers: {
          "content-type": "application/did+json; charset=utf-8",
          "cache-control": `public, max-age=${DID_CACHE_SECONDS}`,
          "access-control-allow-origin": "*",
        },
      });
    }

    // (1b) Health probe — single endpoint Worker-side that does not depend
    // on the LangServer Pod being up. Returns 200 OK if this Worker is alive.
    if (url.pathname === "/healthz") {
      return new Response(
        JSON.stringify({ ok: true, worker: "karute-did-web", did: didDoc.id }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }

    // (2) XRPC dispatch
    if (url.pathname.startsWith("/xrpc/")) {
      const upstream = env.XRPC_KARUTE_UPSTREAM;
      if (!upstream) {
        return jsonError(503, "UpstreamNotConfigured", "XRPC_KARUTE_UPSTREAM is not set. Apply 50-infra/k8s/lg-karute and CF Tunnel + populate wrangler.toml [vars].");
      }
      const target = new URL(upstream);
      target.pathname = url.pathname;
      target.search = url.search;
      return fetch(target.toString(), {
        method: req.method,
        headers: filterRequestHeaders(req.headers),
        body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
      });
    }

    // (3) Static frontend
    const staticUpstream = env.KARUTE_STATIC_UPSTREAM;
    if (!staticUpstream) {
      return jsonError(503, "StaticBundleNotConfigured", "KARUTE_STATIC_UPSTREAM is not set. Run `wrangler pages deploy dist/` and populate wrangler.toml [vars].");
    }
    const target = new URL(staticUpstream);
    target.pathname = url.pathname === "/" ? "/" : url.pathname;
    target.search = url.search;
    return fetch(target.toString(), {
      method: req.method,
      headers: filterRequestHeaders(req.headers),
    });
  },
} satisfies ExportedHandler<Env>;

function jsonError(status: number, error: string, message: string): Response {
  return new Response(JSON.stringify({ error, message }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function filterRequestHeaders(h: Headers): Headers {
  const out = new Headers();
  for (const [k, v] of h.entries()) {
    const lk = k.toLowerCase();
    if (lk === "host" || lk === "cf-connecting-ip" || lk.startsWith("cf-")) continue;
    out.set(k, v);
  }
  return out;
}
