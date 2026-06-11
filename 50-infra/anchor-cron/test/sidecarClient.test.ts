/**
 * sidecarClient — wire-protocol round-trip against an in-process
 * mock checkpointer sidecar (Unix socket on a tmpdir path).
 *
 * Covers the three ops anchor-cron actually drives:
 *   - health
 *   - anchor_pending
 *   - anchor_commit
 *
 * The mock implements the same 4-byte big-endian length-prefix +
 * msgpack envelope declared in ADR-2605171800 §Stage 1, so a passing
 * suite here is evidence that anchor-cron will talk to the real TS
 * sidecar correctly.
 */
import {afterEach, beforeEach, describe, expect, it} from "vitest";

import {
  PROTOCOL_VERSION,
  anchorCommit,
  anchorPending,
  health,
  type CommitEntry,
} from "../src/sidecarClient.js";

import {makeIndexRow, MockSidecar} from "./_mockSidecar.js";

let sidecar: MockSidecar;

beforeEach(async () => {
  sidecar = new MockSidecar();
  await sidecar.start();
});

afterEach(async () => {
  await sidecar.stop();
});

describe("sidecarClient.health", () => {
  it("round-trips a v=1 health envelope", async () => {
    await expect(health(sidecar.socketPath)).resolves.toBeUndefined();
    expect(sidecar.requests).toHaveLength(1);
    const req = sidecar.requests[0];
    expect(req.v).toBe(PROTOCOL_VERSION);
    expect(req.op).toBe("health");
  });

  it("throws when the sidecar returns ok=false", async () => {
    sidecar.failNext("health", "down for maintenance");
    await expect(health(sidecar.socketPath)).rejects.toThrowError(
      /health: down for maintenance/,
    );
  });
});

describe("sidecarClient.anchorPending", () => {
  it("returns an empty list when the sidecar has no pending rows", async () => {
    sidecar.pendingRows = [];
    const rows = await anchorPending(sidecar.socketPath, "did:test:cell");
    expect(rows).toEqual([]);
    const req = sidecar.requests[0];
    expect(req.op).toBe("anchor_pending");
    expect(req.cell_did).toBe("did:test:cell");
  });

  it("decodes a non-empty list with the SaverIndexRow shape preserved", async () => {
    sidecar.pendingRows = [
      makeIndexRow({checkpoint_id: "ckp001", mst_root_cid: "bafy-1"}),
      makeIndexRow({checkpoint_id: "ckp002", mst_root_cid: "bafy-2"}),
    ];
    const rows = await anchorPending(sidecar.socketPath, "did:test:cell");
    expect(rows).toHaveLength(2);
    expect(rows[0].checkpoint_id).toBe("ckp001");
    expect(rows[0].mst_root_cid).toBe("bafy-1");
    expect(rows[1].checkpoint_id).toBe("ckp002");
  });

  it("throws when the sidecar reports an error", async () => {
    sidecar.failNext("anchor_pending", "index unavailable");
    await expect(
      anchorPending(sidecar.socketPath, "did:test:cell"),
    ).rejects.toThrowError(/anchor_pending failed: index unavailable/);
  });
});

describe("sidecarClient.anchorCommit", () => {
  const commits: CommitEntry[] = [
    {
      thread_id: "t-1",
      checkpoint_ns: "",
      checkpoint_id: "ckp001",
      anchor_tx_hash: "0xabc",
      anchor_block_number: 100,
      anchor_log_index: 0,
    },
    {
      thread_id: "t-1",
      checkpoint_ns: "",
      checkpoint_id: "ckp002",
      anchor_tx_hash: "0xdef",
      anchor_block_number: 101,
      anchor_log_index: 0,
    },
  ];

  it("delivers a non-empty commit batch to the sidecar", async () => {
    await anchorCommit(sidecar.socketPath, "did:test:cell", commits);
    expect(sidecar.commits).toEqual(commits);
    const req = sidecar.requests[0];
    expect(req.op).toBe("anchor_commit");
    expect(req.cell_did).toBe("did:test:cell");
  });

  it("is a no-op when the commit batch is empty (no wire send)", async () => {
    await anchorCommit(sidecar.socketPath, "did:test:cell", []);
    expect(sidecar.requests).toEqual([]);
  });

  it("throws when the sidecar reports an error", async () => {
    sidecar.failNext("anchor_commit", "index write failed");
    await expect(
      anchorCommit(sidecar.socketPath, "did:test:cell", commits),
    ).rejects.toThrowError(/anchor_commit failed: index write failed/);
  });
});
