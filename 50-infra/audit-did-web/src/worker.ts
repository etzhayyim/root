import didDoc from "../did.json";

/**
 * audit did:web Worker
 *
 * Responsibilities:
 *
 *   1) DID Document — `https://audit.etzhayyim.com/.well-known/did.json`
 *      Resolves `did:web:audit.etzhayyim.com`. This DID is the standard
 *      auditor target referenced by karute (and other) actor manifests'
 *      `agent.invoke targetDid: did:web:audit.etzhayyim.com` steps.
 *
 *   2) XRPC dispatch — `/xrpc/com.etzhayyim.audit.emitAuditEvent` forwards
 *      to the aggregator service (which signs + writes the event record
 *      into the subject's PDS).
 *
 *   3) Healthz — `/healthz`.
 *
 * Per ADR-2605231700 (audit webhook subsystem).
 */

interface Env {
  AUDIT_AGGREGATOR_UPSTREAM?: string;
}

const DID_CACHE_SECONDS = 300;

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

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

    if (url.pathname === "/healthz") {
      return new Response(
        JSON.stringify({ ok: true, worker: "audit-did-web", did: didDoc.id }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }

    if (url.pathname.startsWith("/xrpc/")) {
      const upstream = env.AUDIT_AGGREGATOR_UPSTREAM;
      if (!upstream) {
        return jsonError(503, "UpstreamNotConfigured", "AUDIT_AGGREGATOR_UPSTREAM is not set.");
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

    return jsonError(404, "NotFound", "audit DID Worker exposes /.well-known/did.json + /xrpc/*");
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
