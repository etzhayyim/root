/**
 * commitToPds — buildL2AnchorRecord lexicon shape + commitL2Anchor
 * AtpAgent wiring (mocked).
 */
import {describe, expect, it, vi} from "vitest";

import {
  buildL2AnchorRecord,
  commitL2Anchor,
} from "../src/commitToPds.js";

const ROOT_CID =
  "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";
const ROOT_HASH =
  "0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789" as const;
const TX_HASH =
  "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" as const;
const ANCHORER = "0xC0fFEE000000000000000000000000000000Cafe" as const;
const ZERO_HASH = ("0x" + "0".repeat(64)) as `0x${string}`;

const BASE = {
  shardKey: "com.etzhayyim.apps.threads.post",
  rootCid: ROOT_CID,
  rootHash: ROOT_HASH,
  chainId: 84532,
  contract: "0x1111111111111111111111111111111111111111" as const,
  anchorer: ANCHORER,
  batchSize: 3,
  ipfsPinUri:
    "at://did:web:pinner.etzhayyim.com/com.etzhayyim.substrate.ipfsPin/3a",
};

describe("buildL2AnchorRecord", () => {
  it("emits the lexicon $type + required fields for a fresh anchor", () => {
    const body = buildL2AnchorRecord({
      ...BASE,
      submit: {
        txHash: TX_HASH,
        blockNumber: 1234,
        logIndex: 2,
        alreadyAnchored: false,
      },
      anchoredAt: "2026-05-21T12:00:00.000Z",
    });
    expect(body.$type).toBe("com.etzhayyim.substrate.l2Anchor");
    expect(body.shardKey).toBe(BASE.shardKey);
    expect(body.rootCid).toBe(ROOT_CID);
    expect(body.rootHash).toBe(ROOT_HASH);
    expect(body.txHash).toBe(TX_HASH);
    expect(body.blockNumber).toBe(1234);
    expect(body.logIndex).toBe(2);
    expect(body.chainId).toBe(84532);
    expect(body.contract).toBe(BASE.contract);
    expect(body.anchorer).toBe(ANCHORER);
    expect(body.batchSize).toBe(3);
    expect(body.alreadyAnchored).toBe(false);
    expect(body.ipfsPinUri).toBe(BASE.ipfsPinUri);
    expect(body.anchoredAt).toBe("2026-05-21T12:00:00.000Z");
  });

  it("flags alreadyAnchored + zero-hash tx for prior-tick repeats", () => {
    const body = buildL2AnchorRecord({
      ...BASE,
      submit: {
        txHash: ZERO_HASH,
        blockNumber: 999,
        logIndex: 0,
        alreadyAnchored: true,
      },
    });
    expect(body.alreadyAnchored).toBe(true);
    expect(body.txHash).toBe(ZERO_HASH);
    expect(typeof body.anchoredAt).toBe("string");
  });

  it("omits ipfsPinUri when not supplied", () => {
    const body = buildL2AnchorRecord({
      ...BASE,
      ipfsPinUri: undefined,
      submit: {
        txHash: TX_HASH,
        blockNumber: 1,
        logIndex: 0,
        alreadyAnchored: false,
      },
    });
    expect("ipfsPinUri" in body).toBe(false);
  });
});

describe("commitL2Anchor", () => {
  it("dispatches createRecord with the built body", async () => {
    const createRecord = vi.fn(async () => ({
      success: true,
      data: {
        uri: "at://did:web:anchorer.etzhayyim.com/com.etzhayyim.substrate.l2Anchor/3rk",
        cid: "bafyrecordcid",
      },
    }));
    const agent = {
      com: {atproto: {repo: {createRecord}}},
    } as never;

    const out = await commitL2Anchor({
      agent,
      repo: "did:web:anchorer.etzhayyim.com",
      ...BASE,
      submit: {
        txHash: TX_HASH,
        blockNumber: 5,
        logIndex: 0,
        alreadyAnchored: false,
      },
    });

    expect(out.uri).toContain("com.etzhayyim.substrate.l2Anchor");
    expect(createRecord).toHaveBeenCalledTimes(1);
    const arg = createRecord.mock.calls[0][0] as {
      repo: string;
      collection: string;
      record: {rootCid: string; chainId: number};
    };
    expect(arg.collection).toBe("com.etzhayyim.substrate.l2Anchor");
    expect(arg.repo).toBe("did:web:anchorer.etzhayyim.com");
    expect(arg.record.rootCid).toBe(ROOT_CID);
    expect(arg.record.chainId).toBe(84532);
  });

  it("throws when createRecord returns success=false", async () => {
    const createRecord = vi.fn(async () => ({
      success: false,
      data: {uri: "", cid: ""},
    }));
    const agent = {com: {atproto: {repo: {createRecord}}}} as never;
    await expect(
      commitL2Anchor({
        agent,
        repo: "did:test:anchorer",
        ...BASE,
        submit: {
          txHash: TX_HASH,
          blockNumber: 5,
          logIndex: 0,
          alreadyAnchored: false,
        },
      }),
    ).rejects.toThrow(/createRecord failed/);
  });
});
