/**
 * Phase 2 MST tests — true AT-Protocol MST root determinism + CAR roundtrip.
 *
 * Run via `pnpm test` (node:test under tsx). No external test framework
 * dependency; keeps the projector image small and matches the host-sdk
 * "deps that ship are deps that bake at deploy time" pattern.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { CID } from "multiformats/cid";
import {
  MemoryBlockstore,
  MST,
  readCarWithRoot,
} from "@atproto/repo";

import {
  applyCommit,
  currentRoot,
  flushShardToCar,
  recordCount,
  resetShard,
} from "./mst.js";
import type { FirehoseEvent } from "./firehose.js";

const SHARD = "com.etzhayyim.apps.threads.post";
const DID_A = "did:web:alice.etzhayyim.com";
const DID_B = "did:web:bob.etzhayyim.com";

// Two distinct, syntactically valid CIDs (raw codec, sha-256). Their
// exact bytes don't matter — only that they're well-formed strings the
// MST + multiformats can parse.
const CID_1 = "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";
const CID_2 = "bafyreiezk44ovi6agnaoob3vznck6m5w3sntlcg6vsl4yhqluwwo6dxqu4";

function ev(
  did: string,
  rkey: string,
  op: "create" | "update" | "delete",
  cidStr: string | undefined,
  seq: bigint,
): FirehoseEvent {
  return { seq, did, collection: SHARD, rkey, op, recordCid: cidStr };
}

function resetAll() {
  resetShard(SHARD);
}

// ─── Root CID determinism ────────────────────────────────────────────

test("empty shard has no root", async () => {
  resetAll();
  const root = await currentRoot(SHARD);
  assert.equal(root, null);
});

test("same insertion sequence → same MST root CID", async () => {
  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 2n));
  const root1 = await currentRoot(SHARD);
  assert.ok(root1, "first sequence produced a root");

  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 2n));
  const root2 = await currentRoot(SHARD);
  assert.equal(root2, root1, "replay yields identical root CID");
});

test("insertion order doesn't change root (sorted MST property)", async () => {
  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 2n));
  const rootForward = await currentRoot(SHARD);

  resetAll();
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 1n));
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 2n));
  const rootReverse = await currentRoot(SHARD);

  assert.equal(rootReverse, rootForward, "MST is order-independent");
});

test("delete removes key and changes root", async () => {
  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 2n));
  const rootBefore = await currentRoot(SHARD);
  const countBefore = recordCount(SHARD);

  const res = await applyCommit(SHARD, ev(DID_A, "3abc", "delete", undefined, 3n));
  assert.equal(res.applied, true);

  const rootAfter = await currentRoot(SHARD);
  assert.notEqual(rootAfter, rootBefore, "root CID changed");
  assert.equal(recordCount(SHARD), countBefore + 1);
});

test("delete on missing key is a no-op skip, not a crash", async () => {
  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  const res = await applyCommit(
    SHARD,
    ev(DID_B, "missing", "delete", undefined, 2n),
  );
  assert.equal(res.applied, false);
  assert.equal(res.reason, "delete-missing");
});

test("create without recordCid is skipped", async () => {
  resetAll();
  const res = await applyCommit(
    SHARD,
    ev(DID_A, "3abc", "create", undefined, 1n),
  );
  assert.equal(res.applied, false);
  assert.equal(res.reason, "missing-record-cid");
});

test("MST-incompatible rkey is rejected", async () => {
  resetAll();
  const res = await applyCommit(
    SHARD,
    ev(DID_A, "bad/rkey", "create", CID_1, 1n),
  );
  assert.equal(res.applied, false);
  assert.equal(res.reason, "invalid-mst-key");
});

// ─── CAR roundtrip ────────────────────────────────────────────────────

test("flushShardToCar produces CAR readable with same root", async () => {
  resetAll();
  await applyCommit(SHARD, ev(DID_A, "3abc", "create", CID_1, 1n));
  await applyCommit(SHARD, ev(DID_B, "3def", "create", CID_2, 2n));

  const flushed = await flushShardToCar(SHARD);
  assert.ok(flushed, "flush produced bytes");

  const { root, blocks } = await readCarWithRoot(flushed.carBytes);
  assert.equal(
    root.toString(),
    flushed.rootCid.toString(),
    "CAR root matches flushed rootCid",
  );

  // Reconstruct the MST from the CAR and read back our keys.
  const storage = new MemoryBlockstore();
  await storage.putMany(blocks);
  const restored = MST.load(storage, root);
  const a = await restored.get(`${DID_A}/3abc`);
  const b = await restored.get(`${DID_B}/3def`);
  assert.ok(a, "DID_A/3abc resolves in restored MST");
  assert.ok(b, "DID_B/3def resolves in restored MST");
  assert.equal(a!.toString(), CID_1);
  assert.equal(b!.toString(), CID_2);
});

test("flushShardToCar returns null for unknown shard", async () => {
  resetShard("com.etzhayyim.apps.nonexistent.foo");
  const flushed = await flushShardToCar("com.etzhayyim.apps.nonexistent.foo");
  assert.equal(flushed, null);
});

// Touch CID import so unused-import lint stays quiet even without explicit
// assertion. Confirms CID.parse remains exported by multiformats (the only
// stable API we depend on for cell.ts).
test("multiformats CID.parse accepts canonical CID strings", () => {
  const parsed = CID.parse(CID_1);
  assert.equal(parsed.toString(), CID_1);
});
