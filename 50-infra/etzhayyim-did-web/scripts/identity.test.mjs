// Domain-independent identity tests (ADR-2606061800): the self-certifying handle
// attestation. The controller did:key signs `{iss, handle}` as a compact EdDSA
// JWS; the apex verifies it against the key IN the DID — no domain, no TLS. This
// also cross-checks the FRONTEND format (signHandleAttestation in
// $lib/auth/identity.ts) by replicating its exact JWS construction and verifying
// it with the real worker verifier.
//   node --experimental-strip-types --test scripts/identity.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { verifyHandleAttestation, selfCertifyingDidDoc } from "../src/identity.ts";

const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function b58(bytes) {
  let z = 0;
  while (z < bytes.length && bytes[z] === 0) z++;
  const d = [];
  for (let i = z; i < bytes.length; i++) {
    let c = bytes[i];
    for (let j = 0; j < d.length; j++) {
      c += d[j] << 8;
      d[j] = c % 58;
      c = (c / 58) | 0;
    }
    while (c > 0) {
      d.push(c % 58);
      c = (c / 58) | 0;
    }
  }
  let o = "1".repeat(z);
  for (let i = d.length - 1; i >= 0; i--) o += B58[d[i]];
  return o;
}
function b64url(bytes) {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
function jsonB64url(o) {
  return b64url(new TextEncoder().encode(JSON.stringify(o)));
}
async function genKey() {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const pre = new Uint8Array(34);
  pre.set([0xed, 0x01]);
  pre.set(pub, 2);
  return { kp, did: "did:key:z" + b58(pre) };
}
// EXACT mirror of $lib/auth/identity.ts signHandleAttestation
async function signHandleAttestation(kp, did, handle, iat, exp) {
  const header = { alg: "EdDSA", typ: "handle-attest+jwt" };
  const payload = { iss: did, sub: did, handle, iat };
  if (exp !== undefined) payload.exp = exp;
  const signingInput = `${jsonB64url(header)}.${jsonB64url(payload)}`;
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, new TextEncoder().encode(signingInput)));
  return `${signingInput}.${b64url(sig)}`;
}
const NOW = 1780000000;

test("frontend handle attestation verifies on the worker (self-certifying, no domain)", async () => {
  const { kp, did } = await genKey();
  const jws = await signHandleAttestation(kp, did, "alice", NOW);
  const r = await verifyHandleAttestation(jws, NOW + 60);
  assert.equal(r.valid, true);
  assert.equal(r.did, did);
  assert.equal(r.handle, "alice");
});

test("tampered handle is rejected (signature no longer matches)", async () => {
  const { kp, did } = await genKey();
  const jws = await signHandleAttestation(kp, did, "alice", NOW);
  const [h, , s] = jws.split(".");
  const forgedPayload = jsonB64url({ iss: did, sub: did, handle: "attacker", iat: NOW });
  const r = await verifyHandleAttestation(`${h}.${forgedPayload}.${s}`, NOW + 60);
  assert.equal(r.valid, false);
});

test("attestation signed by a DIFFERENT key (claiming someone else's did) is rejected", async () => {
  const victim = await genKey();
  const attacker = await genKey();
  // attacker signs a JWS that claims iss = victim.did
  const jws = await signHandleAttestation(attacker.kp, victim.did, "victim-handle", NOW);
  const r = await verifyHandleAttestation(jws, NOW + 60);
  assert.equal(r.valid, false, "must reject — not signed by the claimed did:key");
});

test("expired attestation is rejected", async () => {
  const { kp, did } = await genKey();
  const jws = await signHandleAttestation(kp, did, "alice", NOW, NOW + 10);
  const r = await verifyHandleAttestation(jws, NOW + 1000);
  assert.equal(r.valid, false);
  assert.match(r.reason, /expired/);
});

test("non-EdDSA / malformed JWS is rejected", async () => {
  assert.equal((await verifyHandleAttestation("not.a.jws.too.many", NOW)).valid, false);
  assert.equal((await verifyHandleAttestation("only.two", NOW)).valid, false);
  assert.equal((await verifyHandleAttestation(42, NOW)).valid, false);
});

test("sub must equal iss (no third-party attestation)", async () => {
  const { kp, did } = await genKey();
  const header = { alg: "EdDSA", typ: "handle-attest+jwt" };
  const payload = { iss: did, sub: "did:key:zOTHER", handle: "x", iat: NOW };
  const signingInput = `${jsonB64url(header)}.${jsonB64url(payload)}`;
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, new TextEncoder().encode(signingInput)));
  const r = await verifyHandleAttestation(`${signingInput}.${b64url(sig)}`, NOW + 60);
  assert.equal(r.valid, false);
});

test("selfCertifyingDidDoc: id is the did:key; did:web is only an alsoKnownAs alias", async () => {
  const { did } = await genKey();
  const doc = selfCertifyingDidDoc(did, "alice");
  assert.equal(doc.id, did, "canonical id is the did:key, NOT did:web");
  assert.ok(doc.alsoKnownAs.includes("did:web:etzhayyim.com:alice"), "did:web is a non-authoritative alias");
  assert.equal(doc.verificationMethod[0].controller, did);
  // a domain change cannot forge identity: trust roots in the did:key, the
  // alias is just one resolution endpoint.
});
