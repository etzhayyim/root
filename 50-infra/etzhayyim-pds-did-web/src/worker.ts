import didDoc from "../did.json";

/**
 * etzhayyim PDS did:web Worker
 *
 * Serves the DID Document for did:web:pds.etzhayyim.com at the
 * spec-required resolution endpoint
 * `https://pds.etzhayyim.com/.well-known/did.json`.
 *
 * Route binding (wrangler.toml):
 *   pattern = "pds.etzhayyim.com/.well-known/did.json"
 *
 * Other paths on pds.etzhayyim.com fall through to the CF tunnel CNAME
 * (DNS routing) → simeon Mac mini PDS on port 2583.
 *
 * Per ADR-2605172800 PDS deploy + ADR-2605172000 substrate posture.
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
