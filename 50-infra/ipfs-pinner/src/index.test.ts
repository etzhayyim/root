/**
 * index.ts tests — discoverCars walks the mst-projector data-dir
 * layout (`<dataDir>/<urlencoded shardKey>/<rootCid>.car`) and
 * decodes (shardKey, rootCid) correctly for downstream pinOne calls.
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { discoverCars } from "./index.js";

const ROOT_CID =
  "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";
const ROOT_CID_2 =
  "bafyreiezk44ovi6agnaoob3vznck6m5w3sntlcg6vsl4yhqluwwo6dxqu4";

test("discoverCars returns empty for missing dataDir", async () => {
  const out = await discoverCars(join(tmpdir(), "ipfs-pinner-missing-xyz"));
  assert.deepEqual(out, []);
});

test("discoverCars enumerates shardKey/rootCid pairs from on-disk CARs", async () => {
  const root = await mkdtemp(join(tmpdir(), "ipfs-pinner-test-"));
  const shardKey = "com.etzhayyim.apps.threads.post";
  const shardDir = join(root, encodeURIComponent(shardKey));
  await mkdir(shardDir, { recursive: true });
  await writeFile(join(shardDir, `${ROOT_CID}.car`), Buffer.from([1, 2, 3]));
  await writeFile(
    join(shardDir, `${ROOT_CID_2}.car`),
    Buffer.from([4, 5, 6, 7]),
  );
  // Stray non-CAR file must be ignored.
  await writeFile(join(shardDir, "ignore.txt"), "stray");

  const found = await discoverCars(root);
  found.sort((a, b) => a.rootCid.localeCompare(b.rootCid));

  assert.equal(found.length, 2);
  assert.equal(found[0].shardKey, shardKey);
  assert.equal(found[0].rootCid, ROOT_CID_2);
  assert.equal(found[0].byteSize, 4);
  assert.equal(found[1].rootCid, ROOT_CID);
  assert.equal(found[1].byteSize, 3);
});

test("discoverCars decodes urlencoded shardKey segments", async () => {
  const root = await mkdtemp(join(tmpdir(), "ipfs-pinner-test-"));
  const shardKey = "com.etzhayyim.substrate.shardSnapshot";
  const shardDir = join(root, encodeURIComponent(shardKey));
  await mkdir(shardDir, { recursive: true });
  await writeFile(join(shardDir, `${ROOT_CID}.car`), Buffer.from([0]));

  const found = await discoverCars(root);
  assert.equal(found.length, 1);
  assert.equal(found[0].shardKey, shardKey);
});
