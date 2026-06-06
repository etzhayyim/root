// Domain-independent identity tests (ADR-2606061800): the self-certifying handle
// attestation. The controller did:key signs `{iss, handle}` as a compact EdDSA
// JWS; the apex verifies it against the key IN the DID — no domain, no TLS. This
// also cross-checks the FRONTEND format (signHandleAttestation in
// $lib/auth/identity.ts) by replicating its exact JWS construction and verifying
// it with the real worker verifier.
//   node --experimental-strip-types --test scripts/identity.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { verifyHandleAttestation, selfCertifyingDidDoc, verifyAccountBlock, parseDidKeyHex } from "../src/identity.ts";

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

// ─── account-block read verification (read side) ─────────────────────────────

/** The `did:key:z`+hex(32B) author form (block.put), SAME key as the z6Mk did. */
async function didHexOf(kp) {
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  return "did:key:z" + Array.from(pub).map((b) => b.toString(16).padStart(2, "0")).join("");
}
async function accountBlock(kp, did, handle, withAttestation = true) {
  const rec = { type: "account/register", "account/did": did, "account/controller": did };
  if (handle) rec["account/handle"] = handle;
  if (handle && withAttestation) rec["account/handle-attestation"] = await signHandleAttestation(kp, did, handle, NOW);
  return new TextEncoder().encode(JSON.stringify(rec));
}

test("parseDidKeyHex: did:key:z + 64 hex → 32-byte pubkey; rejects non-hex/wrong-len", () => {
  const pub = parseDidKeyHex("did:key:z" + "ab".repeat(32));
  assert.equal(pub.length, 32);
  assert.equal(pub[0], 0xab);
  assert.throws(() => parseDidKeyHex("did:key:z6MkBase58Form"));
  assert.throws(() => parseDidKeyHex("did:key:z" + "ab".repeat(31)));
});

test("verifyAccountBlock: valid block (author≡account/did, attested handle) → valid", async () => {
  const { kp, did } = await genKey();
  const block = await accountBlock(kp, did, "alice");
  const r = await verifyAccountBlock(block, await didHexOf(kp), NOW + 60);
  assert.equal(r.valid, true);
  assert.equal(r.did, did);
  assert.equal(r.handle, "alice");
});

test("verifyAccountBlock: block author key ≠ account/did key is rejected (no claiming another's did)", async () => {
  const alice = await genKey();
  const mallory = await genKey();
  // mallory authors a block claiming alice's account/did
  const block = await accountBlock(alice.kp, alice.did, "alice"); // record claims alice
  const r = await verifyAccountBlock(block, await didHexOf(mallory.kp), NOW + 60); // but author is mallory
  assert.equal(r.valid, false);
  assert.match(r.reason, /author key ≠ account\/did|not this account/i);
});

test("verifyAccountBlock: handle present but missing/forged attestation is rejected", async () => {
  const { kp, did } = await genKey();
  const noAtt = await accountBlock(kp, did, "alice", false);
  assert.equal((await verifyAccountBlock(noAtt, await didHexOf(kp), NOW + 60)).valid, false);
  // forged: attestation for a DIFFERENT handle
  const rec = { "account/did": did, "account/handle": "alice", "account/handle-attestation": await signHandleAttestation(kp, did, "not-alice", NOW) };
  const forged = new TextEncoder().encode(JSON.stringify(rec));
  assert.equal((await verifyAccountBlock(forged, await didHexOf(kp), NOW + 60)).valid, false);
});

test("verifyAccountBlock: handle-less record (no name claim) is valid if author≡did", async () => {
  const { kp, did } = await genKey();
  const block = await accountBlock(kp, did, null);
  const r = await verifyAccountBlock(block, await didHexOf(kp), NOW + 60);
  assert.equal(r.valid, true);
  assert.equal(r.handle, undefined);
});

test("verifyAccountBlock: non-JSON / missing account/did rejected", async () => {
  const { kp } = await genKey();
  assert.equal((await verifyAccountBlock(new TextEncoder().encode("not json"), await didHexOf(kp), NOW)).valid, false);
  assert.equal((await verifyAccountBlock(new TextEncoder().encode("{}"), await didHexOf(kp), NOW)).valid, false);
});
