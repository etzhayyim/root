// Self-certifying DID attestation tests (ADR-2606015600): did:key roundtrip +
// the full sign→verify loop (an actor's own ed25519 key signs its did.json CID;
// verification is self-certifying — the key is the did:key in the proof).
//   node --experimental-strip-types --test scripts/diddoc-attest.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  verifyDidDocAttestation,
  ed25519PubToDidKey,
  didKeyToEd25519Pub,
  base58btcEncode,
  base58btcDecode,
} from "../src/diddoc-attest.ts";
import { ed25519Key, signDidDocAttestation } from "./sign-diddoc.mjs";

const DID = "did:web:etzhayyim.com:actor:kanae";
const CID = "bafkreiboag3o3axk6z43mme3tmwqz2d7humzw7lhotygxzutoslfp5lw2y";
const payload = { did: DID, didDocCid: CID, signedAt: "2026-06-02T00:00:00.000Z", sequence: 1 };

test("base58btc + did:key roundtrip", async () => {
  const { pubRaw } = await ed25519Key();
  const dk = ed25519PubToDidKey(pubRaw);
  assert.match(dk, /^did:key:z6Mk/); // ed25519 did:key always starts z6Mk
  assert.deepEqual([...didKeyToEd25519Pub(dk)], [...pubRaw]);
  // base58 roundtrip
  const b = new Uint8Array([0, 0, 1, 2, 255, 254]);
  assert.deepEqual([...base58btcDecode(base58btcEncode(b))], [...b]);
});

test("sign → verify is valid + self-certifying (key from the proof)", async () => {
  const { priv, pubRaw } = await ed25519Key();
  const att = await signDidDocAttestation(payload, priv, pubRaw);
  assert.equal(att.proof.verificationMethod, ed25519PubToDidKey(pubRaw));
  const r = await verifyDidDocAttestation(att);
  assert.equal(r.valid, true, r.reason);
  assert.equal(r.did, DID);
  assert.equal(r.didDocCid, CID);
});

test("verify binds the signed CID (expectedDidDocCid)", async () => {
  const { priv, pubRaw } = await ed25519Key();
  const att = await signDidDocAttestation(payload, priv, pubRaw);
  assert.equal((await verifyDidDocAttestation(att, CID)).valid, true);
  const bad = await verifyDidDocAttestation(att, "bafkrei" + "a".repeat(52));
  assert.equal(bad.valid, false);
  assert.equal(bad.reason, "didDocCid mismatch");
});

test("tampered payload is REJECTED (signature no longer matches)", async () => {
  const { priv, pubRaw } = await ed25519Key();
  const att = await signDidDocAttestation(payload, priv, pubRaw);
  const tampered = { ...att, didDocCid: "bafkrei" + "b".repeat(52) };
  assert.equal((await verifyDidDocAttestation(tampered)).valid, false);
});

test("forged signature (other key) is REJECTED", async () => {
  const a = await ed25519Key();
  const b = await ed25519Key();
  const att = await signDidDocAttestation(payload, a.priv, a.pubRaw);
  // claim it was signed by b's key
  const forged = { ...att, proof: { ...att.proof, verificationMethod: ed25519PubToDidKey(b.pubRaw) } };
  assert.equal((await verifyDidDocAttestation(forged)).valid, false);
});
