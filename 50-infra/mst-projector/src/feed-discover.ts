// kotoba-datomic-projection: feed-discover
//
// Per ADR-2605231500 and lexicon `com.etzhayyim.projection.feedDiscover`.
// This module is an L0-projection — derived hot-path read cache for the
// Discover feed. The canonical state is each DID's `app.bsky.feed.post`
// record in its own MST. This file MUST stay rebuildable from the firehose
// alone (no operator-held state); the rebuild runbook lives at
//   50-infra/mst-projector/projection/REBUILD.md
// and the manifest at
//   50-infra/mst-projector/projection/kotoba-datomic-projection.edn
//
// Substrate-boundary lint allow-rule: this directory has a
// kotoba-datomic-projection.edn manifest, so RW-style state primitives are
// permitted *for projections only*. The actual primitive used here is
// just an in-memory sorted index — no DB.

import { AtpAgent } from "@atproto/api";

import type { FirehoseEvent } from "./firehose.js";

const FEED_POST_COLLECTION = "app.bsky.feed.post";
const PROJECTION_COLLECTION = "com.etzhayyim.projection.feedDiscover";
const VERDICT_COLLECTION = "com.etzhayyim.membrane.verdict";
type ProjectionLevel = "L0" | "L1" | "L2";
// Bumped from L0 to L1 once `test/feed-discover.replay.test.ts` (CI-
// exercised golden replay) landed. Per ADR-2605231500 §"Three conformance
// levels" L1: "Rebuild tool exists and is exercised in CI". L2 lands
// when a 1% byte-identical random-slice replay is part of pre-deploy gates.
const PROJECTION_LEVEL: ProjectionLevel = "L1";

export interface FeedItem {
  uri: string;
  cid: string;
  did: string;
  indexedAt: string; // ISO-8601
  textPreview?: string;
  verdict?: "approve" | "escalate" | "unverdicted";
}

interface IndexEntry extends FeedItem {
  seq: bigint;
}

interface FeedDiscoverIndexState {
  /** key = `${did}/${rkey}` so update/delete operations are O(1). */
  byKey: Map<string, IndexEntry>;
  /** Sorted list maintained on insert; small N (cap << 10k) keeps O(N) cheap. */
  sortedDesc: IndexEntry[];
  /** Lifetime distinct-(did,rkey) counter used for projection drift checks. */
  totalSeen: number;
  /** First + last firehose seq covered by the in-memory window. */
  firstSeq?: bigint;
  lastSeq?: bigint;
  /** Sequence dirty flag — true when index changed since last emission. */
  dirty: boolean;
}

const MAX_ITEMS = 500;
const PREVIEW_LEN = 600;

const state: FeedDiscoverIndexState = {
  byKey: new Map(),
  sortedDesc: [],
  totalSeen: 0,
  dirty: false,
};

export function isFeedPost(ev: FirehoseEvent): boolean {
  return ev.collection === FEED_POST_COLLECTION;
}

export function isVerdict(ev: FirehoseEvent): boolean {
  return ev.collection === VERDICT_COLLECTION;
}

/**
 * Apply a single firehose event to the projection.
 *
 * `recordFetcher` is the callback that hydrates record text — separated
 * from the index so a real PDS fetch (via `com.atproto.repo.getRecord`)
 * is a strategy decision in `index.ts`, and the index unit tests can
 * supply an in-memory stub.
 */
export async function applyFeedPostEvent(
  ev: FirehoseEvent,
  recordFetcher: (
    did: string,
    rkey: string,
  ) => Promise<{ text?: string; createdAt?: string } | null>,
): Promise<{ applied: boolean; reason?: string }> {
  if (!isFeedPost(ev)) return { applied: false, reason: "wrong-collection" };
  const key = `${ev.did}/${ev.rkey}`;

  if (ev.op === "delete") {
    const existing = state.byKey.get(key);
    if (!existing) return { applied: false, reason: "delete-missing" };
    state.byKey.delete(key);
    const idx = state.sortedDesc.findIndex((e) => e === existing);
    if (idx >= 0) state.sortedDesc.splice(idx, 1);
    state.dirty = true;
    noteSeq(ev.seq);
    return { applied: true };
  }

  if (!ev.recordCid) return { applied: false, reason: "missing-record-cid" };

  let body: { text?: string; createdAt?: string } | null = null;
  try {
    body = await recordFetcher(ev.did, ev.rkey);
  } catch (err) {
    return {
      applied: false,
      reason: `record-fetch-failed:${(err as Error).message}`,
    };
  }
  if (!body) return { applied: false, reason: "record-not-found" };

  const indexedAt = sanitizeIndexedAt(body.createdAt);
  const textPreview = body.text
    ? body.text.slice(0, PREVIEW_LEN)
    : undefined;

  const entry: IndexEntry = {
    uri: `at://${ev.did}/${FEED_POST_COLLECTION}/${ev.rkey}`,
    cid: ev.recordCid,
    did: ev.did,
    indexedAt,
    textPreview,
    verdict: "unverdicted",
    seq: ev.seq,
  };

  const prev = state.byKey.get(key);
  state.byKey.set(key, entry);
  if (prev) {
    const idx = state.sortedDesc.findIndex((e) => e === prev);
    if (idx >= 0) state.sortedDesc.splice(idx, 1);
  } else {
    state.totalSeen += 1;
  }
  insertSorted(entry);
  trimToMax();
  state.dirty = true;
  noteSeq(ev.seq);
  return { applied: true };
}

/**
 * Apply a FeedPostCell verdict observation (membrane L3 sidecar) coming off
 * the firehose. Fetches the `com.etzhayyim.membrane.verdict` record via the
 * supplied callback (firehose only carries the record CID, not the body),
 * pulls out `subject.uri` + `verdict`, then defers to {@link applyVerdict}.
 *
 * Only `op: "create"` events are processed — an `update` to a verdict is
 * a re-attestation by the same cell on the same record, and `delete` of a
 * verdict has no meaningful effect on the projection.
 */
export async function applyVerdictEvent(
  ev: FirehoseEvent,
  verdictFetcher: (
    did: string,
    rkey: string,
  ) => Promise<{ subject?: { uri?: string }; verdict?: string } | null>,
): Promise<{ applied: boolean; reason?: string }> {
  if (!isVerdict(ev)) return { applied: false, reason: "wrong-collection" };
  if (ev.op !== "create") return { applied: false, reason: "skip-non-create" };
  let body: { subject?: { uri?: string }; verdict?: string } | null = null;
  try {
    body = await verdictFetcher(ev.did, ev.rkey);
  } catch (err) {
    return {
      applied: false,
      reason: `verdict-fetch-failed:${(err as Error).message}`,
    };
  }
  if (!body) return { applied: false, reason: "verdict-not-found" };
  const subjectUri = body.subject?.uri;
  const kind = body.verdict;
  if (!subjectUri || typeof subjectUri !== "string") {
    return { applied: false, reason: "subject-uri-missing" };
  }
  if (kind !== "approve" && kind !== "reject" && kind !== "escalate") {
    return { applied: false, reason: `unknown-verdict:${String(kind)}` };
  }
  applyVerdict(subjectUri, kind);
  return { applied: true };
}

/**
 * Apply a FeedPostCell verdict observation (membrane L3 sidecar).
 * The membrane verdict lives under `com.etzhayyim.membrane.verdict` records
 * keyed by the original post URI in `subject.uri`.
 */
export function applyVerdict(
  subjectUri: string,
  verdict: "approve" | "reject" | "escalate",
): void {
  // Reject = drop from projection (never promote).
  if (verdict === "reject") {
    const entry = [...state.byKey.values()].find((e) => e.uri === subjectUri);
    if (!entry) return;
    state.byKey.delete(`${entry.did}/${rkeyFromUri(subjectUri)}`);
    const idx = state.sortedDesc.findIndex((e) => e === entry);
    if (idx >= 0) state.sortedDesc.splice(idx, 1);
    state.dirty = true;
    return;
  }
  const entry = [...state.byKey.values()].find((e) => e.uri === subjectUri);
  if (!entry) return;
  if (entry.verdict !== verdict) {
    entry.verdict = verdict;
    state.dirty = true;
  }
}

export function snapshotItems(limit: number = MAX_ITEMS): FeedItem[] {
  return state.sortedDesc.slice(0, Math.min(limit, MAX_ITEMS)).map(
    ({ seq: _seq, ...rest }) => rest,
  );
}

export interface SnapshotRecord {
  $type: typeof PROJECTION_COLLECTION;
  snapshotAt: string;
  cursor: string;
  firstSeq?: string;
  items: FeedItem[];
  totalSeen: number;
  projectionLevel: ProjectionLevel;
}

export function buildSnapshotRecord(opts: {
  /** Caller-supplied wall clock — kept out of this module for testability. */
  now: string;
}): SnapshotRecord {
  const record: SnapshotRecord = {
    $type: PROJECTION_COLLECTION,
    snapshotAt: opts.now,
    cursor: (state.lastSeq ?? 0n).toString(),
    items: snapshotItems(),
    totalSeen: state.totalSeen,
    projectionLevel: PROJECTION_LEVEL,
  };
  if (state.firstSeq !== undefined) record.firstSeq = state.firstSeq.toString();
  return record;
}

export interface EmitOpts {
  did: string;
  pdsUrl: string;
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };
  auth?: { handle: string; password: string };
  now?: string;
}

let cachedAgent: AtpAgent | null = null;

async function getAgent(opts: EmitOpts): Promise<AtpAgent> {
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
      "[feed-discover] no PDS auth configured (set ETZ_PROJECTOR_PDS_SESSION or ETZ_PROJECTOR_PDS_AUTH)",
    );
  }
  cachedAgent = agent;
  return agent;
}

export async function emitSnapshot(opts: EmitOpts): Promise<{ uri: string; cid: string } | null> {
  if (!state.dirty) return null;
  const record = buildSnapshotRecord({
    now: opts.now ?? new Date().toISOString(),
  });
  const agent = await getAgent(opts);
  const res = await agent.com.atproto.repo.createRecord({
    repo: opts.did,
    collection: PROJECTION_COLLECTION,
    record: record as unknown as Record<string, unknown>,
  });
  if (!res.success) {
    throw new Error(
      `[feed-discover] createRecord failed: ${JSON.stringify(res)}`,
    );
  }
  state.dirty = false;
  return { uri: res.data.uri, cid: res.data.cid as string };
}

/**
 * Default record fetcher backed by `com.atproto.repo.getRecord`.
 * Uses the projector's PDS agent; for cross-PDS DIDs this still works
 * because the federation layer resolves DIDs to their home PDS.
 */
export function makeAtpRecordFetcher(opts: EmitOpts) {
  return async (
    did: string,
    rkey: string,
  ): Promise<{ text?: string; createdAt?: string } | null> => {
    const agent = await getAgent(opts);
    try {
      const r = await agent.com.atproto.repo.getRecord({
        repo: did,
        collection: FEED_POST_COLLECTION,
        rkey,
      });
      const v = r.data.value as Record<string, unknown> | undefined;
      if (!v) return null;
      return {
        text: typeof v.text === "string" ? v.text : undefined,
        createdAt: typeof v.createdAt === "string" ? v.createdAt : undefined,
      };
    } catch {
      return null;
    }
  };
}

/**
 * Fetcher for `com.etzhayyim.membrane.verdict` records. Separate from
 * {@link makeAtpRecordFetcher} so the collection parameter is fixed at
 * its (different) NSID — the membrane verdict subscriber never reads
 * arbitrary collections.
 */
export function makeAtpVerdictFetcher(opts: EmitOpts) {
  return async (
    did: string,
    rkey: string,
  ): Promise<{ subject?: { uri?: string }; verdict?: string } | null> => {
    const agent = await getAgent(opts);
    try {
      const r = await agent.com.atproto.repo.getRecord({
        repo: did,
        collection: VERDICT_COLLECTION,
        rkey,
      });
      const v = r.data.value as Record<string, unknown> | undefined;
      if (!v) return null;
      const subject = v.subject as { uri?: unknown } | undefined;
      return {
        subject:
          subject && typeof subject.uri === "string"
            ? { uri: subject.uri }
            : undefined,
        verdict: typeof v.verdict === "string" ? v.verdict : undefined,
      };
    } catch {
      return null;
    }
  };
}

// ── helpers ─────────────────────────────────────────────────────────

function insertSorted(entry: IndexEntry): void {
  // Binary search for descending insertion.
  let lo = 0;
  let hi = state.sortedDesc.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (state.sortedDesc[mid].indexedAt < entry.indexedAt) hi = mid;
    else lo = mid + 1;
  }
  state.sortedDesc.splice(lo, 0, entry);
}

function trimToMax(): void {
  while (state.sortedDesc.length > MAX_ITEMS) {
    const dropped = state.sortedDesc.pop()!;
    state.byKey.delete(`${dropped.did}/${rkeyFromUri(dropped.uri)}`);
  }
}

function rkeyFromUri(uri: string): string {
  const m = uri.match(/^at:\/\/[^/]+\/[^/]+\/(.+)$/);
  return m ? m[1] : "";
}

function noteSeq(seq: bigint): void {
  if (state.firstSeq === undefined) state.firstSeq = seq;
  state.lastSeq = seq;
}

function sanitizeIndexedAt(createdAt: string | undefined): string {
  if (!createdAt) return new Date().toISOString();
  // Reject createdAt-in-the-future >24h (defence against clock-skewed clients).
  const t = Date.parse(createdAt);
  if (Number.isNaN(t)) return new Date().toISOString();
  const now = Date.now();
  if (t > now + 24 * 60 * 60 * 1000) return new Date(now).toISOString();
  return new Date(t).toISOString();
}

/**
 * Test-only resetter. Module-level state would otherwise leak between
 * vitest workers; production code never calls this.
 */
export function _resetForTests(): void {
  state.byKey.clear();
  state.sortedDesc.length = 0;
  state.totalSeen = 0;
  state.firstSeq = undefined;
  state.lastSeq = undefined;
  state.dirty = false;
  cachedAgent = null;
}
