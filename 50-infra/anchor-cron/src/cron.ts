/**
 * anchor-cron tick orchestration.
 *
 * Extracted from `index.ts` so unit tests can exercise the loop with
 * mocked sidecarClient / submit / solvency / logger. `index.ts` is the
 * thin CLI entrypoint that wires up the real implementations.
 */
import type {PendingRoot} from "./pending.js";
import type {CommitEntry} from "./sidecarClient.js";
import type {SubmitResult} from "./submit.js";
import type {SolvencyStatus} from "./solvency.js";

export interface CronConfig {
  contract: `0x${string}`;
  rpcUrl: string;
  signerKey: `0x${string}`;
  sidecarSocket: string;
  cellDids: string[];
  confirmations: number;
  batchMax: number;
  /**
   * When > 0, anchor-cron reads the signer's balance each tick and
   * emits a single-line stderr warning if it falls below this floor.
   * 0 disables solvency monitoring (suitable for local-anvil smoke).
   */
  warnBalanceWei: bigint;
}

/**
 * Externally-injectable side-effects. Defaults are wired up by
 * `index.ts`; tests replace them with vi.fn() spies.
 */
export interface CronDeps {
  health: (socketPath: string) => Promise<void>;
  readPending: (opts: {
    socketPath: string;
    cellDid: string;
    limit: number;
  }) => Promise<PendingRoot[]>;
  submitAnchor: (opts: {
    contract: `0x${string}`;
    rpcUrl: string;
    signerKey: `0x${string}`;
    confirmations: number;
    pending: PendingRoot;
  }) => Promise<SubmitResult>;
  anchorCommit: (
    socketPath: string,
    cellDid: string,
    commits: CommitEntry[],
  ) => Promise<void>;
  checkSolvency: (opts: {
    rpcUrl: string;
    signerKey: `0x${string}`;
    warnBelowWei: bigint;
  }) => Promise<SolvencyStatus>;
  emitSolvencyWarning: (status: SolvencyStatus) => void;
  log: (msg: string) => void;
}

export interface TickResult {
  freshAnchors: number;
  alreadyOnChain: number;
  solvency: SolvencyStatus | null;
}

export async function runTick(
  cfg: CronConfig,
  deps: CronDeps,
): Promise<TickResult> {
  if (cfg.cellDids.length === 0) {
    throw new Error("anchor-cron: cellDids list is empty");
  }
  await deps.health(cfg.sidecarSocket);
  deps.log(
    `[anchor-cron] sidecar=${cfg.sidecarSocket} contract=${cfg.contract} cells=${cfg.cellDids.length}`,
  );

  // Solvency check is best-effort: a failed RPC call surfaces as a
  // warning but does not abort anchoring (anchoring will fail on its
  // own RPC call with a clearer error).
  let solvency: SolvencyStatus | null = null;
  if (cfg.warnBalanceWei > 0n) {
    try {
      solvency = await deps.checkSolvency({
        rpcUrl: cfg.rpcUrl,
        signerKey: cfg.signerKey,
        warnBelowWei: cfg.warnBalanceWei,
      });
      deps.emitSolvencyWarning(solvency);
    } catch (cause) {
      deps.log(
        `[anchor-cron] solvency: check failed (continuing): ${
          (cause as Error).message ?? cause
        }`,
      );
    }
  }

  let freshAnchors = 0;
  let alreadyOnChain = 0;

  for (const cellDid of cfg.cellDids) {
    const pending = await deps.readPending({
      socketPath: cfg.sidecarSocket,
      cellDid,
      limit: cfg.batchMax,
    });
    if (pending.length === 0) {
      deps.log(`[anchor-cron] ${cellDid}: nothing pending`);
      continue;
    }
    deps.log(
      `[anchor-cron] ${cellDid}: ${pending.length} pending root(s) to anchor`,
    );

    const commits: CommitEntry[] = [];
    for (const p of pending) {
      const res = await deps.submitAnchor({
        contract: cfg.contract,
        rpcUrl: cfg.rpcUrl,
        signerKey: cfg.signerKey,
        confirmations: cfg.confirmations,
        pending: p,
      });
      if (res.alreadyAnchored) alreadyOnChain++;
      else freshAnchors++;
      commits.push({
        thread_id: p.row.thread_id,
        checkpoint_ns: p.row.checkpoint_ns,
        checkpoint_id: p.row.checkpoint_id,
        anchor_tx_hash: res.txHash,
        anchor_block_number: res.blockNumber,
        anchor_log_index: res.logIndex,
      });
      deps.log(
        `[anchor-cron]   ${p.row.checkpoint_id} rootHash=${p.rootHash} ` +
          `${
            res.alreadyAnchored
              ? "(already on-chain)"
              : `tx=${res.txHash}`
          } block=${res.blockNumber}`,
      );
    }
    await deps.anchorCommit(cfg.sidecarSocket, cellDid, commits);
    deps.log(
      `[anchor-cron] ${cellDid}: committed ${commits.length} anchor row(s) back to sidecar`,
    );
  }

  deps.log(
    `[anchor-cron] done. fresh anchors=${freshAnchors} already-on-chain=${alreadyOnChain}`,
  );

  return {freshAnchors, alreadyOnChain, solvency};
}
