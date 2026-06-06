// Block CID cross-impl invariant (ADR-2606061800): the FRONTEND block-publish
// CID (what the member signs + sends to block.put) MUST equal the APEX/IPFS CID
// (what block.put + the consumer + kotobase.net pin re-verify). If these ever
// diverge, every member-signed account block would fail verification. This pins
// frontend `cidV1` == apex `cidV1Raw` byte-for-byte, plus the did:key:z+hex /
// account-graph derivations block.put expects.
//   node --experimental-strip-types --test scripts/block-cid-compat.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { cidV1Raw, isRawCidV1 } from "../src/cid.ts";
import {
  cidV1 as feCidV1,
  didKeyHex,
  accountGraph,
} from "../../../60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/block-publish.ts";

const CASES = [
  new TextEncoder().encode(""),
  new TextEncoder().encode("a"),
  new TextEncoder().encode(JSON.stringify({ type: "account/register", "account/handle": "alice" })),
  new TextEncoder().encode("x".repeat(1000)),
  Uint8Array.from({ length: 256 }, (_, i) => i & 0xff),
];

test("frontend cidV1 == apex cidV1Raw (the block.put/IPFS verification invariant)", async () => {
  for (const bytes of CASES) {
    const fe = (await feCidV1(bytes)).str;
    const apex = await cidV1Raw(bytes);
    assert.equal(fe, apex, `CID mismatch for ${bytes.length}-byte input`);
    assert.ok(fe.startsWith("bafkrei"), `expected raw sha2-256 CIDv1 (bafkrei…), got ${fe}`);
    assert.equal(isRawCidV1(fe), true, "apex must recognize its own CID form");
  }
});

test("frontend cidV1 .bytes is the 36-byte CID (01 55 12 20 + 32-byte sha256)", async () => {
  const { bytes } = await feCidV1(new TextEncoder().encode("hello"));
  assert.equal(bytes.length, 36);
  assert.deepEqual([...bytes.slice(0, 4)], [0x01, 0x55, 0x12, 0x20]);
});

test("didKeyHex: did:key:z + 64 hex chars (the block.put author form)", () => {
  const pub = Uint8Array.from({ length: 32 }, (_, i) => (i * 7) & 0xff);
  const sk = { privateKey: {}, publicKey: pub, publicKeyMultibase: "", didKey: "did:key:z6Mk…" };
  const d = didKeyHex(sk);
  assert.match(d, /^did:key:z[0-9a-f]{64}$/, "did:key:z + hex(32B pubkey)");
  // deterministic
  assert.equal(didKeyHex(sk), d);
});

test("accountGraph: per-member graph acct-<pubkeyHex> (no cross-member contention)", () => {
  const a = { publicKey: Uint8Array.from({ length: 32 }, () => 0xaa) };
  const b = { publicKey: Uint8Array.from({ length: 32 }, () => 0xbb) };
  assert.match(accountGraph(a), /^acct-[0-9a-f]{64}$/);
  assert.notEqual(accountGraph(a), accountGraph(b), "distinct members → distinct graphs");
});

test("signature is over the raw 36-byte CID bytes, not the hash (block.put verifyRootSig)", async () => {
  // documents the contract: block.put base32-decodes root.slice(1) → the 36 CID
  // bytes → verifies the member sig over THOSE bytes (see kotoba-publish.ts).
  const { bytes } = await feCidV1(new TextEncoder().encode("sig-target"));
  assert.equal(bytes.length, 36, "the signed message is the full CID (36B), not the 32B digest");
});
