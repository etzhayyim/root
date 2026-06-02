/**
 * Substrate-mode tick orchestration.
 *
 * Parallels `cron.ts` (sidecar mode) but reads pending roots from a PDS
 * (`com.etzhayyim.substrate.ipfsPin` records) and writes anchor receipts
 * back as `com.etzhayyim.substrate.l2Anchor` records. The contract-call
 * path (submit.ts) and the solvency monitor (solvency.ts) are reused
 * unchanged.
 *
 * Per ADR-2605171800 Stage 5b.
 */

import type {PendingRoot} from "./pending.js";
import type {SubmitResult} from "./submit.js";
import type {SolvencyStatus} from "./solvency.js";

export interface SubstrateCronConfig {
  contract: `0x${string}`;
  rpcUrl: string;
  signerKey: `0x${string}`;
  chainId: number;
  /** PDS service the anchorer authenticates against. */
  pdsUrl: string;
  /** Repo (DID) hosting the ipfsPin records. */
  pinnerRepo: string;
  /** Repo (DID) under which this cron writes l2Anchor records. */
  anchorerRepo: string;
  confirmations: number;
  batchMax: number;
  warnBalanceWei: bigint;
}

export interface SubstratePending {
  pending: PendingRoot;
  shardKey: string;
  ipfsPinUri: string;
}

export interface SubstrateCronDeps {
  readPending: (opts: {
    limit: number;
  }) => Promise<SubstratePending[]>;
  submitAnchor: (opts: {
    contract: `0x${string}`;
    rpcUrl: string;
    signerKey: `0x${string}`;
    confirmations: number;
    pending: PendingRoot;
  }) => Promise<SubmitResult>;
  commitL2Anchor: (input: {
    shardKey: string;
    rootCid: string;
    rootHash: `0x${string}`;
    submit: SubmitResult;
    chainId: number;
    contract: `0x${string}`;
    anchorer: `0x${string}`;
    batchSize: number;
    ipfsPinUri: string;
  }) => Promise<{uri: string; cid: string}>;
  resolveAnchorerAddress: () => Promise<`0x${string}`>;
  checkSolvency: (opts: {
    rpcUrl: string;
    signerKey: `0x${string}`;
    warnBelowWei: bigint;
  }) => Promise<SolvencyStatus>;
  emitSolvencyWarning: (status: SolvencyStatus) => void;
  log: (msg: string) => void;
}

export interface SubstrateTickResult {
  freshAnchors: number;
  alreadyOnChain: number;
  emittedReceipts: number;
  solvency: SolvencyStatus | null;
}

export async function runTickSubstrate(
  cfg: SubstrateCronConfig,
  deps: SubstrateCronDeps,
): Promise<SubstrateTickResult> {
  deps.log(
    `[anchor-cron substrate] pds=${cfg.pdsUrl} pinner=${cfg.pinnerRepo} anchorer=${cfg.anchorerRepo} contract=${cfg.contract} chain=${cfg.chainId}`,
  );

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
        `[anchor-cron substrate] solvency: check failed (continuing): ${
          (cause as Error).message ?? cause
        }`,
      );
    }
  }

  const pending = await deps.readPending({limit: cfg.batchMax});
  if (pending.length === 0) {
    deps.log(`[anchor-cron substrate] nothing pending`);
    return {freshAnchors: 0, alreadyOnChain: 0, emittedReceipts: 0, solvency};
  }
  deps.log(
    `[anchor-cron substrate] ${pending.length} pending root(s) to anchor`,
  );

  const anchorer = await deps.resolveAnchorerAddress();

  let freshAnchors = 0;
  let alreadyOnChain = 0;
  let emittedReceipts = 0;

  for (const p of pending) {
    const res = await deps.submitAnchor({
      contract: cfg.contract,
      rpcUrl: cfg.rpcUrl,
      signerKey: cfg.signerKey,
      confirmations: cfg.confirmations,
      pending: p.pending,
    });
    if (res.alreadyAnchored) alreadyOnChain++;
    else freshAnchors++;
    const receipt = await deps.commitL2Anchor({
      shardKey: p.shardKey,
      rootCid: p.pending.row.mst_root_cid,
      rootHash: p.pending.rootHash,
      submit: res,
      chainId: cfg.chainId,
      contract: cfg.contract,
      anchorer,
      batchSize: p.pending.batchSize,
      ipfsPinUri: p.ipfsPinUri,
    });
    emittedReceipts++;
    deps.log(
      `[anchor-cron substrate]   ${p.shardKey}/${p.pending.row.mst_root_cid} ` +
        `${res.alreadyAnchored ? "(already on-chain)" : `tx=${res.txHash}`} ` +
        `block=${res.blockNumber} → ${receipt.uri}`,
    );
  }

  deps.log(
    `[anchor-cron substrate] done. fresh=${freshAnchors} already=${alreadyOnChain} receipts=${emittedReceipts}`,
  );
  return {freshAnchors, alreadyOnChain, emittedReceipts, solvency};
}
