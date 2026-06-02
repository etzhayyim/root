import didDoc from "../did.json";

/**
 * etzhayyim-dataset-pinner did:web Worker
 *
 * Serves the DID Document for did:web:dataset-pinner.etzhayyim.com at
 * the spec-required resolution endpoint
 * `https://dataset-pinner.etzhayyim.com/.well-known/did.json`.
 *
 * Identity of the religious-corp dataset pinner that:
 *   - Mirrors annex-store objects to IPFS via Kubo (sidecar publisher)
 *   - Emits `com.etzhayyim.substrate.datasetPin` records to PDS
 *
 * Distinct from `pinner.etzhayyim.com` (MST CAR pinner, ADR-2605171800
 * Stage 4) — that actor pins firehose-driven MST shards continuously,
 * this one pins operator-triggered datasets per ADR-2605241500.
 *
 * AT-Protocol clients resolve this DID via `/.well-known/did.json`.
 * Service entries route resolvers to the central PDS at
 * pds.etzhayyim.com (where datasetPin records live) and to the actor's
 * own HTTPS surface (Phase 2 — actor runtime on operator workstations,
 * not a public Worker).
 *
 * Per ADR-2605241500 + ADR-2605172000 substrate posture.
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

    if (url.pathname === "/healthz") {
      return new Response("ok\n", {
        status: 200,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    return new Response("Not Found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
} satisfies ExportedHandler;
