/**
 * pendingFromPds — converts ipfsPin AT records into PendingRoots for
 * the existing submit.ts path, skipping rows that already have a
 * matching l2Anchor record under the anchorer's repo.
 */
import {describe, expect, it, vi} from "vitest";

import {
  ipfsPinToPendingRoot,
  readPendingFromPds,
  type IpfsPinRecord,
} from "../src/pendingFromPds.js";

const ROOT_CID =
  "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";
const ROOT_CID_2 =
  "bafyreiezk44ovi6agnaoob3vznck6m5w3sntlcg6vsl4yhqluwwo6dxqu4";
const PINNER_REPO = "did:web:pinner.etzhayyim.com";
const ANCHORER_REPO = "did:web:anchorer.etzhayyim.com";

const PIN_A: IpfsPinRecord = {
  uri: `at://${PINNER_REPO}/com.etzhayyim.substrate.ipfsPin/3a`,
  shardKey: "com.etzhayyim.apps.threads.post",
  rootCid: ROOT_CID,
  carCid: ROOT_CID,
  byteSize: 4096,
  blockCount: 3,
  pinnedAt: "2026-05-21T12:00:00.000Z",
};

describe("ipfsPinToPendingRoot", () => {
  it("computes rootHash = sha256(rootCid as UTF-8) and shapes a PendingRoot", () => {
    const {pending, shardKey, ipfsPinUri} = ipfsPinToPendingRoot(PIN_A);
    expect(shardKey).toBe(PIN_A.shardKey);
    expect(ipfsPinUri).toBe(PIN_A.uri);
    expect(pending.rootHash).toMatch(/^0x[0-9a-f]{64}$/);
    // Deterministic — sha256 of the same string is stable.
    const again = ipfsPinToPendingRoot(PIN_A);
    expect(again.pending.rootHash).toBe(pending.rootHash);
    // ipfsCidBytes mirrors the rootCid string bytes.
    expect(new TextDecoder().decode(pending.ipfsCidBytes)).toBe(ROOT_CID);
    // batchSize = blockCount + 1 when blockCount is known.
    expect(pending.batchSize).toBe(4);
    // Row carries shardKey + rootCid identifiers that downstream callers
    // (submit.ts, commitToPds.ts) read.
    expect(pending.row.cell_did).toBe(PIN_A.shardKey);
    expect(pending.row.mst_root_cid).toBe(ROOT_CID);
  });

  it("defaults batchSize to 1 when blockCount is absent", () => {
    const {pending} = ipfsPinToPendingRoot({...PIN_A, blockCount: undefined});
    expect(pending.batchSize).toBe(1);
  });
});

function mockAgent(opts: {
  pins: Array<{uri: string; value: unknown}>;
  anchors: Array<{uri: string; value: unknown}>;
}): {
  agent: {com: {atproto: {repo: {listRecords: ReturnType<typeof vi.fn>}}}};
  calls: Array<{collection: string; cursor?: string}>;
} {
  const calls: Array<{collection: string; cursor?: string}> = [];
  const listRecords = vi.fn(async (req: {collection: string; cursor?: string}) => {
    calls.push({collection: req.collection, cursor: req.cursor});
    const records =
      req.collection === "com.etzhayyim.substrate.ipfsPin"
        ? opts.pins
        : opts.anchors;
    return {data: {records, cursor: undefined as string | undefined}};
  });
  return {
    agent: {com: {atproto: {repo: {listRecords}}}},
    calls,
  };
}

describe("readPendingFromPds", () => {
  it("returns ipfsPins without a matching l2Anchor under anchorerRepo", async () => {
    const {agent, calls} = mockAgent({
      pins: [
        {
          uri: PIN_A.uri,
          value: {
            shardKey: PIN_A.shardKey,
            rootCid: ROOT_CID,
            carCid: ROOT_CID,
            byteSize: PIN_A.byteSize,
            blockCount: PIN_A.blockCount,
            pinnedAt: PIN_A.pinnedAt,
          },
        },
        {
          uri: `at://${PINNER_REPO}/com.etzhayyim.substrate.ipfsPin/3b`,
          value: {
            shardKey: PIN_A.shardKey,
            rootCid: ROOT_CID_2,
            carCid: ROOT_CID_2,
          },
        },
      ],
      // ROOT_CID is already anchored → must be filtered out.
      anchors: [
        {
          uri: `at://${ANCHORER_REPO}/com.etzhayyim.substrate.l2Anchor/3z`,
          value: {rootCid: ROOT_CID},
        },
      ],
    });

    const out = await readPendingFromPds({
      agent: agent as never,
      pinnerRepo: PINNER_REPO,
      anchorerRepo: ANCHORER_REPO,
      limit: 10,
    });

    expect(out).toHaveLength(1);
    expect(out[0].pending.row.mst_root_cid).toBe(ROOT_CID_2);
    expect(out[0].shardKey).toBe(PIN_A.shardKey);
    // Both collections were queried.
    expect(calls.some((c) => c.collection === "com.etzhayyim.substrate.ipfsPin"))
      .toBe(true);
    expect(calls.some((c) => c.collection === "com.etzhayyim.substrate.l2Anchor"))
      .toBe(true);
  });

  it("respects the limit cap", async () => {
    const pins = Array.from({length: 5}, (_, i) => ({
      uri: `at://${PINNER_REPO}/com.etzhayyim.substrate.ipfsPin/3p${i}`,
      value: {
        shardKey: "x",
        rootCid: `bafy${"x".repeat(50)}${i}`,
        carCid: `bafy${"x".repeat(50)}${i}`,
      },
    }));
    const {agent} = mockAgent({pins, anchors: []});
    const out = await readPendingFromPds({
      agent: agent as never,
      pinnerRepo: PINNER_REPO,
      anchorerRepo: ANCHORER_REPO,
      limit: 2,
    });
    expect(out).toHaveLength(2);
  });

  it("skips rows missing required fields", async () => {
    const {agent} = mockAgent({
      pins: [
        {uri: "at://x/y/1", value: {shardKey: "x", rootCid: ROOT_CID}}, // missing carCid
        {uri: "at://x/y/2", value: {rootCid: ROOT_CID, carCid: ROOT_CID}}, // missing shardKey
        {
          uri: "at://x/y/3",
          value: {shardKey: "x", rootCid: ROOT_CID_2, carCid: ROOT_CID_2},
        },
      ],
      anchors: [],
    });
    const out = await readPendingFromPds({
      agent: agent as never,
      pinnerRepo: PINNER_REPO,
      anchorerRepo: ANCHORER_REPO,
      limit: 10,
    });
    expect(out).toHaveLength(1);
    expect(out[0].pending.row.mst_root_cid).toBe(ROOT_CID_2);
  });
});
