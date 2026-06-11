/**
 * Emit pin receipts.
 *
 * After a CAR has been pinned by ≥1 providers (the production
 * invariant in `index.ts` enforces ≥2, but `emitPinRecord` itself
 * accepts any non-empty `providers` set so single-provider Kubo dev
 * loops still produce a public trail), publish an
 * `com.etzhayyim.substrate.ipfsPin` record under the pinner's DID.
 *
 * The record links back to the originating
 * `com.etzhayyim.substrate.shardSnapshot` via `rootCid` (always) and
 * `snapshotUri` (when known — Phase 1 emissions that read local CAR
 * files directly may omit this).
 *
 * Per ADR-2605171800 Stage 4.
 */

import { AtpAgent } from "@atproto/api";

const COLLECTION = "com.etzhayyim.substrate.ipfsPin";

export interface PinEmitOpts {
  /** DID of the pinner emitting the record. */
  did: string;
  /** PDS service to authenticate against. */
  pdsUrl: string;
  /** PDS auth — handle+password OR a resumable session. */
  auth?: { handle: string; password: string };
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };

  // Pin payload
  shardKey: string;
  rootCid: string;
  carCid: string;
  providers: string[];
  byteSize: number;
  blockCount?: number;
  snapshotUri?: string;
  pinnedAt: string;
}

let cachedAgent: AtpAgent | null = null;

async function getAgent(opts: PinEmitOpts): Promise<AtpAgent> {
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
      "[ipfs-pinner/emit] no PDS auth configured (set ETZ_PINNER_PDS_SESSION or ETZ_PINNER_PDS_AUTH)",
    );
  }
  cachedAgent = agent;
  return agent;
}

/**
 * Construct the AT-Protocol record body without performing any
 * network IO. Exposed for unit tests that assert payload shape +
 * required fields without booting an AtpAgent.
 */
export function buildPinRecord(opts: PinEmitOpts): Record<string, unknown> {
  if (!opts.providers || opts.providers.length === 0) {
    throw new Error("[ipfs-pinner/emit] providers must be non-empty");
  }
  const body: Record<string, unknown> = {
    $type: COLLECTION,
    shardKey: opts.shardKey,
    rootCid: opts.rootCid,
    carCid: opts.carCid,
    providers: opts.providers,
    byteSize: opts.byteSize,
    pinnedAt: opts.pinnedAt,
  };
  if (typeof opts.blockCount === "number") body.blockCount = opts.blockCount;
  if (opts.snapshotUri) body.snapshotUri = opts.snapshotUri;
  return body;
}

export async function emitPinRecord(
  opts: PinEmitOpts,
): Promise<{ uri: string; cid: string }> {
  const agent = await getAgent(opts);
  const body = buildPinRecord(opts);
  const res = await agent.com.atproto.repo.createRecord({
    repo: opts.did,
    collection: COLLECTION,
    record: body,
  });
  if (!res.success) {
    throw new Error(
      `[ipfs-pinner/emit] createRecord failed: ${JSON.stringify(res)}`,
    );
  }
  return { uri: res.data.uri, cid: res.data.cid as string };
}
