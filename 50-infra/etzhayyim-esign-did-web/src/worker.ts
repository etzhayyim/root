import didDoc from "../did.json";

/**
 * etzhayyim-esign did:web Worker
 *
 * Serves the DID Document for did:web:esign.etzhayyim.com at the
 * spec-required resolution endpoint
 * `https://esign.etzhayyim.com/.well-known/did.json`.
 *
 * Identity of the religious-corp document-signing actor that issues,
 * collects, and completes `com.etzhayyim.esign.*` envelopes (per
 * ADR-2605231230). The runtime Worker lives at
 * `orgs/etzhayyim/com-etzhayyim-esign/`; on-chain anchoring is delegated to
 * anchor-cron (50-infra/anchor-cron/).
 *
 * AT-Protocol clients resolve this DID via `/.well-known/did.json`.
 * Service entries route resolvers to the central PDS at
 * pds.etzhayyim.com (where esign records live) and to the actor's own
 * HTTPS surface for XRPC procedure calls.
 *
 * Per ADR-2605231230 + ADR-2605172000 substrate posture.
 */
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: { allow: "GET, HEAD" },
      });
    }

    if (url.pathname === "/.well-known/did.json") {
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

    return new Response("Not Found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
} satisfies ExportedHandler;
