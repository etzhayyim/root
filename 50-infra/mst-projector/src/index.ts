/**
 * mst-projector — PDS firehose → shard-snapshot projector.
 *
 * Per ADR-2605191358 step 5 (Phase 1). Cycle:
 *   1. open firehose subscribeRepos WebSocket (resumed from cursor file)
 *   2. for each commit op: if its collection prefix is in
 *      ETZ_PROJECTOR_COLLECTIONS, apply to the per-shard in-memory record list
 *   3. on flush boundary (records-since-flush ≥ N or wall ≥ T seconds):
 *      - serialise the shard to a JSON manifest (Phase 1; CAR in Phase 2)
 *      - pin the manifest to IPFS (best-effort)
 *      - emit `app.etzhayyim.substrate.shardSnapshot` AT record under the
 *        projector's DID, including snapshotHash + snapshotCid
 *   4. on SIGTERM: flush in-flight shards + exit
 */

import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { startFirehose } from "./firehose.js";
import { applyCommit, recordCount, shardSnapshot } from "./mst.js";
import {
  flushShard,
  notePending,
  shouldFlush,
  type ShardKey,
} from "./shard.js";
import { emitShardSnapshot } from "./emit.js";

interface ResolvedConfig {
  firehoseUrl: string;
  did: string;
  pdsUrl: string;
  dataDir: string;
  flushRecords: number;
  flushSeconds: number;
  collections: string[];
  ipfsApiUrl?: string;
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };
  auth?: { handle: string; password: string };
}

function loadConfig(): ResolvedConfig {
  const session = process.env.ETZ_PROJECTOR_PDS_SESSION
    ? (JSON.parse(process.env.ETZ_PROJECTOR_PDS_SESSION) as {
        did: string;
        handle: string;
        accessJwt: string;
        refreshJwt: string;
      })
    : undefined;
  const auth = !session && process.env.ETZ_PROJECTOR_PDS_AUTH
    ? (JSON.parse(process.env.ETZ_PROJECTOR_PDS_AUTH) as {
        handle: string;
        password: string;
      })
    : undefined;
  return {
    firehoseUrl:
      process.env.ETZ_PDS_FIREHOSE_URL ??
      "wss://pds.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos",
    did:
      process.env.ETZ_PROJECTOR_DID ?? "did:web:projector.etzhayyim.com",
    pdsUrl: process.env.ETZ_PROJECTOR_PDS_URL ?? "https://pds.etzhayyim.com",
    dataDir: process.env.ETZ_PROJECTOR_DATA_DIR ?? "/data/mst-projector",
    flushRecords: Number(process.env.ETZ_PROJECTOR_FLUSH_RECORDS ?? 1000),
    flushSeconds: Number(process.env.ETZ_PROJECTOR_FLUSH_SECONDS ?? 60),
    collections: (
      process.env.ETZ_PROJECTOR_COLLECTIONS ??
      "app.etzhayyim.,ai.gftd.apps."
    )
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    ipfsApiUrl: process.env.ETZ_PROJECTOR_IPFS_API_URL,
    session,
    auth,
  };
}

async function flushAndEmit(
  config: ResolvedConfig,
  shardKey: ShardKey
): Promise<void> {
  const pre = shardSnapshot(shardKey);
  const flushed = await flushShard(shardKey, config.dataDir);
  try {
    const receipt = await emitShardSnapshot({
      did: config.did,
      pdsUrl: config.pdsUrl,
      session: config.session,
      auth: config.auth,
      ipfsApiUrl: config.ipfsApiUrl,
      shardKey,
      manifestPath: flushed.manifestPath,
      snapshotHash: flushed.snapshotHash,
      recordCount: flushed.recordCount,
      byteSize: flushed.byteSize,
      firstSeq: pre.firstSeq,
      lastSeq: pre.lastSeq,
    });
    console.log(
      `[mst-projector] flushed ${shardKey} count=${flushed.recordCount} hash=${flushed.snapshotHash} snapshotCid=${receipt.snapshotCid ?? "—"} uri=${receipt.uri}`
    );
  } catch (err) {
    console.error(`[mst-projector] emit failed for ${shardKey}:`, err);
  }
}

async function main() {
  const config = loadConfig();
  console.log("[mst-projector] starting", {
    firehoseUrl: config.firehoseUrl,
    did: config.did,
    dataDir: config.dataDir,
    flushRecords: config.flushRecords,
    flushSeconds: config.flushSeconds,
    collections: config.collections,
    pdsUrl: config.pdsUrl,
    ipfsApiUrl: config.ipfsApiUrl ?? "(none)",
    authMode: config.session ? "session" : config.auth ? "password" : "none",
  });

  await mkdir(config.dataDir, { recursive: true });
  const cursorFile = join(config.dataDir, "firehose.cursor");

  for await (const ev of startFirehose(config.firehoseUrl, { cursorFile })) {
    if (!config.collections.some((p) => ev.collection.startsWith(p))) continue;

    const shardKey: ShardKey = ev.collection;
    applyCommit(shardKey, ev);
    notePending(shardKey);

    if (shouldFlush(shardKey, config.flushRecords, config.flushSeconds)) {
      if (recordCount(shardKey) === 0) continue;
      await flushAndEmit(config, shardKey);
    }
  }
}

main().catch((err) => {
  console.error("[mst-projector] fatal:", err);
  process.exit(2);
});
