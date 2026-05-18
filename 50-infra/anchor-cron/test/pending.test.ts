/**
 * pending — rootHash computation is the contract between anchor-cron
 * and the EtzhayyimAnchor on-chain mapping. We pin the formula
 * (sha256 over UTF-8 bytes of mst_root_cid) so any future change is
 * caught by a failing test rather than a silent off-chain / on-chain
 * lookup mismatch.
 */
import {afterEach, beforeEach, describe, expect, it} from "vitest";
import {sha256} from "@noble/hashes/sha256";
import {bytesToHex} from "@noble/hashes/utils";

import {readPending} from "../src/pending.js";

import {makeIndexRow, MockSidecar} from "./_mockSidecar.js";

let sidecar: MockSidecar;

beforeEach(async () => {
  sidecar = new MockSidecar();
  await sidecar.start();
});

afterEach(async () => {
  await sidecar.stop();
});

describe("readPending", () => {
  it("returns an empty array when the sidecar has nothing pending", async () => {
    sidecar.pendingRows = [];
    const pending = await readPending({
      socketPath: sidecar.socketPath,
      cellDid: "did:test:cell",
      limit: 10,
    });
    expect(pending).toEqual([]);
  });

  it("computes rootHash = sha256(UTF-8(mst_root_cid)) for every row", async () => {
    sidecar.pendingRows = [
      makeIndexRow({checkpoint_id: "ckp001", mst_root_cid: "bafy-one"}),
      makeIndexRow({checkpoint_id: "ckp002", mst_root_cid: "bafy-two"}),
    ];
    const pending = await readPending({
      socketPath: sidecar.socketPath,
      cellDid: "did:test:cell",
      limit: 10,
    });
    expect(pending).toHaveLength(2);
    for (const p of pending) {
      const expectedBytes = new TextEncoder().encode(p.row.mst_root_cid);
      const expectedHash = ("0x" +
        bytesToHex(sha256(expectedBytes))) as `0x${string}`;
      expect(p.rootHash).toBe(expectedHash);
      expect(Array.from(p.ipfsCidBytes)).toEqual(Array.from(expectedBytes));
    }
  });

  it("sets batchSize = car_blob_count + 1 (inline record + blobs)", async () => {
    sidecar.pendingRows = [
      makeIndexRow({mst_root_cid: "bafy-a", car_blob_count: 0}),
      makeIndexRow({mst_root_cid: "bafy-b", car_blob_count: 3}),
    ];
    const pending = await readPending({
      socketPath: sidecar.socketPath,
      cellDid: "did:test:cell",
      limit: 10,
    });
    expect(pending[0].batchSize).toBe(1);
    expect(pending[1].batchSize).toBe(4);
  });

  it("trims the result to `limit` rows", async () => {
    sidecar.pendingRows = Array.from({length: 7}, (_, i) =>
      makeIndexRow({checkpoint_id: `ckp00${i}`, mst_root_cid: `bafy-${i}`}),
    );
    const pending = await readPending({
      socketPath: sidecar.socketPath,
      cellDid: "did:test:cell",
      limit: 3,
    });
    expect(pending).toHaveLength(3);
  });
});
