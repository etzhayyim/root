// kotoba-datomic-projection: feed-discover (unit tests).
//
// Uses node:test (same as mst.test.ts) — no external framework dependency
// keeps the projector image small. Deterministic-rebuild contract:
// given the same firehose event stream, applyFeedPostEvent +
// snapshotItems MUST produce a byte-identical snapshot. The CI replay
// smoke (L1 conformance) builds on these unit guarantees.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  _resetForTests,
  applyFeedPostEvent,
  applyVerdict,
  applyVerdictEvent,
  buildSnapshotRecord,
  isFeedPost,
  isVerdict,
  snapshotItems,
} from "./feed-discover.js";
import type { FirehoseEvent } from "./firehose.js";

function ev(
  partial: Partial<FirehoseEvent> & Pick<FirehoseEvent, "did" | "rkey" | "seq">,
): FirehoseEvent {
  return {
    collection: "app.bsky.feed.post",
    op: "create",
    recordCid: `bafy-${partial.did}-${partial.rkey}`,
    ...partial,
  };
}

const fetcher = (
  records: Record<string, { text?: string; createdAt?: string }>,
) => async (did: string, rkey: string) => records[`${did}/${rkey}`] ?? null;

test("isFeedPost matches app.bsky.feed.post only", () => {
  _resetForTests();
  assert.equal(isFeedPost(ev({ did: "did:web:a", rkey: "1", seq: 1n })), true);
  assert.equal(
    isFeedPost(
      ev({
        did: "did:web:a",
        rkey: "1",
        seq: 1n,
        collection: "app.bsky.feed.like",
      }),
    ),
    false,
  );
});

test("applyFeedPostEvent creates an entry on `create`", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "hello", createdAt: "2026-05-23T00:00:00Z" },
  });
  const r = await applyFeedPostEvent(
    ev({ did: "did:web:a", rkey: "1", seq: 1n }),
    fetch,
  );
  assert.equal(r.applied, true);
  const items = snapshotItems();
  assert.equal(items.length, 1);
  assert.equal(items[0].uri, "at://did:web:a/app.bsky.feed.post/1");
  assert.equal(items[0].did, "did:web:a");
  assert.equal(items[0].indexedAt, "2026-05-23T00:00:00.000Z");
  assert.equal(items[0].textPreview, "hello");
  assert.equal(items[0].verdict, "unverdicted");
});

test("applyFeedPostEvent sorts items by indexedAt desc across DIDs", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "older", createdAt: "2026-05-22T00:00:00Z" },
    "did:web:b/2": { text: "newest", createdAt: "2026-05-24T00:00:00Z" },
    "did:web:c/3": { text: "middle", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetch);
  await applyFeedPostEvent(ev({ did: "did:web:b", rkey: "2", seq: 2n }), fetch);
  await applyFeedPostEvent(ev({ did: "did:web:c", rkey: "3", seq: 3n }), fetch);
  const items = snapshotItems();
  assert.deepEqual(items.map((i) => i.textPreview), ["newest", "middle", "older"]);
});

test("applyFeedPostEvent `update` replaces the entry in place", async () => {
  _resetForTests();
  const fetchV1 = fetcher({
    "did:web:a/1": { text: "v1", createdAt: "2026-05-23T00:00:00Z" },
  });
  const fetchV2 = fetcher({
    "did:web:a/1": { text: "v2", createdAt: "2026-05-24T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetchV1);
  await applyFeedPostEvent(
    ev({
      did: "did:web:a",
      rkey: "1",
      seq: 2n,
      op: "update",
      recordCid: "bafy-v2",
    }),
    fetchV2,
  );
  const items = snapshotItems();
  assert.equal(items.length, 1);
  assert.equal(items[0].textPreview, "v2");
  assert.equal(items[0].cid, "bafy-v2");
});

test("applyFeedPostEvent `delete` removes the entry", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "to-delete", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetch);
  assert.equal(snapshotItems().length, 1);
  await applyFeedPostEvent(
    ev({ did: "did:web:a", rkey: "1", seq: 2n, op: "delete" }),
    fetch,
  );
  assert.equal(snapshotItems().length, 0);
});

test("applyFeedPostEvent skips records missing recordCid for non-delete ops", async () => {
  _resetForTests();
  const fetch = fetcher({});
  const r = await applyFeedPostEvent(
    {
      seq: 1n,
      did: "did:web:a",
      rkey: "1",
      collection: "app.bsky.feed.post",
      op: "create",
    },
    fetch,
  );
  assert.equal(r.applied, false);
  assert.equal(r.reason, "missing-record-cid");
});

test("applyFeedPostEvent caps index at MAX_ITEMS (500) by dropping oldest", async () => {
  _resetForTests();
  const records: Record<string, { text?: string; createdAt?: string }> = {};
  for (let i = 0; i < 600; i++) {
    const day = String(1 + (i % 28)).padStart(2, "0");
    const month = String(1 + Math.floor(i / 31)).padStart(2, "0");
    records[`did:web:bulk/${i}`] = {
      text: `post ${i}`,
      createdAt: `2026-${month}-${day}T00:00:${String(i % 60).padStart(2, "0")}Z`,
    };
  }
  const fetch = fetcher(records);
  for (let i = 0; i < 600; i++) {
    await applyFeedPostEvent(
      ev({ did: "did:web:bulk", rkey: String(i), seq: BigInt(i + 1) }),
      fetch,
    );
  }
  assert.equal(snapshotItems().length, 500);
});

test("applyVerdict promotes verdict on existing entry", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "hello", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetch);
  applyVerdict("at://did:web:a/app.bsky.feed.post/1", "approve");
  assert.equal(snapshotItems()[0].verdict, "approve");
});

test("applyVerdict drops the entry on `reject`", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "bad", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetch);
  applyVerdict("at://did:web:a/app.bsky.feed.post/1", "reject");
  assert.equal(snapshotItems().length, 0);
});

test("buildSnapshotRecord — determinism: same event sequence → identical items", async () => {
  const records = {
    "did:web:a/1": { text: "a", createdAt: "2026-05-23T01:00:00Z" },
    "did:web:b/2": { text: "b", createdAt: "2026-05-23T02:00:00Z" },
    "did:web:c/3": { text: "c", createdAt: "2026-05-23T03:00:00Z" },
  };
  const fetch = fetcher(records);
  const replay = async () => {
    _resetForTests();
    await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), fetch);
    await applyFeedPostEvent(ev({ did: "did:web:b", rkey: "2", seq: 2n }), fetch);
    await applyFeedPostEvent(ev({ did: "did:web:c", rkey: "3", seq: 3n }), fetch);
    return buildSnapshotRecord({ now: "fixed" }).items;
  };
  const a = await replay();
  const b = await replay();
  assert.equal(JSON.stringify(a), JSON.stringify(b));
});

// ── membrane → projection wire tests ─────────────────────────────────

const verdictFetcher = (
  records: Record<
    string,
    { subject?: { uri?: string }; verdict?: string }
  >,
) => async (did: string, rkey: string) => records[`${did}/${rkey}`] ?? null;

test("isVerdict matches com.etzhayyim.membrane.verdict only", () => {
  _resetForTests();
  assert.equal(
    isVerdict({
      seq: 1n,
      did: "did:web:cell",
      rkey: "1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    }),
    true,
  );
  assert.equal(
    isVerdict({
      seq: 1n,
      did: "did:web:cell",
      rkey: "1",
      collection: "app.bsky.feed.post",
      op: "create",
      recordCid: "bafy-p",
    }),
    false,
  );
});

test("applyVerdictEvent — approve verdict annotates index entry", async () => {
  _resetForTests();
  const postFetch = fetcher({
    "did:web:a/1": { text: "hello", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), postFetch);
  const vFetch = verdictFetcher({
    "did:web:cell/v1": {
      subject: { uri: "at://did:web:a/app.bsky.feed.post/1" },
      verdict: "approve",
    },
  });
  const r = await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(r.applied, true);
  assert.equal(snapshotItems()[0].verdict, "approve");
});

test("applyVerdictEvent — reject verdict drops index entry", async () => {
  _resetForTests();
  const postFetch = fetcher({
    "did:web:a/1": { text: "bad", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), postFetch);
  assert.equal(snapshotItems().length, 1);
  const vFetch = verdictFetcher({
    "did:web:cell/v1": {
      subject: { uri: "at://did:web:a/app.bsky.feed.post/1" },
      verdict: "reject",
    },
  });
  const r = await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(r.applied, true);
  assert.equal(snapshotItems().length, 0);
});

test("applyVerdictEvent — escalate verdict annotates index entry", async () => {
  _resetForTests();
  const postFetch = fetcher({
    "did:web:a/1": { text: "context", createdAt: "2026-05-23T00:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 1n }), postFetch);
  const vFetch = verdictFetcher({
    "did:web:cell/v1": {
      subject: { uri: "at://did:web:a/app.bsky.feed.post/1" },
      verdict: "escalate",
    },
  });
  await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(snapshotItems()[0].verdict, "escalate");
});

test("applyVerdictEvent — non-create ops are skipped", async () => {
  _resetForTests();
  const vFetch = verdictFetcher({});
  const r = await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "update",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(r.applied, false);
  assert.equal(r.reason, "skip-non-create");
});

test("applyVerdictEvent — unknown verdict kind rejected", async () => {
  _resetForTests();
  const vFetch = verdictFetcher({
    "did:web:cell/v1": {
      subject: { uri: "at://did:web:a/app.bsky.feed.post/1" },
      verdict: "maybe-someday",
    },
  });
  const r = await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(r.applied, false);
  assert.equal(r.reason, "unknown-verdict:maybe-someday");
});

test("applyVerdictEvent — verdict for unknown subject is a no-op (not an error)", async () => {
  _resetForTests();
  // No applyFeedPostEvent — the index is empty, so the verdict has nothing
  // to update or drop. Per the projection contract (rebuild-from-firehose),
  // verdicts that arrive before their post are not an error; the post's
  // own create event will arrive later and applyVerdict() can be re-emitted
  // from a follow-up cell run.
  const vFetch = verdictFetcher({
    "did:web:cell/v1": {
      subject: { uri: "at://did:web:a/app.bsky.feed.post/1" },
      verdict: "approve",
    },
  });
  const r = await applyVerdictEvent(
    {
      seq: 2n,
      did: "did:web:cell",
      rkey: "v1",
      collection: "com.etzhayyim.membrane.verdict",
      op: "create",
      recordCid: "bafy-v",
    },
    vFetch,
  );
  assert.equal(r.applied, true);
  assert.equal(snapshotItems().length, 0);
});

test("buildSnapshotRecord includes cursor + level + totalSeen", async () => {
  _resetForTests();
  const fetch = fetcher({
    "did:web:a/1": { text: "a", createdAt: "2026-05-23T01:00:00Z" },
  });
  await applyFeedPostEvent(ev({ did: "did:web:a", rkey: "1", seq: 42n }), fetch);
  const snap = buildSnapshotRecord({ now: "2026-05-23T05:00:00Z" });
  assert.equal(snap.snapshotAt, "2026-05-23T05:00:00Z");
  assert.equal(snap.cursor, "42");
  assert.equal(snap.firstSeq, "42");
  assert.equal(snap.totalSeen, 1);
  assert.equal(snap.projectionLevel, "L1");
});
