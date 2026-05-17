/**
 * ipfs-pinner — MST CAR → IPFS pinning service.
 * Stage 4 of ADR-2605171800. Status: scaffold v0.0.0, stubs.
 */

import { pinata } from "./providers/pinata.js";
import { web3storage } from "./providers/web3storage.js";
import { filecoin } from "./providers/filecoin.js";
import { kubo } from "./providers/kubo.js";
import { emitPinRecord } from "./emit.js";

const CONFIG = {
  providers: (process.env.ETZ_PINNER_PROVIDERS ?? "pinata,filecoin")
    .split(",")
    .map((s) => s.trim()),
  dataDir: process.env.ETZ_PINNER_DATA_DIR ?? "/data/mst-projector",
  did: process.env.ETZ_PINNER_DID ?? "did:web:pinner.etzhayyim.com",
};

const REGISTRY: Record<
  string,
  (carPath: string) => Promise<{ cid: string; receipt: unknown }>
> = {
  pinata,
  web3storage,
  filecoin,
  kubo,
};

async function pinOne(carPath: string): Promise<void> {
  const results: Array<{ provider: string; cid: string; receipt: unknown }> = [];
  for (const name of CONFIG.providers) {
    const fn = REGISTRY[name];
    if (!fn) throw new Error(`unknown provider: ${name}`);
    const { cid, receipt } = await fn(carPath);
    results.push({ provider: name, cid, receipt });
    console.log(`[ipfs-pinner] ${name} pinned ${carPath} → ${cid}`);
  }
  if (results.length < 2) {
    throw new Error("[ipfs-pinner] replication factor < 2; refusing to record");
  }
  // All providers should return the same CID for the same CAR
  const cids = new Set(results.map((r) => r.cid));
  if (cids.size > 1) {
    throw new Error(`[ipfs-pinner] CID mismatch across providers: ${[...cids].join(", ")}`);
  }
  await emitPinRecord({
    did: CONFIG.did,
    carPath,
    cid: results[0].cid,
    providers: results.map((r) => r.provider),
    pinnedAt: new Date().toISOString(),
  });
}

async function main() {
  console.log("[ipfs-pinner] starting", { config: CONFIG });
  throw new Error(
    "[ipfs-pinner] main loop TODO: subscribe to ai.gftd.apps.substrate.mstRoot " +
      "firehose, for each new emit read carPath from shared dataDir, call pinOne()."
  );
  // unreachable
  await pinOne("/data/mst-projector/example.car");
}

main().catch((err) => {
  console.error("[ipfs-pinner] fatal:", err);
  process.exit(2);
});
