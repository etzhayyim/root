#!/usr/bin/env node
/**
 * e7m deploy — the kotoba-premise WASM-actor deploy (ADR-2606064500).
 *
 * The mirror image of `runner.mjs`. Where the legacy deploy
 * (`70-tools/etzhayyim-cli/deploy.go`) built a Docker image, pushed it, wrote a
 * `wrangler.jsonc` and ran `wrangler deploy` onto Cloudflare Containers, this
 * path is Cloudflare-free end to end:
 *
 *   .wasm bytes
 *     → buildCar()         content-address (raw single-block / dag-pb multi-block)
 *     → pin to IPFS        kubo /dag/import (live)  OR  drop a CAR for ipfs-pinner
 *     → registerInKotoba() append the handle→CID binding to the canonical Datom log
 *     → <name>.deploy.json a gateway-independent manifest; run via ANY IPFS gateway
 *
 * The CID is the only deploy artifact that matters: once the bytes are pinned and
 * the binding is in kotoba, `e7m-wasm-runner --cid <cid>` (or `--did <did>`) fetches
 * from any IPFS gateway, re-verifies against the CID, and runs — no apex Worker, no
 * server key (ADR-2605231525), no Cloudflare. Cloudflare's `/ipfs/` is then just
 * one optional gateway among many, not a dependency.
 *
 * Usage:
 *   node deploy.mjs --file actor.wasm --actor tsumugi [--did did:web:...:actor:tsumugi]
 *                   [--pin kubo|pinner|none] [--kubo http://127.0.0.1:5001]
 *                   [--pinner-dir /data/mst-projector] [--graph com.etzhayyim.tsumugi]
 *                   [--out actor.deploy.json] [--kotoba http://127.0.0.1:8077]
 *   KOTOBA_TOKEN=<op-jwt> node deploy.mjs ...   # actually write the kotoba binding
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { basename, join } from "node:path";
import { buildCar } from "./wasmcar.mjs";
import { registerInKotoba } from "./kotoba-register.mjs";

/** Pin a CAR to a local/LAN kubo node via the HTTP API (live). */
async function pinToKubo({ car, cid, kuboApi = "http://127.0.0.1:5001", fetchImpl = fetch }) {
  const form = new FormData();
  form.append("file", new Blob([car], { type: "application/vnd.ipld.car" }), "actor.car");
  const res = await fetchImpl(`${kuboApi.replace(/\/+$/, "")}/api/v0/dag/import?pin-roots=true`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`kubo dag/import: ${res.status} ${await res.text().catch(() => "")}`);
  const roots = [];
  for (const line of (await res.text()).split("\n")) {
    const t = line.trim();
    if (!t) continue;
    try {
      const cidStr = JSON.parse(t)?.Root?.Cid?.["/"];
      if (typeof cidStr === "string") roots.push(cidStr);
    } catch {
      /* skip non-JSON lines */
    }
  }
  if (!roots.includes(cid)) {
    throw new Error(`kubo imported roots [${roots.join(",")}] do not include our CID ${cid}`);
  }
  return { mode: "kubo", api: kuboApi, roots };
}

/** Drop a CAR where the existing ipfs-pinner daemon (ADR-2605171800 Stage 4)
 *  will discover and pin it: `<dataDir>/<encodeURIComponent(shardKey)>/<cid>.car`. */
function dropForPinner({ car, cid, dataDir = "/data/mst-projector", shardKey }) {
  const dir = join(dataDir, encodeURIComponent(shardKey));
  mkdirSync(dir, { recursive: true });
  const carPath = join(dir, `${cid}.car`);
  writeFileSync(carPath, car);
  return { mode: "pinner", carPath, shardKey };
}

/**
 * Deploy a WASM actor onto IPFS + kotoba. Returns the deploy manifest object.
 */
export async function deploy({
  file,
  bytes,
  actor,
  did,
  pin = "none",
  kuboApi,
  pinnerDir,
  shardKey,
  graph,
  kotobaUrl,
  kotobaToken = process.env.KOTOBA_TOKEN,
  adr = "2606064500",
  chunkSize,
  deployedAt = new Date().toISOString(),
  fetchImpl = fetch,
}) {
  const wasm = bytes ?? new Uint8Array(readFileSync(file));
  if (!actor) actor = basename(file ?? "actor.wasm").replace(/[-_.]?(core|agent)?\.wasm$/, "") || "actor";
  did = did ?? `did:web:etzhayyim.com:actor:${actor}`;

  // 1. content-address
  const { cid, car, codec, blockCount, byteSize } = await buildCar(wasm, { chunkSize });

  // 2. pin to IPFS (Cloudflare-free)
  let pinResult = { mode: "none", note: "compute-only; pin separately or via the ipfs-pinner daemon" };
  if (pin === "kubo") pinResult = await pinToKubo({ car, cid, kuboApi, fetchImpl });
  else if (pin === "pinner") pinResult = dropForPinner({ car, cid, dataDir: pinnerDir, shardKey: shardKey ?? graph ?? `com.etzhayyim.${actor}` });

  // 3. register the handle→CID binding in the canonical Datom log (operator-gated)
  const kotoba = await registerInKotoba({
    cid, actor, codec, byteSize, blockCount, did, adr, graph, deployedAt,
    kotobaUrl, token: kotobaToken, fetchImpl,
  });

  // 4. gateway-independent manifest
  const exec = codec === "raw" ? ["browser-local", "donated-mesh"] : ["donated-mesh"];
  return {
    schema: "com.etzhayyim.deploy.manifest/1",
    adr,
    actor,
    did,
    deployedAt,
    image: { cid, ipfsUri: `ipfs://${cid}`, gatewayPath: `/ipfs/${cid}`, codec, blockCount, byteSize },
    exec,
    run: {
      mesh: `node runner.mjs --cid ${cid}`,
      byDid: `node runner.mjs --did ${did}`,
      note: "resolves from ANY IPFS gateway (local kubo first), re-verifies CID, runs — no Cloudflare",
    },
    pin: pinResult,
    kotoba: { posted: kotoba.posted, endpoint: kotoba.endpoint, ...(kotoba.reason ? { reason: kotoba.reason } : {}) },
    didDocServiceHint: {
      id: `${did}#wasm`,
      type: "EtzhayyimWasmComponent",
      serviceEndpoint: `ipfs://${cid}`,
      "x-cid-codec": codec === "raw" ? "raw" : "dag-pb",
      "x-exec": exec.join("|"),
      "x-runtime": "kotoba-wasm",
    },
  };
}

// ── CLI ───────────────────────────────────────────────────────────────────────
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const val = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const file = val("--file") ?? args.find((a) => a.endsWith(".wasm"));
  if (!file) { console.error("usage: deploy.mjs --file <actor.wasm> [--actor <h>] [--pin kubo|pinner|none] ..."); process.exit(2); }
  deploy({
    file,
    actor: val("--actor"),
    did: val("--did"),
    pin: val("--pin") ?? "none",
    kuboApi: val("--kubo"),
    pinnerDir: val("--pinner-dir"),
    shardKey: val("--shard"),
    graph: val("--graph"),
    kotobaUrl: val("--kotoba"),
  })
    .then((manifest) => {
      const out = val("--out") ?? `${manifest.actor}.deploy.json`;
      writeFileSync(out, JSON.stringify(manifest, null, 2) + "\n");
      console.log(JSON.stringify(manifest, null, 2));
      console.error(`\n✓ deployed ${manifest.actor} → ${manifest.image.cid} (${manifest.image.codec}, ${manifest.image.byteSize}B)`);
      console.error(`  pin: ${manifest.pin.mode}   kotoba: ${manifest.kotoba.posted ? "written" : "dry-run (no KOTOBA_TOKEN)"}`);
      console.error(`  manifest: ${out}`);
    })
    .catch((e) => { console.error("deploy failed:", e.message); process.exit(1); });
}
