/**
 * emit.ts tests — payload shape + invariants for buildPinRecord.
 *
 * The AtpAgent-backed `emitPinRecord` requires PDS auth + network and
 * is exercised at deploy time. buildPinRecord is the pure helper that
 * encodes the lexicon contract; that's what we lock down here.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { buildPinRecord } from "./emit.js";

const BASE = {
  did: "did:web:pinner.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  shardKey: "com.etzhayyim.apps.threads.post",
  rootCid: "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44",
  carCid: "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44",
  providers: ["kubo"],
  byteSize: 4096,
  pinnedAt: "2026-05-21T12:00:00.000Z",
};

test("buildPinRecord emits the lexicon $type + required fields", () => {
  const body = buildPinRecord(BASE);
  assert.equal(body.$type, "com.etzhayyim.substrate.ipfsPin");
  assert.equal(body.shardKey, BASE.shardKey);
  assert.equal(body.rootCid, BASE.rootCid);
  assert.equal(body.carCid, BASE.carCid);
  assert.deepEqual(body.providers, ["kubo"]);
  assert.equal(body.byteSize, 4096);
  assert.equal(body.pinnedAt, BASE.pinnedAt);
});

test("buildPinRecord omits optional fields when absent", () => {
  const body = buildPinRecord(BASE);
  assert.equal("blockCount" in body, false);
  assert.equal("snapshotUri" in body, false);
});

test("buildPinRecord carries optional blockCount + snapshotUri when present", () => {
  const body = buildPinRecord({
    ...BASE,
    blockCount: 7,
    snapshotUri:
      "at://did:web:projector.etzhayyim.com/com.etzhayyim.substrate.shardSnapshot/3kabcd",
  });
  assert.equal(body.blockCount, 7);
  assert.equal(
    body.snapshotUri,
    "at://did:web:projector.etzhayyim.com/com.etzhayyim.substrate.shardSnapshot/3kabcd",
  );
});

test("buildPinRecord rejects empty providers list", () => {
  assert.throws(
    () => buildPinRecord({ ...BASE, providers: [] }),
    /providers must be non-empty/,
  );
});
