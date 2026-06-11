/**
 * Substrate-mode pending-roots discovery.
 *
 * Lists `com.etzhayyim.substrate.ipfsPin` records from a PDS and
 * filters down to those that do NOT yet have a matching
 * `com.etzhayyim.substrate.l2Anchor` record under the anchorer's DID.
 * Returns `PendingRoot`s shaped for `submit.ts` so we can reuse the
 * existing viem submission path.
 *
 * Per ADR-2605171800 Stage 5b — substrate mode. This is the firehose
 * sibling of `pending.ts` (sidecar mode).
 */

import {sha256} from "@noble/hashes/sha256";
import {bytesToHex} from "@noble/hashes/utils";
import {AtpAgent} from "@atproto/api";

import type {PendingRoot} from "./pending.js";
import type {SaverIndexRow} from "./sidecarClient.js";

const COLL_IPFS_PIN = "com.etzhayyim.substrate.ipfsPin";
const COLL_L2_ANCHOR = "com.etzhayyim.substrate.l2Anchor";

export interface IpfsPinRecord {
  uri: string;
  shardKey: string;
  rootCid: string;
  carCid: string;
  byteSize?: number;
  blockCount?: number;
  pinnedAt?: string;
}

export interface ReadPendingFromPdsOpts {
  agent: AtpAgent;
  /** Repo (DID) hosting the ipfsPin records (the ipfs-pinner DID). */
  pinnerRepo: string;
  /** Repo (DID) under which this anchor-cron writes l2Anchor records.
   *  Used to discover which roots are already anchored. */
  anchorerRepo: string;
  /** Max number of ipfsPin records to scan per tick. */
  limit: number;
}

/** Pure converter: ipfsPin record → PendingRoot. */
export function ipfsPinToPendingRoot(rec: IpfsPinRecord): {
  pending: PendingRoot;
  shardKey: string;
  ipfsPinUri: string;
} {
  const ipfsCidBytes = new TextEncoder().encode(rec.rootCid);
  const rootHash = ("0x" + bytesToHex(sha256(ipfsCidBytes))) as `0x${string}`;
  const row: SaverIndexRow = {
    cell_did: rec.shardKey,            // substrate mode: shardKey replaces cell_did
    thread_id: rec.rootCid,            // unique-per-anchor identifier
    checkpoint_ns: "",
    checkpoint_id: rec.rootCid,
    mst_root_cid: rec.rootCid,
    car_size_bytes: rec.byteSize ?? 0,
    car_blob_count: rec.blockCount ?? 0,
    mst_projected_at: rec.pinnedAt ? Date.parse(rec.pinnedAt) : 0,
    ipfs_pinned_at: rec.pinnedAt ? Date.parse(rec.pinnedAt) : 0,
    ipfs_pin_service: "ipfs-pinner",
    ipfs_pin_id: rec.carCid,
    anchor_tx_hash: null,
    anchor_block_number: null,
    anchor_log_index: null,
    anchor_chain_id: 0,
    anchored_at: null,
  };
  // batchSize on-chain is informational; mirror Phase 1 convention of
  // (block count + 1) so the value is meaningful for downstream observers.
  // When blockCount is unknown we use 1 — anchor() accepts any uint64.
  const batchSize = (rec.blockCount ?? 0) + 1;
  return {
    pending: {
      row,
      rootHash,
      ipfsCidBytes,
      batchSize,
    },
    shardKey: rec.shardKey,
    ipfsPinUri: rec.uri,
  };
}

async function listAllRecords<R>(
  agent: AtpAgent,
  collection: string,
  repo: string,
  hardLimit: number,
): Promise<Array<{uri: string; value: R}>> {
  const out: Array<{uri: string; value: R}> = [];
  let cursor: string | undefined;
  while (out.length < hardLimit) {
    const res = await agent.com.atproto.repo.listRecords({
      repo,
      collection,
      limit: Math.min(100, hardLimit - out.length),
      cursor,
    });
    for (const rec of res.data.records) {
      out.push({uri: rec.uri, value: rec.value as R});
    }
    if (!res.data.cursor) break;
    cursor = res.data.cursor;
  }
  return out;
}

interface IpfsPinValue {
  shardKey?: string;
  rootCid?: string;
  carCid?: string;
  byteSize?: number;
  blockCount?: number;
  pinnedAt?: string;
}

interface L2AnchorValue {
  rootCid?: string;
}

export async function readPendingFromPds(
  opts: ReadPendingFromPdsOpts,
): Promise<
  Array<{pending: PendingRoot; shardKey: string; ipfsPinUri: string}>
> {
  const [pinRows, anchorRows] = await Promise.all([
    listAllRecords<IpfsPinValue>(
      opts.agent,
      COLL_IPFS_PIN,
      opts.pinnerRepo,
      opts.limit * 4,        // overscan to absorb already-anchored gaps
    ),
    listAllRecords<L2AnchorValue>(
      opts.agent,
      COLL_L2_ANCHOR,
      opts.anchorerRepo,
      opts.limit * 4,
    ),
  ]);

  const anchored = new Set<string>();
  for (const a of anchorRows) {
    if (a.value.rootCid) anchored.add(a.value.rootCid);
  }

  const pending: Array<{
    pending: PendingRoot;
    shardKey: string;
    ipfsPinUri: string;
  }> = [];
  for (const row of pinRows) {
    const v = row.value;
    if (!v.shardKey || !v.rootCid || !v.carCid) continue;
    if (anchored.has(v.rootCid)) continue;
    pending.push(
      ipfsPinToPendingRoot({
        uri: row.uri,
        shardKey: v.shardKey,
        rootCid: v.rootCid,
        carCid: v.carCid,
        byteSize: v.byteSize,
        blockCount: v.blockCount,
        pinnedAt: v.pinnedAt,
      }),
    );
    if (pending.length >= opts.limit) break;
  }
  return pending;
}
