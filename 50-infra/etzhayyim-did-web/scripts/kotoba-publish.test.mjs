// Tests for the kotoba member-signed publish crypto (the most fragile new code:
// the custom did:key format + base32 CID decode + ed25519 verify). Run via:
//   node --experimental-strip-types --test scripts/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { base32Decode, verifyRootSig, ipPrefix } from "../src/kotoba-publish.ts";

const B32 = "abcdefghijklmnopqrstuvwxyz234567";
function base32Encode(bytes) {
  let bits = 0,
    value = 0,
    out = "";
  for (const b of bytes) {
    value = (value << 8) | b;
    bits += 8;
    while (bits >= 5) {
      out += B32[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) out += B32[(value << (5 - bits)) & 31];
  return out;
}
const hex = (b) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");

// Build a CIDv1 dag-cbor sha2-256 (0x01 0x71 0x12 0x20 + 32-byte digest) the way
// kotoba does, and its multibase 'b'+base32 form (== KotobaCid::to_multibase).
function makeRoot(digest32) {
  const cidBytes = new Uint8Array(36);
  cidBytes.set([0x01, 0x71, 0x12, 0x20], 0);
  cidBytes.set(digest32, 4);
  return { cidBytes, multibase: "b" + base32Encode(cidBytes) };
}

test("base32Decode round-trips a 36-byte CID", () => {
  const digest = crypto.getRandomValues(new Uint8Array(32));
  const { cidBytes, multibase } = makeRoot(digest);
  const decoded = base32Decode(multibase.slice(1));
  assert.equal(decoded.length, 36);
  assert.deepEqual(Array.from(decoded), Array.from(cidBytes));
  assert.deepEqual(Array.from(decoded.slice(0, 4)), [0x01, 0x71, 0x12, 0x20]);
});

test("ipPrefix coarsens IPv4 /24, IPv6 /48, empty", () => {
  assert.equal(ipPrefix("203.0.113.45"), "203.0.113.0/24");
  assert.equal(ipPrefix("2001:db8:abcd:1234::1"), "2001:db8:abcd::/48");
  assert.equal(ipPrefix(""), "");
});

test("verifyRootSig accepts a valid wasm-style ed25519 signature", async () => {
  // Mirror kotoba-wasm WriteCrypto: did = did:key:z + hex(pubkey); sign root.0.
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const did = "did:key:z" + hex(pub);
  const { cidBytes, multibase } = makeRoot(crypto.getRandomValues(new Uint8Array(32)));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, cidBytes));
  assert.equal(await verifyRootSig(did, multibase, hex(sig)), true);
});

test("verifyRootSig rejects tampering and malformed inputs", async () => {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const did = "did:key:z" + hex(pub);
  const { cidBytes, multibase } = makeRoot(crypto.getRandomValues(new Uint8Array(32)));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, cidBytes));

  // flipped signature byte
  const bad = Uint8Array.from(sig);
  bad[0] ^= 0xff;
  assert.equal(await verifyRootSig(did, multibase, hex(bad)), false, "tampered sig");

  // wrong signer (different key, same root+sig)
  const kp2 = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pub2 = new Uint8Array(await crypto.subtle.exportKey("raw", kp2.publicKey));
  assert.equal(await verifyRootSig("did:key:z" + hex(pub2), multibase, hex(sig)), false, "wrong key");

  // signature over a different root
  const other = makeRoot(crypto.getRandomValues(new Uint8Array(32)));
  assert.equal(await verifyRootSig(did, other.multibase, hex(sig)), false, "wrong root");

  // malformed shapes
  assert.equal(await verifyRootSig("did:web:nope", multibase, hex(sig)), false, "not did:key");
  assert.equal(await verifyRootSig(did, "znotmultibase", hex(sig)), false, "bad multibase prefix");
  assert.equal(await verifyRootSig(did, multibase, "00"), false, "short sig");
});
