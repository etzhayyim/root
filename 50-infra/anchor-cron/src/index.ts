/**
 * anchor-cron — pending MST roots → EtzhayyimAnchor on Base L2.
 *
 * Stage 5b of ADR-2605171800. Status: scaffold v0.0.0, stubs.
 *
 * Run as a K8s CronJob (every 60s) OR continuously (with internal sleep).
 */

import { readPending } from "./pending.js";
import { submitAnchor } from "./submit.js";
import { emitAnchoredReceipt } from "./emit.js";

const CONFIG = {
  contract: process.env.ETZ_ANCHOR_CONTRACT as `0x${string}` | undefined,
  rpcUrl: process.env.ETZ_ANCHOR_RPC_URL ?? "https://mainnet.base.org",
  did: process.env.ETZ_ANCHOR_DID ?? "did:web:anchor.etzhayyim.com",
  signerKey: process.env.ETZ_ANCHOR_SIGNER_KEY,
  confirmations: Number(process.env.ETZ_ANCHOR_CONFIRMATIONS ?? 3),
  batchMax: Number(process.env.ETZ_ANCHOR_BATCH_MAX ?? 10),
};

async function tick() {
  if (!CONFIG.contract) throw new Error("ETZ_ANCHOR_CONTRACT not set");
  if (!CONFIG.signerKey) throw new Error("ETZ_ANCHOR_SIGNER_KEY not set");

  const pending = await readPending({ limit: CONFIG.batchMax });
  if (pending.length === 0) {
    console.log("[anchor-cron] no pending roots, skipping");
    return;
  }
  console.log(`[anchor-cron] ${pending.length} pending roots`);

  for (const p of pending) {
    const tx = await submitAnchor({
      contract: CONFIG.contract,
      rpcUrl: CONFIG.rpcUrl,
      signerKey: CONFIG.signerKey,
      confirmations: CONFIG.confirmations,
      rootHash: p.rootHash,
      ipfsCid: p.ipfsCid,
      batchSize: p.batchSize,
    });
    await emitAnchoredReceipt({
      did: CONFIG.did,
      mstRootUri: p.mstRootUri,
      txHash: tx.txHash,
      blockNumber: tx.blockNumber,
    });
    console.log(`[anchor-cron] anchored ${p.rootHash} tx=${tx.txHash} block=${tx.blockNumber}`);
  }
}

tick().catch((err) => {
  console.error("[anchor-cron] fatal:", err);
  process.exit(2);
});
