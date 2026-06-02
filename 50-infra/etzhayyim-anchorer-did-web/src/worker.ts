import didDoc from "../did.json";

/**
 * etzhayyim anchor-cron did:web Worker
 *
 * Serves the DID Document for did:web:anchorer.etzhayyim.com at the
 * spec-required resolution endpoint
 * `https://anchorer.etzhayyim.com/.well-known/did.json`.
 *
 * Identity of the off-chain actor that consumes
 * `com.etzhayyim.substrate.ipfsPin` records, anchors each unique
 * `rootCid` to EtzhayyimAnchor on Base L2, and emits
 * `com.etzhayyim.substrate.l2Anchor` receipts back to PDS. See
 * 50-infra/anchor-cron/ (substrate mode) for the runtime.
 *
 * AT-Protocol clients resolve this DID via `/.well-known/did.json`.
 * Service entry routes resolvers to the central PDS at
 * pds.etzhayyim.com where l2Anchor records live.
 *
 * Per ADR-2605171800 Stage 5b + ADR-2605172000 substrate posture.
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
