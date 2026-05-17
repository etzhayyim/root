/**
 * mst-projector — PDS firehose → MST shard projector.
 *
 * Stage 3 of ADR-2605171800. Status: scaffold v0.0.0, stubs.
 *
 * Cycle:
 *   1. open firehose subscribeRepos WebSocket
 *   2. for each commit op (create / update / delete):
 *      - if NSID matches ETZ_PROJECTOR_COLLECTIONS prefix, apply to in-mem MST
 *   3. on flush boundary (records ≥ N or wall ≥ T):
 *      - serialize subtree → CAR file
 *      - compute root CID
 *      - emit ai.gftd.apps.substrate.mstRoot record to projector's PDS
 *      - persist firehose cursor
 *   4. on SIGTERM: flush in-flight + exit clean
 */

import { startFirehose } from "./firehose.js";
import { applyCommit, currentRoot } from "./mst.js";
import { shouldFlush, flushShard, type ShardKey } from "./shard.js";
import { emitMstRoot } from "./emit.js";

const CONFIG = {
  firehoseUrl:
    process.env.ETZ_PDS_FIREHOSE_URL ??
    "wss://pds.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos",
  did: process.env.ETZ_PROJECTOR_DID ?? "did:web:projector.etzhayyim.com",
  dataDir: process.env.ETZ_PROJECTOR_DATA_DIR ?? "/data/mst-projector",
  flushRecords: Number(process.env.ETZ_PROJECTOR_FLUSH_RECORDS ?? 1000),
  flushSeconds: Number(process.env.ETZ_PROJECTOR_FLUSH_SECONDS ?? 60),
  collections: (process.env.ETZ_PROJECTOR_COLLECTIONS ?? "ai.gftd.apps.")
    .split(",")
    .map((s) => s.trim()),
};

async function main() {
  console.log("[mst-projector] starting", { config: CONFIG });

  for await (const ev of startFirehose(CONFIG.firehoseUrl)) {
    if (!CONFIG.collections.some((p) => ev.collection.startsWith(p))) continue;

    const shardKey: ShardKey = ev.collection;
    applyCommit(shardKey, ev);

    if (shouldFlush(shardKey, CONFIG.flushRecords, CONFIG.flushSeconds)) {
      const rootCid = currentRoot(shardKey);
      const carPath = await flushShard(shardKey, CONFIG.dataDir);
      await emitMstRoot({
        did: CONFIG.did,
        shardKey,
        rootCid,
        carPath,
      });
      console.log(`[mst-projector] flushed ${shardKey} root=${rootCid}`);
    }
  }
}

main().catch((err) => {
  console.error("[mst-projector] fatal:", err);
  process.exit(2);
});
