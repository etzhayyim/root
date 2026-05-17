import didDoc from "../did.json";

/**
 * etzhayyim did:web Worker
 *
 * Serves the DID Document for did:web:etzhayyim.com at the spec-required
 * resolution endpoint `https://etzhayyim.com/.well-known/did.json`.
 *
 * Route binding (wrangler.toml):
 *   pattern = "etzhayyim.com/.well-known/did.json"
 *   zone_name = "etzhayyim.com"
 *
 * All other paths return 404 so the same Worker can later be extended
 * to serve additional .well-known artifacts (atproto-did, openid-configuration,
 * security.txt, etc.) without colliding with the apex landing page or Pages
 * deployment.
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
