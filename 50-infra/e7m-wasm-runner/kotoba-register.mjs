/**
 * kotoba-register — bind a deployed WASM actor's content CID into the kotoba
 * Datom log (ADR-2606064500). This is the "register" leg of the kotoba-premise
 * deploy: where the Cloudflare path mutated a CF Worker registry / wrangler
 * config, the kotoba path appends a Datom to the canonical log (ADR-2605312345)
 * — IPFS holds the bytes, kotoba holds the binding, no Cloudflare in the loop.
 *
 * Two records, both `kg.ingest_batch` entities (shape matches the wasm-sbom
 * generator, ADR-2606036000, so the EXISTING purl↔CVE / SBOM joins compose):
 *   1. WasmActorImage  id=<cid>          — the immutable image (codec/size/etc).
 *   2. actor.<handle>  claim actor/wasm-cid=<cid> — the mutable binding the apex
 *      did.json reads (kotoba.ts → EtzhayyimWasmComponent service endpoint).
 *
 * Write posture: NO server key (ADR-2605231525). A write to the canonical log
 * needs an operator AT-session token; without `KOTOBA_TOKEN` this is a DRY RUN
 * that returns the body it WOULD post (same convention as every kotoba/deploy.sh).
 */

const INGEST_XRPC = "com.etzhayyim.apps.kotobase.kg.ingest_batch";

/**
 * Build the `kg.ingest_batch` body that binds <actor> → <cid>.
 * @returns {{entities: Array<object>}}
 */
export function buildIngestBody({
  cid,
  actor,
  codec,
  byteSize,
  blockCount,
  did,
  adr = "2606064500",
  programType = "actor",
  graph,
  deployedAt,
}) {
  if (!cid) throw new Error("buildIngestBody: cid required");
  if (!actor) throw new Error("buildIngestBody: actor required");
  const g = graph ?? `com.etzhayyim.${actor}`;
  const image = {
    id: cid,
    type: "WasmActorImage",
    graph: g,
    claims: [
      { pred: "wasm/programCid", value: cid },
      { pred: "wasm/actor", value: actor },
      { pred: "wasm/programType", value: programType },
      { pred: "wasm/codec", value: codec },
      { pred: "wasm/byteSize", value: String(byteSize) },
      { pred: "wasm/blockCount", value: String(blockCount) },
      { pred: "wasm/ipfsUri", value: `ipfs://${cid}` },
      { pred: "wasm/adr", value: adr },
      ...(did ? [{ pred: "wasm/agentDid", value: did }] : []),
      ...(deployedAt ? [{ pred: "wasm/deployedAt", value: deployedAt }] : []),
    ],
  };
  // The mutable handle→CID binding the did.json EtzhayyimWasmComponent reads.
  const binding = {
    id: `actor.${actor}`,
    type: "Actor",
    graph: "actors-v1",
    claims: [
      { pred: "actor/handle", value: actor },
      { pred: "actor/wasm-cid", value: cid },
    ],
    relations: [{ pred: "actor/wasmImage", dstId: cid }],
  };
  return { entities: [image, binding] };
}

/**
 * POST the ingest body to a kotoba node — or DRY RUN when no operator token.
 * @returns {Promise<{posted:boolean, endpoint:string, body:object, status?:number}>}
 */
export async function registerInKotoba({
  cid,
  actor,
  codec,
  byteSize,
  blockCount,
  did,
  adr,
  graph,
  deployedAt,
  kotobaUrl = process.env.KOTOBA_URL ?? "http://127.0.0.1:8077",
  token = process.env.KOTOBA_TOKEN,
  fetchImpl = fetch,
}) {
  const body = buildIngestBody({ cid, actor, codec, byteSize, blockCount, did, adr, graph, deployedAt });
  const endpoint = `${kotobaUrl.replace(/\/$/, "")}/xrpc/${INGEST_XRPC}`;
  if (!token) {
    // no-server-key: an unauthenticated process cannot mutate the canonical log.
    return { posted: false, endpoint, body, reason: "no KOTOBA_TOKEN — dry run" };
  }
  const res = await fetchImpl(endpoint, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`kotoba ingest failed: ${res.status} ${await res.text().catch(() => "")}`);
  }
  return { posted: true, endpoint, body, status: res.status };
}
