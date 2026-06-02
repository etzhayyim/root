import didDoc from "../did.json";

/**
 * etzhayyim ipfs-pinner did:web Worker
 *
 * Serves the DID Document for did:web:pinner.etzhayyim.com at the
 * spec-required resolution endpoint
 * `https://pinner.etzhayyim.com/.well-known/did.json`.
 *
 * Identity of the off-chain actor that consumes mst-projector CAR
 * files from a shared volume, pins them to ≥1 IPFS providers (Kubo /
 * Pinata / Web3.Storage / Filecoin via Storacha), and emits
 * `com.etzhayyim.substrate.ipfsPin` records to PDS. See
 * 50-infra/ipfs-pinner/ for the runtime.
 *
 * AT-Protocol clients resolve this DID via `/.well-known/did.json`.
 * Service entry routes resolvers to the central PDS at
 * pds.etzhayyim.com where ipfsPin records live.
 *
 * Per ADR-2605171800 Stage 4 + ADR-2605172000 substrate posture.
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
