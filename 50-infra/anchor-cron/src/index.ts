/**
 * anchor-cron — pending MST roots → EtzhayyimAnchor on Base L2.
 *
 * Stage 5b of ADR-2605171800.
 *
 * Runs as a K8s CronJob (every N minutes) OR as a one-shot ticked by
 * the user. Reads pending rows directly from the checkpointer sidecar
 * over its Unix socket; writes anchor receipts back the same way.
 *
 * Required env:
 *   ETZ_ANCHOR_CONTRACT   0x... EtzhayyimAnchor address on the target chain
 *   ETZ_ANCHOR_RPC_URL    JSON-RPC endpoint (default: https://mainnet.base.org)
 *   ETZ_ANCHOR_SIGNER_KEY 0x... 32-byte hex private key. Funded with enough
 *                         native gas to anchor `ETZ_ANCHOR_BATCH_MAX` roots.
 *   ETZ_ANCHOR_SOCKET     Unix socket of the checkpointer sidecar
 *                         (default: /run/etzhayyim/checkpointer.sock)
 *   ETZ_ANCHOR_CELL_DIDS  CSV of cell DIDs to walk. Defaults to the
 *                         single-DID case below.
 *   ETZ_ANCHOR_CONFIRMATIONS  default 3
 *   ETZ_ANCHOR_BATCH_MAX  default 10
 */

import process from "node:process";

import {readPending} from "./pending.js";
import {submitAnchor} from "./submit.js";
import {anchorCommit, health, type CommitEntry} from "./sidecarClient.js";

function envOrThrow(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`anchor-cron: ${name} is required`);
  return v;
}

const CONFIG = {
  contract: envOrThrow("ETZ_ANCHOR_CONTRACT") as `0x${string}`,
  rpcUrl: process.env.ETZ_ANCHOR_RPC_URL ?? "https://mainnet.base.org",
  signerKey: envOrThrow("ETZ_ANCHOR_SIGNER_KEY") as `0x${string}`,
  sidecarSocket:
    process.env.ETZ_ANCHOR_SOCKET ?? "/run/etzhayyim/checkpointer.sock",
  cellDids: (process.env.ETZ_ANCHOR_CELL_DIDS ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
  confirmations: Number(process.env.ETZ_ANCHOR_CONFIRMATIONS ?? 3),
  batchMax: Number(process.env.ETZ_ANCHOR_BATCH_MAX ?? 10),
};

async function tick(): Promise<void> {
  if (CONFIG.cellDids.length === 0) {
    throw new Error("anchor-cron: ETZ_ANCHOR_CELL_DIDS lists no DIDs");
  }
  await health(CONFIG.sidecarSocket);
  console.log(
    `[anchor-cron] sidecar=${CONFIG.sidecarSocket} contract=${CONFIG.contract} cells=${CONFIG.cellDids.length}`
  );

  let totalAnchored = 0;
  let totalAlreadyOnChain = 0;

  for (const cellDid of CONFIG.cellDids) {
    const pending = await readPending({
      socketPath: CONFIG.sidecarSocket,
      cellDid,
      limit: CONFIG.batchMax,
    });
    if (pending.length === 0) {
      console.log(`[anchor-cron] ${cellDid}: nothing pending`);
      continue;
    }
    console.log(
      `[anchor-cron] ${cellDid}: ${pending.length} pending root(s) to anchor`
    );

    const commits: CommitEntry[] = [];
    for (const p of pending) {
      const res = await submitAnchor({
        contract: CONFIG.contract,
        rpcUrl: CONFIG.rpcUrl,
        signerKey: CONFIG.signerKey,
        confirmations: CONFIG.confirmations,
        pending: p,
      });
      if (res.alreadyAnchored) totalAlreadyOnChain++;
      else totalAnchored++;
      commits.push({
        thread_id: p.row.thread_id,
        checkpoint_ns: p.row.checkpoint_ns,
        checkpoint_id: p.row.checkpoint_id,
        anchor_tx_hash: res.txHash,
        anchor_block_number: res.blockNumber,
        anchor_log_index: res.logIndex,
      });
      console.log(
        `[anchor-cron]   ${p.row.checkpoint_id} rootHash=${p.rootHash} ` +
          `${res.alreadyAnchored ? "(already on-chain)" : `tx=${res.txHash}`} ` +
          `block=${res.blockNumber}`
      );
    }
    await anchorCommit(CONFIG.sidecarSocket, cellDid, commits);
    console.log(
      `[anchor-cron] ${cellDid}: committed ${commits.length} anchor row(s) back to sidecar`
    );
  }

  console.log(
    `[anchor-cron] done. fresh anchors=${totalAnchored} already-on-chain=${totalAlreadyOnChain}`
  );
}

tick().catch((cause) => {
  console.error("[anchor-cron] fatal:", cause);
  process.exit(2);
});
