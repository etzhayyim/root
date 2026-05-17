/**
 * Shard partitioning + flush policy.
 *
 * Default = one shard per collection NSID (`ai.gftd.apps.openIsco.occupation`).
 * Flush when records-since-flush ≥ N OR wall-clock ≥ T.
 */

export type ShardKey = string;

export function shouldFlush(
  _shardKey: ShardKey,
  _recordsThreshold: number,
  _secondsThreshold: number
): boolean {
  throw new Error(
    "[mst-projector/shard] shouldFlush TODO: track per-shard last-flush " +
      "timestamp + record counter, return true when either threshold crosses."
  );
}

export async function flushShard(
  _shardKey: ShardKey,
  _dataDir: string
): Promise<string> {
  throw new Error(
    "[mst-projector/shard] flushShard TODO: serialize current MST to CAR file " +
      "in dataDir/<shardKey>/<root-cid>.car, return the file path."
  );
}
