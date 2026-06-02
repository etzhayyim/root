/**
 * Substrate-mode anchor commit.
 *
 * Writes `com.etzhayyim.substrate.l2Anchor` records under the
 * anchorer's DID after a successful (or alreadyAnchored=true)
 * EtzhayyimAnchor.anchor() call. Mirror of `sidecarClient.anchorCommit`
 * for the firehose-driven substrate pipeline.
 *
 * Per ADR-2605171800 Stage 5b.
 */

import type {AtpAgent} from "@atproto/api";

import type {SubmitResult} from "./submit.js";

const COLLECTION = "com.etzhayyim.substrate.l2Anchor";

export interface L2AnchorRecordInput {
  shardKey: string;
  rootCid: string;
  rootHash: `0x${string}`;
  submit: SubmitResult;
  chainId: number;
  contract: `0x${string}`;
  anchorer: `0x${string}`;
  batchSize: number;
  ipfsPinUri?: string;
  anchoredAt?: string;
}

/**
 * Pure helper — encode the lexicon contract. Exposed so unit tests can
 * assert the payload shape without booting an AtpAgent or a real PDS.
 */
export function buildL2AnchorRecord(
  input: L2AnchorRecordInput,
): Record<string, unknown> {
  const body: Record<string, unknown> = {
    $type: COLLECTION,
    shardKey: input.shardKey,
    rootCid: input.rootCid,
    rootHash: input.rootHash,
    txHash: input.submit.txHash,
    blockNumber: input.submit.blockNumber,
    logIndex: input.submit.logIndex,
    chainId: input.chainId,
    contract: input.contract,
    anchorer: input.anchorer,
    batchSize: input.batchSize,
    alreadyAnchored: input.submit.alreadyAnchored,
    anchoredAt: input.anchoredAt ?? new Date().toISOString(),
  };
  if (input.ipfsPinUri) body.ipfsPinUri = input.ipfsPinUri;
  return body;
}

export interface CommitToPdsOpts extends L2AnchorRecordInput {
  agent: AtpAgent;
  /** Repo the AtpAgent is authenticated as (the anchorer's DID). */
  repo: string;
}

export async function commitL2Anchor(
  opts: CommitToPdsOpts,
): Promise<{uri: string; cid: string}> {
  const record = buildL2AnchorRecord(opts);
  const res = await opts.agent.com.atproto.repo.createRecord({
    repo: opts.repo,
    collection: COLLECTION,
    record,
  });
  if (!res.success) {
    throw new Error(
      `[anchor-cron/commitToPds] createRecord failed: ${JSON.stringify(res)}`,
    );
  }
  return {uri: res.data.uri, cid: res.data.cid as string};
}
