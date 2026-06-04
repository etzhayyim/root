/**
 * mst-projector — PDS firehose → shard-snapshot projector.
 *
 * Phase 2 (per ADR-2605171800 + ADR-2605191655). Cycle:
 *   1. open firehose subscribeRepos WebSocket (resumed from cursor file)
 *   2. for each commit op: if its collection prefix is in
 *      ETZ_PROJECTOR_COLLECTIONS, apply to the per-shard in-memory MST
 *      (true AT-Protocol MST via @atproto/repo)
 *   3. on flush boundary (records-since-flush ≥ N or wall ≥ T seconds):
 *      - serialise the shard to a CAR file (root + unstored MST blocks)
 *      - pin the CAR to IPFS (best-effort)
 *      - emit `com.etzhayyim.substrate.shardSnapshot` AT record under the
 *        projector's DID with `phase: 2`, `rootCid`, `snapshotCid`
 *   4. on SIGTERM: flush in-flight shards + exit
 */

import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { startFirehose } from "./firehose.js";
import { applyCommit, recordCount } from "./mst.js";
import {
  flushShard,
  notePending,
  shouldFlush,
  type ShardKey,
} from "./shard.js";
import { emitShardSnapshot } from "./emit.js";
import {
  applyFeedPostEvent,
  applyVerdictEvent,
  emitSnapshot as emitFeedDiscoverSnapshot,
  isFeedPost,
  isVerdict,
  makeAtpRecordFetcher,
  makeAtpVerdictFetcher,
} from "./feed-discover.js";

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
      // `app.bsky.feed.` is included so the feed-discover kotoba-datomic-projection
      // (see src/feed-discover.ts + projection/kotoba-datomic-projection.edn) can
      // index posts. `com.etzhayyim.membrane.` is the FeedPostCell verdict
      // sidecar that drives applyVerdict on the projection. Per ADR-2605231500
      // + ADR-2605231400 SPEC §4.
      "com.etzhayyim.,com.etzhayyim.apps.,app.bsky.feed.,com.etzhayyim.membrane."
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
  shardKey: ShardKey,
): Promise<void> {
  const flushed = await flushShard(shardKey, config.dataDir);
  if (!flushed) return;
  try {
    const receipt = await emitShardSnapshot({
      did: config.did,
      pdsUrl: config.pdsUrl,
      session: config.session,
      auth: config.auth,
      ipfsApiUrl: config.ipfsApiUrl,
      shardKey,
      carPath: flushed.carPath,
      rootCid: flushed.rootCid,
      recordCount: flushed.recordCount,
      byteSize: flushed.byteSize,
      firstSeq: flushed.firstSeq,
      lastSeq: flushed.lastSeq,
    });
    console.log(
      `[mst-projector] flushed ${shardKey} count=${flushed.recordCount} rootCid=${flushed.rootCid} snapshotCid=${receipt.snapshotCid ?? "—"} uri=${receipt.uri}`,
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
    phase: 2,
  });

  await mkdir(config.dataDir, { recursive: true });
  const cursorFile = join(config.dataDir, "firehose.cursor");

  let skippedSinceLastLog = 0;
  // kotoba-datomic-projection: feed-discover hydration callbacks. See
  // projection/kotoba-datomic-projection.edn.
  const feedDiscoverFetcher = makeAtpRecordFetcher({
    did: config.did,
    pdsUrl: config.pdsUrl,
    session: config.session,
    auth: config.auth,
  });
  const verdictFetcher = makeAtpVerdictFetcher({
    did: config.did,
    pdsUrl: config.pdsUrl,
    session: config.session,
    auth: config.auth,
  });

  for await (const ev of startFirehose(config.firehoseUrl, { cursorFile })) {
    if (!config.collections.some((p) => ev.collection.startsWith(p))) continue;

    // kotoba-datomic-projection: feed-discover side-effects. Both updates the
    // in-memory cross-DID index; emission piggy-backs on the shard flush
    // cadence so there is no extra wall-clock timer.
    if (isFeedPost(ev)) {
      const fdRes = await applyFeedPostEvent(ev, feedDiscoverFetcher);
      if (!fdRes.applied && fdRes.reason !== "delete-missing") {
        // Silent skip — feed-discover is best-effort; the canonical record
        // is still the MST entry.
      }
    } else if (isVerdict(ev)) {
      // Membrane → projection wire: a FeedPostCell verdict observation
      // drops (reject) or annotates (approve / escalate) the projection.
      // Per ADR-2605231400 SPEC §4 + lexicon
      // `com.etzhayyim.projection.feedDiscover` feedItem.verdict.
      const vRes = await applyVerdictEvent(ev, verdictFetcher);
      if (!vRes.applied && vRes.reason !== "skip-non-create") {
        console.warn(
          `[mst-projector] verdict skip seq=${ev.seq} reason=${vRes.reason}`,
        );
      }
    }

    const shardKey: ShardKey = ev.collection;
    const res = await applyCommit(shardKey, ev);
    if (!res.applied) {
      skippedSinceLastLog += 1;
      if (skippedSinceLastLog % 100 === 1) {
        console.warn(
          `[mst-projector] skip ${shardKey} seq=${ev.seq} reason=${res.reason}`,
        );
      }
      continue;
    }
    notePending(shardKey);

    if (shouldFlush(shardKey, config.flushRecords, config.flushSeconds)) {
      if (recordCount(shardKey) === 0) continue;
      await flushAndEmit(config, shardKey);
      // Same flush boundary → emit feed-discover snapshot if dirty.
      try {
        const fdReceipt = await emitFeedDiscoverSnapshot({
          did: config.did,
          pdsUrl: config.pdsUrl,
          session: config.session,
          auth: config.auth,
        });
        if (fdReceipt) {
          console.log(
            `[mst-projector] feed-discover snapshot emitted uri=${fdReceipt.uri}`,
          );
        }
      } catch (err) {
        console.error("[mst-projector] feed-discover emit failed:", err);
      }
    }
  }
}

main().catch((err) => {
  console.error("[mst-projector] fatal:", err);
  process.exit(2);
});
