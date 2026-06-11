/**
 * Shard partitioning + flush policy + CAR serializer (Phase 2).
 *
 * Default = one shard per collection NSID. Flush when records-since-flush ≥ N
 * OR wall-clock since-last-flush ≥ T.
 *
 * Phase 2 serializes the shard as a CAR file (root + unstored MST blocks)
 * named by the AT-Protocol MST root CID, written to
 * `<dataDir>/<shardKey>/<rootCid>.car`. The deterministic filename means
 * idempotent flushes never overwrite distinct content — same root → same
 * file.
 *
 * Phase 1's JSON manifest path is retired; downstream readers were
 * already advised to prefer `rootCid` over `snapshotHash` when both are
 * present (lexicon comment + ADR-2605191655).
 */

import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import {
  flushShardToCar,
  recordCount,
  resetShard,
  shardSequenceRange,
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
  secondsThreshold: number,
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
  carPath: string;
  rootCid: string;
  recordCount: number;
  byteSize: number;
  blockCount: number;
  firstSeq?: string;
  lastSeq?: string;
}

export async function flushShard(
  shardKey: ShardKey,
  dataDir: string,
): Promise<FlushResult | null> {
  const car = await flushShardToCar(shardKey);
  if (!car) return null;
  const { firstSeq, lastSeq } = shardSequenceRange(shardKey);
  const count = recordCount(shardKey);

  const shardDir = join(dataDir, encodeURIComponent(shardKey));
  await mkdir(shardDir, { recursive: true });
  const rootCidStr = car.rootCid.toString();
  const carPath = join(shardDir, `${rootCidStr}.car`);
  await writeFile(carPath, car.carBytes);

  counters.set(shardKey, { lastFlushTsMs: Date.now(), recordsSinceFlush: 0 });
  resetShard(shardKey);

  return {
    carPath,
    rootCid: rootCidStr,
    recordCount: count,
    byteSize: car.carBytes.byteLength,
    blockCount: car.blockCount,
    firstSeq,
    lastSeq,
  };
}
