/**
 * Shard partitioning + flush policy + manifest serializer (Phase 1).
 *
 * Default = one shard per collection NSID. Flush when records-since-flush ≥ N
 * OR wall-clock since-last-flush ≥ T.
 *
 * Phase 1 serializes the shard as a JSON manifest:
 *   { shardKey, firstSeq, lastSeq, recordCount, snapshotHash, records[] }
 * written to `<dataDir>/<shardKey>/<snapshotHash>.json`.
 *
 * Phase 2 replaces this with a CAR file containing the true MST root +
 * leaf blocks, identified by a CID v1 (dag-cbor).
 */

import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import {
  currentRoot,
  recordCount,
  resetShard,
  shardSnapshot,
} from "./mst.js";

export type ShardKey = string;

interface ShardCounter {
  lastFlushTsMs: number;
  recordsSinceFlush: number;
}

const counters = new Map<ShardKey, ShardCounter>();

export function notePending(shardKey: ShardKey): void {
  const now = Date.now();
  const c = counters.get(shardKey) ?? {
    lastFlushTsMs: now,
    recordsSinceFlush: 0,
  };
  c.recordsSinceFlush += 1;
  counters.set(shardKey, c);
}

export function shouldFlush(
  shardKey: ShardKey,
  recordsThreshold: number,
  secondsThreshold: number
): boolean {
  const c = counters.get(shardKey);
  if (!c) return false;
  if (recordCount(shardKey) === 0) return false;
  if (c.recordsSinceFlush >= recordsThreshold) return true;
  const ageSec = (Date.now() - c.lastFlushTsMs) / 1000;
  if (ageSec >= secondsThreshold && c.recordsSinceFlush > 0) return true;
  return false;
}

export interface FlushResult {
  manifestPath: string;
  snapshotHash: string;
  recordCount: number;
  byteSize: number;
}

export async function flushShard(
  shardKey: ShardKey,
  dataDir: string
): Promise<FlushResult> {
  const snap = shardSnapshot(shardKey);
  const snapshotHash = currentRoot(shardKey);
  const manifest = {
    version: 1,
    shardKey,
    firstSeq: snap.firstSeq,
    lastSeq: snap.lastSeq,
    recordCount: snap.records.length,
    snapshotHash,
    flushedAt: new Date().toISOString(),
    records: snap.records,
  };
  const json = JSON.stringify(manifest);
  const shardDir = join(dataDir, encodeURIComponent(shardKey));
  await mkdir(shardDir, { recursive: true });
  const manifestPath = join(shardDir, `${snapshotHash}.json`);
  await writeFile(manifestPath, json, "utf8");

  counters.set(shardKey, { lastFlushTsMs: Date.now(), recordsSinceFlush: 0 });
  resetShard(shardKey);

  return {
    manifestPath,
    snapshotHash,
    recordCount: manifest.recordCount,
    byteSize: Buffer.byteLength(json, "utf8"),
  };
}
