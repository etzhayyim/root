/**
 * Emit shard-snapshot records (Phase 1).
 *
 * After a shard flush, the projector:
 *   1. Pins the JSON manifest to IPFS via the configured Kubo HTTP API
 *      (best-effort — Phase 1 tolerates pin failure and proceeds with
 *      snapshotCid unset).
 *   2. Publishes an `app.etzhayyim.substrate.shardSnapshot` record under the
 *      projector's DID containing {shardKey, recordCount, snapshotHash,
 *      snapshotCid?, byteSize, flushedAt}.
 *
 * Downstream consumers (`ipfs-pinner` for replication, `anchor-cron` for L2
 * anchoring, app readers that need cached aggregates) subscribe to this
 * lexicon via the firehose or `listRecords`.
 *
 * Phase 2 swaps the JSON manifest for a CAR file and emits a true MST root
 * CID — the lexicon already has the schema slot (`snapshotCid` becomes
 * required, `snapshotHash` becomes deprecated/dropped).
 */

import { readFile } from "node:fs/promises";
import { AtpAgent } from "@atproto/api";

const COLLECTION = "app.etzhayyim.substrate.shardSnapshot";

export interface ShardSnapshotEmitOpts {
  /** DID of the projector emitting the record. */
  did: string;
  /** PDS service the projector authenticates against. */
  pdsUrl: string;
  /** PDS auth — handle+password OR a resumable session. */
  auth?: { handle: string; password: string };
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };
  /** Kubo HTTP API for IPFS pinning, e.g. http://localhost:5001. */
  ipfsApiUrl?: string;

  // Snapshot payload
  shardKey: string;
  manifestPath: string;
  snapshotHash: string;
  recordCount: number;
  byteSize: number;
  firstSeq?: string;
  lastSeq?: string;
}

let cachedAgent: AtpAgent | null = null;

async function getAgent(opts: ShardSnapshotEmitOpts): Promise<AtpAgent> {
  if (cachedAgent) return cachedAgent;
  const agent = new AtpAgent({ service: opts.pdsUrl });
  if (opts.session) {
    await agent.resumeSession({
      did: opts.session.did,
      handle: opts.session.handle,
      accessJwt: opts.session.accessJwt,
      refreshJwt: opts.session.refreshJwt,
      active: true,
    });
  } else if (opts.auth) {
    await agent.login({
      identifier: opts.auth.handle,
      password: opts.auth.password,
    });
  } else {
    throw new Error(
      "[mst-projector/emit] no PDS auth configured (set ETZ_PROJECTOR_PDS_SESSION or ETZ_PROJECTOR_PDS_AUTH)"
    );
  }
  cachedAgent = agent;
  return agent;
}

async function pinManifestToIpfs(
  apiUrl: string,
  manifestPath: string
): Promise<string | undefined> {
  const bytes = await readFile(manifestPath);
  const form = new FormData();
  const blob = new Blob([bytes as BlobPart], {
    type: "application/json",
  });
  form.append("file", blob);
  const res = await fetch(
    `${apiUrl.replace(/\/+$/, "")}/api/v0/add?pin=true&cid-version=1`,
    { method: "POST", body: form }
  );
  if (!res.ok) {
    throw new Error(`pin failed: ${res.status} ${await res.text()}`);
  }
  const text = await res.text();
  const lines = text.trim().split("\n").filter(Boolean);
  const last = JSON.parse(lines[lines.length - 1]);
  return typeof last.Hash === "string" ? last.Hash : undefined;
}

export async function emitShardSnapshot(
  opts: ShardSnapshotEmitOpts
): Promise<{ uri: string; cid: string; snapshotCid?: string }> {
  let snapshotCid: string | undefined;
  if (opts.ipfsApiUrl) {
    try {
      snapshotCid = await pinManifestToIpfs(opts.ipfsApiUrl, opts.manifestPath);
    } catch (err) {
      console.warn(
        `[mst-projector/emit] IPFS pin failed for ${opts.shardKey}:`,
        err
      );
    }
  }

  const agent = await getAgent(opts);
  const body: Record<string, unknown> = {
    $type: COLLECTION,
    shardKey: opts.shardKey,
    phase: 1,
    recordCount: opts.recordCount,
    snapshotHash: opts.snapshotHash,
    byteSize: opts.byteSize,
    flushedAt: new Date().toISOString(),
  };
  if (opts.firstSeq) body.firstSeq = opts.firstSeq;
  if (opts.lastSeq) body.lastSeq = opts.lastSeq;
  if (snapshotCid) body.snapshotCid = snapshotCid;

  const res = await agent.com.atproto.repo.createRecord({
    repo: opts.did,
    collection: COLLECTION,
    record: body,
  });
  if (!res.success) {
    throw new Error(
      `[mst-projector/emit] createRecord failed: ${JSON.stringify(res)}`
    );
  }
  return { uri: res.data.uri, cid: res.data.cid as string, snapshotCid };
}

/**
 * Backwards-compatible export for `index.ts` which still calls `emitMstRoot`.
 * Phase 1 wraps the shardSnapshot emit; the function name persists for the
 * upcoming Phase 2 rename.
 */
export async function emitMstRoot(opts: {
  did: string;
  pdsUrl: string;
  auth?: { handle: string; password: string };
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };
  ipfsApiUrl?: string;
  shardKey: string;
  manifestPath: string;
  snapshotHash: string;
  recordCount: number;
  byteSize: number;
  firstSeq?: string;
  lastSeq?: string;
}): Promise<{ uri: string; cid: string; snapshotCid?: string }> {
  return emitShardSnapshot(opts);
}
