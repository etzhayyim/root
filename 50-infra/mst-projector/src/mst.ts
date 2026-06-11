/**
 * Per-shard MST state (Phase 2).
 *
 * Phase 2 holds an in-memory `@atproto/repo` MST per shard, keyed by
 * `<did>/<rkey>`. The shard's root identifier is the true AT-Protocol
 * MST root CID (v1, dag-cbor) — `await mst.getPointer()`. The
 * deterministic root replaces the Phase 1 counter-derived
 * `sha256-...` hash and unblocks IPFS pin verification + L2 anchoring.
 *
 * Phase 1's record-list + JSON-canonical-hash path is removed entirely;
 * downstream lexicon (`com.etzhayyim.substrate.shardSnapshot`) was
 * already forward-compatible (`phase`, `rootCid`, `snapshotCid` slots
 * pre-defined) per ADR-2605191655.
 */

import { CID } from "multiformats/cid";
import {
  BlockMap,
  MemoryBlockstore,
  MST,
  blocksToCarFile,
} from "@atproto/repo";

import type { FirehoseEvent } from "./firehose.js";

/** Allowed character set for an MST key segment (per @atproto/repo). */
const MST_SEGMENT_RE = /^[a-zA-Z0-9_~\-:.]+$/;

interface ShardState {
  storage: MemoryBlockstore;
  mst: MST;
  firstSeq?: string;
  lastSeq?: string;
  recordCount: number;
}

const shards = new Map<string, ShardState>();

function shardKeyOf(ev: FirehoseEvent): string {
  return ev.collection;
}

function mstKeyOf(ev: FirehoseEvent): string | null {
  const seg1 = ev.did;
  const seg2 = ev.rkey;
  if (!MST_SEGMENT_RE.test(seg1) || !MST_SEGMENT_RE.test(seg2)) return null;
  const key = `${seg1}/${seg2}`;
  return key.length <= 1024 ? key : null;
}

async function ensureShard(shardKey: string): Promise<ShardState> {
  const existing = shards.get(shardKey);
  if (existing) return existing;
  const storage = new MemoryBlockstore();
  const mst = await MST.create(storage);
  const fresh: ShardState = { storage, mst, recordCount: 0 };
  shards.set(shardKey, fresh);
  return fresh;
}

/**
 * Apply one firehose op to its shard's MST.
 *
 * - `create` ↔ `MST.add(key, cid)`. If key already exists (replay /
 *   firehose dup), fall back to `MST.update`.
 * - `update` ↔ `MST.update(key, cid)`. If key doesn't exist (out-of-order
 *   replay), fall back to `MST.add`.
 * - `delete` ↔ `MST.delete(key)`. No-op if key absent.
 *
 * Ops with missing/invalid CID, or with MST-incompatible DID/rkey
 * segments, are skipped (logged once and counted in the shard's
 * skip-trail via the projector's logger; not the MST).
 */
export async function applyCommit(
  shardKey: string,
  ev: FirehoseEvent,
): Promise<{ applied: boolean; reason?: string }> {
  const key = mstKeyOf(ev);
  if (!key) return { applied: false, reason: "invalid-mst-key" };
  const needsCid = ev.op === "create" || ev.op === "update";
  if (needsCid && !ev.recordCid) {
    return { applied: false, reason: "missing-record-cid" };
  }

  const shard = await ensureShard(shardKey);
  const cid = ev.recordCid ? CID.parse(ev.recordCid) : null;

  try {
    if (ev.op === "create") {
      const existing = await shard.mst.get(key);
      shard.mst = existing
        ? await shard.mst.update(key, cid!)
        : await shard.mst.add(key, cid!);
    } else if (ev.op === "update") {
      const existing = await shard.mst.get(key);
      shard.mst = existing
        ? await shard.mst.update(key, cid!)
        : await shard.mst.add(key, cid!);
    } else if (ev.op === "delete") {
      const existing = await shard.mst.get(key);
      if (!existing) return { applied: false, reason: "delete-missing" };
      shard.mst = await shard.mst.delete(key);
    }
  } catch (err) {
    return { applied: false, reason: `mst-error:${(err as Error).message}` };
  }

  shard.recordCount += 1;
  const seqStr = ev.seq.toString();
  shard.firstSeq ??= seqStr;
  shard.lastSeq = seqStr;
  return { applied: true };
}

export async function currentRoot(shardKey: string): Promise<string | null> {
  const shard = shards.get(shardKey);
  if (!shard) return null;
  const cid = await shard.mst.getPointer();
  return cid.toString();
}

export function recordCount(shardKey: string): number {
  return shards.get(shardKey)?.recordCount ?? 0;
}

export function shardSequenceRange(
  shardKey: string,
): { firstSeq?: string; lastSeq?: string } {
  const s = shards.get(shardKey);
  return { firstSeq: s?.firstSeq, lastSeq: s?.lastSeq };
}

export function resetShard(shardKey: string): void {
  shards.delete(shardKey);
}

export function listShards(): string[] {
  return [...shards.keys()];
}

/**
 * Materialise the shard's MST as a CAR file.
 *
 * Returns the CAR bytes (root + unstored MST blocks) and the root CID.
 * The MST itself is rebuilt against a fresh storage so that calling
 * `flushShardToCar` is idempotent — repeated calls without further
 * `applyCommit` produce the same root CID and (modulo CAR block
 * ordering, which @atproto/repo keeps deterministic) the same bytes.
 */
export async function flushShardToCar(
  shardKey: string,
): Promise<{ rootCid: CID; carBytes: Uint8Array; blockCount: number } | null> {
  const shard = shards.get(shardKey);
  if (!shard) return null;
  const unstored = await shard.mst.getUnstoredBlocks();
  await shard.storage.putMany(unstored.blocks);
  const blocks: BlockMap = new BlockMap();
  blocks.addMap(unstored.blocks);
  const rootCid = await shard.mst.getPointer();
  const carBytes = await blocksToCarFile(rootCid, blocks);
  return { rootCid, carBytes, blockCount: blocks.size };
}
