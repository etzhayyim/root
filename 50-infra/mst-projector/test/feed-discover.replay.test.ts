// L1-projection conformance smoke for `com.etzhayyim.projection.feedDiscover`.
//
// Per ADR-2605231500 §"Three conformance levels" L1 row:
//
//   L1-projection automated: (1) and (3) hold + (2) verified by structural
//   guarantee (firehose subscription, refuses out-of-order). Rebuild tool
//   exists AND IS EXERCISED IN CI.
//
// This test IS the CI exercise. It replays a fixed firehose fixture
// (test/fixtures/feed-discover.firehose.json) and asserts the resulting
// snapshot's `items` are byte-identical to test/golden/feed-discover.snapshot.json.
//
// `snapshotAt` is excluded per
//   50-infra/mst-projector/projection/kotoba-datomic-projection.edn
//   intentional_non_determinism = [{field = "snapshotAt", ...}].
//
// To regenerate the golden after an intentional behaviour change:
//   ETZ_REGEN_GOLDEN=1 pnpm test -- --test-name-pattern='L1.*golden replay'

import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  _resetForTests,
  applyFeedPostEvent,
  applyVerdictEvent,
  buildSnapshotRecord,
} from "../src/feed-discover.js";
import type { FirehoseEvent } from "../src/firehose.js";

interface FixturePostEvent {
  kind: "post";
  seq: string;
  did: string;
  rkey: string;
  op: "create" | "update" | "delete";
  recordCid?: string;
  record?: { text?: string; createdAt?: string };
}

interface FixtureVerdictEvent {
  kind: "verdict";
  seq: string;
  did: string;
  rkey: string;
  op: "create" | "update" | "delete";
  recordCid?: string;
  record?: {
    subject?: { uri?: string };
    verdict?: string;
  };
}

type FixtureEvent = FixturePostEvent | FixtureVerdictEvent;

interface Fixture {
  comment?: string;
  events: FixtureEvent[];
}

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE_PATH = join(HERE, "fixtures/feed-discover.firehose.json");
const GOLDEN_PATH = join(HERE, "golden/feed-discover.snapshot.json");

function toFirehoseEvent(e: FixtureEvent, collection: string): FirehoseEvent {
  const ev: FirehoseEvent = {
    seq: BigInt(e.seq),
    did: e.did,
    rkey: e.rkey,
    collection,
    op: e.op,
  };
  if (e.recordCid) ev.recordCid = e.recordCid;
  return ev;
}

function postFetcher(events: FixtureEvent[]) {
  const records: Record<string, { text?: string; createdAt?: string }> = {};
  for (const e of events) {
    if (e.kind !== "post") continue;
    if (e.op === "delete") continue;
    if (!e.record) continue;
    records[`${e.did}/${e.rkey}`] = e.record;
  }
  return async (did: string, rkey: string) =>
    records[`${did}/${rkey}`] ?? null;
}

function verdictFetcher(events: FixtureEvent[]) {
  const records: Record<
    string,
    { subject?: { uri?: string }; verdict?: string }
  > = {};
  for (const e of events) {
    if (e.kind !== "verdict") continue;
    if (e.op === "delete") continue;
    if (!e.record) continue;
    records[`${e.did}/${e.rkey}`] = e.record;
  }
  return async (did: string, rkey: string) =>
    records[`${did}/${rkey}`] ?? null;
}

async function loadFixture(): Promise<Fixture> {
  const raw = await readFile(FIXTURE_PATH, "utf8");
  return JSON.parse(raw) as Fixture;
}

async function replay(fixture: Fixture) {
  _resetForTests();
  const post = postFetcher(fixture.events);
  const verdict = verdictFetcher(fixture.events);
  for (const e of fixture.events) {
    if (e.kind === "post") {
      const fhe = toFirehoseEvent(e, "app.bsky.feed.post");
      await applyFeedPostEvent(fhe, post);
    } else {
      const fhe = toFirehoseEvent(e, "com.etzhayyim.membrane.verdict");
      await applyVerdictEvent(fhe, verdict);
    }
  }
  // Fixed snapshotAt so any field-level drift is caught — the manifest's
  // intentional_non_determinism list isolates it.
  const snap = buildSnapshotRecord({ now: "2026-05-23T05:00:00Z" });
  // Strip the volatile field for golden comparison.
  const { snapshotAt: _ignored, ...comparable } = snap;
  return comparable;
}

test("L1-projection conformance: feed-discover golden replay matches", async () => {
  const fixture = await loadFixture();
  const observed = await replay(fixture);
  const canonical = JSON.stringify(observed, null, 2) + "\n";

  if (process.env.ETZ_REGEN_GOLDEN === "1") {
    await writeFile(GOLDEN_PATH, canonical);
    console.log("[L1-replay] golden regenerated:", GOLDEN_PATH);
    return;
  }

  let goldenRaw: string;
  try {
    goldenRaw = await readFile(GOLDEN_PATH, "utf8");
  } catch (err) {
    throw new Error(
      `golden missing at ${GOLDEN_PATH}. Run \`ETZ_REGEN_GOLDEN=1 pnpm test\` to generate.\n` +
        (err instanceof Error ? err.message : String(err)),
    );
  }
  assert.equal(
    canonical,
    goldenRaw,
    "feed-discover snapshot drifted from golden — intentional? Regenerate with `ETZ_REGEN_GOLDEN=1 pnpm test`.",
  );
});

test("L1-projection conformance: replay is deterministic across runs", async () => {
  const fixture = await loadFixture();
  const a = await replay(fixture);
  const b = await replay(fixture);
  assert.equal(JSON.stringify(a), JSON.stringify(b));
});

test("L1-projection conformance: reject verdict drops post; approve/escalate annotates", async () => {
  // Defence in depth — even if the golden were accidentally regenerated
  // with bad data, the loop's invariant (reject => drop) must hold.
  const fixture = await loadFixture();
  const observed = await replay(fixture);
  const items = observed.items;
  // dan's post (seq 5) was rejected by verdict v3 (seq 8) → must be absent.
  assert.equal(
    items.find((i) => i.did === "did:web:dan.etzhayyim.com"),
    undefined,
    "rejected post must not appear in projection",
  );
  // bob (seq 2) was approved by verdict v1 (seq 6).
  const bob = items.find((i) => i.did === "did:web:bob.etzhayyim.com");
  assert.ok(bob, "bob's post should be present");
  assert.equal(bob!.verdict, "approve");
  // carol (seq 3) was escalated by verdict v2 (seq 7).
  const carol = items.find((i) => i.did === "did:web:carol.etzhayyim.com");
  assert.ok(carol, "carol's post should be present");
  assert.equal(carol!.verdict, "escalate");
  // eve (seq 9 create then seq 10 delete) must be absent.
  assert.equal(
    items.find((i) => i.did === "did:web:eve.etzhayyim.com"),
    undefined,
    "deleted post must not appear in projection",
  );
  // alice was updated (seq 4) — must reflect v2 content + indexedAt.
  const alice = items.find((i) => i.did === "did:web:alice.etzhayyim.com");
  assert.ok(alice, "alice's post should be present");
  assert.equal(alice!.cid, "bafyrei-alice-3kfa-v2");
  assert.equal(alice!.textPreview, "alice's first post (edited)");
});
