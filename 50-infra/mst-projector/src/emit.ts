/**
 * Emit shard-snapshot records (Phase 2).
 *
 * After a shard flush:
 *   1. Pin the CAR file to IPFS via the configured Kubo HTTP API
 *      (best-effort — fall back to omitting `snapshotCid` if the pin
 *      service is unreachable; the `rootCid` still guarantees content
 *      identity).
 *   2. Publish an `com.etzhayyim.substrate.shardSnapshot` record under
 *      the projector's DID with `phase: 2`, the AT-Protocol MST
 *      `rootCid`, the IPFS `snapshotCid`, and the seq range covered.
 *
 * Downstream consumers (ipfs-pinner for replication, anchor-cron for L2
 * anchoring, app readers) subscribe to this lexicon via the firehose or
 * `listRecords`.
 *
 * Phase 1's `snapshotHash` field is no longer populated; the lexicon's
 * 4-week deprecation grace (per ADR-2605191655) starts at the first
 * Phase 2 emission.
 */

import { readFile } from "node:fs/promises";
import { AtpAgent } from "@atproto/api";

const COLLECTION = "com.etzhayyim.substrate.shardSnapshot";
const PHASE = 2 as const;

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

  // Snapshot payload (Phase 2 fields)
  shardKey: string;
  carPath: string;
  rootCid: string;
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
      "[mst-projector/emit] no PDS auth configured (set ETZ_PROJECTOR_PDS_SESSION or ETZ_PROJECTOR_PDS_AUTH)",
    );
  }
  cachedAgent = agent;
  return agent;
}

async function pinCarToIpfs(
  apiUrl: string,
  carPath: string,
): Promise<string | undefined> {
  const bytes = await readFile(carPath);
  const form = new FormData();
  const blob = new Blob([bytes as BlobPart], {
    type: "application/vnd.ipld.car",
  });
  form.append("file", blob);
  const res = await fetch(
    `${apiUrl.replace(/\/+$/, "")}/api/v0/add?pin=true&cid-version=1`,
    { method: "POST", body: form },
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
  opts: ShardSnapshotEmitOpts,
): Promise<{ uri: string; cid: string; snapshotCid?: string }> {
  let snapshotCid: string | undefined;
  if (opts.ipfsApiUrl) {
    try {
      snapshotCid = await pinCarToIpfs(opts.ipfsApiUrl, opts.carPath);
    } catch (err) {
      console.warn(
        `[mst-projector/emit] IPFS pin failed for ${opts.shardKey}:`,
        err,
      );
    }
  }

  const agent = await getAgent(opts);
  const body: Record<string, unknown> = {
    $type: COLLECTION,
    shardKey: opts.shardKey,
    phase: PHASE,
    rootCid: opts.rootCid,
    recordCount: opts.recordCount,
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
      `[mst-projector/emit] createRecord failed: ${JSON.stringify(res)}`,
    );
  }
  return { uri: res.data.uri, cid: res.data.cid as string, snapshotCid };
}

/** Phase 1 alias retained for `index.ts` callers; will be removed once they
 *  migrate to `emitShardSnapshot`. Identical implementation. */
export const emitMstRoot = emitShardSnapshot;
