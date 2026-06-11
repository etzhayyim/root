// pqh-v1 dual-proof attestation tests (ADR-2606111300): ML-DSA-65 multikey
// roundtrip + AND-composed verify (Ed25519 + ML-DSA over the same bytes) +
// downgrade-stripping fails closed under requirePq.
//   node --experimental-strip-types --test scripts/diddoc-attest-pq.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  verifyDidDocAttestation,
  mlDsa65PubToDidKey,
  didKeyToMlDsa65Pub,
} from "../src/diddoc-attest.ts";
import { ed25519Key, mlDsa65Key, signDidDocAttestation } from "./sign-diddoc.mjs";

const payload = {
  did: "did:web:etzhayyim.com:actor:kanae",
  didDocCid: "bafkreigh2akiscaildcqabsyg3dfr6chu3fgpregiymsck7e7aqa4s52zy",
  signedAt: "2026-06-11T00:00:00.000Z",
  sequence: 7,
};

test("ml-dsa-65 multikey did:key roundtrip", () => {
  const pq = mlDsa65Key();
  const didKey = mlDsa65PubToDidKey(pq.publicKey);
  assert.ok(didKey.startsWith("did:key:z"));
  assert.deepEqual(didKeyToMlDsa65Pub(didKey), pq.publicKey);
  // an ed25519 did:key must NOT decode as ml-dsa
  assert.throws(() => didKeyToMlDsa65Pub("did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"));
});

test("dual-signed attestation verifies (Ed25519 AND ML-DSA-65)", async () => {
  const ed = await ed25519Key();
  const pq = mlDsa65Key();
  const att = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, pq);
  assert.equal(att.pqProof.type, "MlDsa65Signature2026");

  const res = await verifyDidDocAttestation(att, payload.didDocCid, { requirePq: true });
  assert.equal(res.valid, true, res.reason);
});

test("stripping pqProof fails closed under requirePq, passes legacy verifier", async () => {
  const ed = await ed25519Key();
  const pq = mlDsa65Key();
  const att = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, pq);
  const { pqProof, ...stripped } = att;

  const strict = await verifyDidDocAttestation(stripped, undefined, { requirePq: true });
  assert.equal(strict.valid, false);
  assert.match(strict.reason, /pqProof required/);

  const legacy = await verifyDidDocAttestation(stripped);
  assert.equal(legacy.valid, true, legacy.reason);
});

test("tampered payload breaks BOTH proofs", async () => {
  const ed = await ed25519Key();
  const pq = mlDsa65Key();
  const att = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, pq);
  const tampered = { ...att, sequence: 8 };
  const res = await verifyDidDocAttestation(tampered);
  assert.equal(res.valid, false);
});

test("a forged pq signature is rejected even with a valid Ed25519 proof", async () => {
  const ed = await ed25519Key();
  const pq = mlDsa65Key();
  const evil = mlDsa65Key();
  const att = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, pq);
  const forged = {
    ...att,
    pqProof: { ...att.pqProof, verificationMethod: mlDsa65PubToDidKey(evil.publicKey) },
  };
  const res = await verifyDidDocAttestation(forged);
  assert.equal(res.valid, false);
  assert.match(res.reason, /bad pq signature/);
});

test("pq key SUBSTITUTION is rejected when the doc-published key is pinned", async () => {
  // The PQ threat model assumes the Ed25519 proof is forgeable, so the
  // attacker re-signs the same payload with their OWN ML-DSA key. Without a
  // pin this self-consistent pqProof verifies; with expectedPqDidKey (from
  // the CID-verified did.json) it must fail.
  const ed = await ed25519Key();
  const real = mlDsa65Key();
  const attacker = mlDsa65Key();
  const realDidKey = mlDsa65PubToDidKey(real.publicKey);

  const substituted = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, attacker);

  const unpinned = await verifyDidDocAttestation(substituted, undefined, { requirePq: true });
  assert.equal(unpinned.valid, true); // self-consistent — why pinning exists

  const pinned = await verifyDidDocAttestation(substituted, undefined, {
    expectedPqDidKey: realDidKey,
  });
  assert.equal(pinned.valid, false);
  assert.match(pinned.reason, /pinned key/);

  const genuine = await signDidDocAttestation(payload, ed.priv, ed.pubRaw, real);
  const ok = await verifyDidDocAttestation(genuine, undefined, { expectedPqDidKey: realDidKey });
  assert.equal(ok.valid, true, ok.reason);
});

test("expectedPqDidKey implies the proof is required (absent → invalid)", async () => {
  const ed = await ed25519Key();
  const real = mlDsa65Key();
  const att = await signDidDocAttestation(payload, ed.priv, ed.pubRaw);
  const res = await verifyDidDocAttestation(att, undefined, {
    expectedPqDidKey: mlDsa65PubToDidKey(real.publicKey),
  });
  assert.equal(res.valid, false);
  assert.match(res.reason, /pqProof required/);
});

test("pq seed is deterministic (same seed → same did:key)", () => {
  const seed = crypto.getRandomValues(new Uint8Array(32));
  const a = mlDsa65Key(new Uint8Array(seed));
  const b = mlDsa65Key(new Uint8Array(seed));
  assert.equal(mlDsa65PubToDidKey(a.publicKey), mlDsa65PubToDidKey(b.publicKey));
});
