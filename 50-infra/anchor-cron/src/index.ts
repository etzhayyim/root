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
 *   ETZ_ANCHOR_CONTRACT     0x... EtzhayyimAnchor address on the target chain
 *   ETZ_ANCHOR_RPC_URL      JSON-RPC endpoint (default: https://mainnet.base.org)
 *   ETZ_ANCHOR_SIGNER_KEY   0x... 32-byte hex private key. Funded with enough
 *                           native gas to anchor `ETZ_ANCHOR_BATCH_MAX` roots.
 *   ETZ_ANCHOR_SOCKET       Unix socket of the checkpointer sidecar
 *                           (default: /run/etzhayyim/checkpointer.sock)
 *   ETZ_ANCHOR_CELL_DIDS    CSV of cell DIDs to walk.
 *   ETZ_ANCHOR_CONFIRMATIONS                default 3
 *   ETZ_ANCHOR_BATCH_MAX                    default 10
 *   ETZ_ANCHOR_WARN_BALANCE_WEI             solvency floor (wei). 0 = off.
 */

import process from "node:process";

import {runTick, type CronConfig} from "./cron.js";
import {readPending} from "./pending.js";
import {submitAnchor} from "./submit.js";
import {anchorCommit, health} from "./sidecarClient.js";
import {checkSolvency, emitSolvencyWarning} from "./solvency.js";

function envOrThrow(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`anchor-cron: ${name} is required`);
  return v;
}

function envBigIntOrZero(name: string): bigint {
  const raw = process.env[name];
  if (!raw) return 0n;
  try {
    return BigInt(raw);
  } catch {
    throw new Error(`anchor-cron: ${name} must be a base-10 integer (wei)`);
  }
}

const CONFIG: CronConfig = {
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
  warnBalanceWei: envBigIntOrZero("ETZ_ANCHOR_WARN_BALANCE_WEI"),
};

runTick(CONFIG, {
  health,
  readPending,
  submitAnchor,
  anchorCommit,
  checkSolvency,
  emitSolvencyWarning,
  log: (msg) => console.log(msg),
}).catch((cause) => {
  console.error("[anchor-cron] fatal:", cause);
  process.exit(2);
});
