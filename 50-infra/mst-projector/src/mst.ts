/**
 * Per-shard state + counter-derived root (Phase 1).
 *
 * Phase 1 keeps an ordered list of (rkey, recordCid, op, seq, did, tsMs) per
 * shard and derives a deterministic sha-256 root from the canonical-JSON
 * serialization of that list. This unblocks downstream snapshot emission
 * before fully porting @atproto/repo's MST.
 *
 * Phase 2 replaces this with a true MST root CID (CID v1, dag-cbor), at
 * which point the downstream lexicon switches the field name from
 * `snapshotHash` to `rootCid`.
 */

import { createHash } from "node:crypto";
import type { FirehoseEvent } from "./firehose.js";

export interface ShardRecord {
  rkey: string;
  recordCid?: string;
  op: "create" | "update" | "delete";
  seq: string; // bigint serialised — JSON-safe
  did: string;
  tsMs: number;
}

interface ShardState {
  records: ShardRecord[];
  firstSeq?: string;
  lastSeq?: string;
}

const shards = new Map<string, ShardState>();

export function applyCommit(shardKey: string, ev: FirehoseEvent): void {
  const s = shards.get(shardKey) ?? { records: [] };
  const rec: ShardRecord = {
    rkey: ev.rkey,
    recordCid: ev.recordCid,
    op: ev.op,
    seq: ev.seq.toString(),
    did: ev.did,
    tsMs: Date.now(),
  };
  s.records.push(rec);
  s.firstSeq ??= rec.seq;
  s.lastSeq = rec.seq;
  shards.set(shardKey, s);
}

export function shardSnapshot(shardKey: string): {
  records: ShardRecord[];
  firstSeq?: string;
  lastSeq?: string;
} {
  const s = shards.get(shardKey);
  return s ? { ...s, records: [...s.records] } : { records: [] };
}

export function recordCount(shardKey: string): number {
  return shards.get(shardKey)?.records.length ?? 0;
}

export function currentRoot(shardKey: string): string {
  const snap = shardSnapshot(shardKey);
  const canonical = JSON.stringify(snap.records);
  return "sha256-" + createHash("sha256").update(canonical).digest("hex");
}

export function resetShard(shardKey: string): void {
  shards.delete(shardKey);
}

export function listShards(): string[] {
  return [...shards.keys()];
}
