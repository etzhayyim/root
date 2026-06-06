// Cross-implementation compat test (ADR-2606061800): proves the FRONTEND
// same-origin login artifact verifies on the WORKER verifier. It re-derives the
// passkey→did:key exactly as the browser does (PRF secret = ARK →
// HKDF-SHA256(salt=0³², info="kotoba/session/sign/v1") → Ed25519 → did:key),
// signs a CAP_ACCOUNT_LOGIN CACAO over the byte-identical SIWE plaintext, and
// runs it through the real `handleVerifyCacao`. Also checks the P-256 fallback
// did:key encoding (compress + p256-pub multicodec 0x1200 + base58btc).
//   node --experimental-strip-types --test scripts/same-origin-login-compat.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { siweMessage, parseEd25519DidKey } from "../src/cacao.ts";
import { handleVerifyCacao } from "../src/session.ts";

const NOW = Date.parse("2026-06-06T12:00:00Z");

// ── base58btc (matches session-key.ts base58btcEncode / cacao.ts decode) ────
const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function base58btcEncode(bytes) {
  let zeros = 0;
  while (zeros < bytes.length && bytes[zeros] === 0) zeros++;
  const digits = [];
  for (let i = zeros; i < bytes.length; i++) {
    let carry = bytes[i];
    for (let j = 0; j < digits.length; j++) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = (carry / 58) | 0;
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = (carry / 58) | 0;
    }
  }
  let out = "1".repeat(zeros);
  for (let i = digits.length - 1; i >= 0; i--) out += B58[digits[i]];
  return out;
}
function bytesToHex(b) {
  let o = "";
  for (const x of b) o += x.toString(16).padStart(2, "0");
  return o;
}

// ── client key derivation (mirror of key-tree.ts + session-key.ts) ──────────
const PKCS8_ED25519_PREFIX = Uint8Array.from([
  0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20,
]);
async function hkdf32(ikm, label) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "HKDF", hash: "SHA-256", salt: new Uint8Array(32), info: new TextEncoder().encode(label) },
    key,
    256,
  );
  return new Uint8Array(bits);
}
/** PRF secret (= ARK) → Ed25519 session key → did:key, exactly as the browser. */
async function deriveDidKeyFromPrf(prfSecret) {
  const seed = await hkdf32(prfSecret, "kotoba/session/sign/v1");
  const pkcs8 = new Uint8Array(PKCS8_ED25519_PREFIX.length + 32);
  pkcs8.set(PKCS8_ED25519_PREFIX);
  pkcs8.set(seed, PKCS8_ED25519_PREFIX.length);
  const priv = await crypto.subtle.importKey("pkcs8", pkcs8, { name: "Ed25519" }, true, ["sign"]);
  const jwk = await crypto.subtle.exportKey("jwk", priv);
  const pub = Uint8Array.from(atob(jwk.x.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
  const prefixed = new Uint8Array(2 + pub.length);
  prefixed.set([0xed, 0x01]);
  prefixed.set(pub, 2);
  return { privateKey: priv, didKey: "did:key:z" + base58btcEncode(prefixed) };
}

// ── client CACAO builder/signer (mirror of frontend cacao.ts) ───────────────
function buildLoginCacao(did) {
  return {
    h: { t: "eip4361" },
    p: {
      iss: did,
      aud: "did:web:etzhayyim.com",
      iat: "2026-06-06T11:59:00Z",
      exp: "2026-06-06T12:04:00Z",
      nonce: "deadbeefdeadbeef",
      domain: "etzhayyim.com",
      statement: "Sign in to etzhayyim",
      version: "1",
      resources: ["kotoba://op/account:login"],
    },
    s: { t: "", s: "" },
  };
}
async function signEdDSA(cacao, privateKey) {
  const msg = new TextEncoder().encode(siweMessage(cacao));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, privateKey, msg));
  return { ...cacao, s: { t: "EdDSA", s: bytesToHex(sig) } };
}

test("PRF→did:key is deterministic (same passkey ⇒ same DID, no server store)", async () => {
  const prf = new Uint8Array(32).fill(0x11);
  const a = await deriveDidKeyFromPrf(prf);
  const b = await deriveDidKeyFromPrf(prf);
  assert.equal(a.didKey, b.didKey);
  assert.match(a.didKey, /^did:key:z6Mk/); // ed25519-pub multibase prefix
  // a different PRF ⇒ a different DID
  const c = await deriveDidKeyFromPrf(new Uint8Array(32).fill(0x22));
  assert.notEqual(a.didKey, c.didKey);
});

test("frontend login CACAO (CAP_ACCOUNT_LOGIN) verifies on the worker verifier", async () => {
  const prf = new Uint8Array(32).fill(0x42);
  const { privateKey, didKey } = await deriveDidKeyFromPrf(prf);
  const signed = await signEdDSA(buildLoginCacao(didKey), privateKey);
  const { status, result } = await handleVerifyCacao({ cacao: signed }, NOW);
  assert.equal(status, 200);
  assert.equal(result.valid, true);
  assert.equal(result.did, didKey);
  assert.ok(result.scope.capabilities.includes("kotoba://op/account:login"));
});

test("tampered login CACAO is rejected (401)", async () => {
  const prf = new Uint8Array(32).fill(0x43);
  const { privateKey, didKey } = await deriveDidKeyFromPrf(prf);
  const signed = await signEdDSA(buildLoginCacao(didKey), privateKey);
  signed.p.nonce = "tampered_nonce!!"; // signature no longer matches the message
  const { status, result } = await handleVerifyCacao({ cacao: signed }, NOW);
  assert.equal(status, 401);
  assert.equal(result.valid, false);
});

test("P-256 fallback did:key: compress + 0x1200 multicodec + base58btc round-trips", async () => {
  // mirror deriveDidKeyFromP256 in same-origin-auth.ts
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const raw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey)); // 0x04‖X‖Y (65)
  assert.equal(raw.length, 65);
  assert.equal(raw[0], 0x04);
  const x = raw.slice(1, 33);
  const y = raw.slice(33, 65);
  const compressed = new Uint8Array(33);
  compressed[0] = (y[y.length - 1] & 1) === 0 ? 0x02 : 0x03;
  compressed.set(x, 1);
  const prefixed = new Uint8Array(2 + 33);
  prefixed.set([0x80, 0x24]); // p256-pub multicodec varint
  prefixed.set(compressed, 2);
  const did = "did:key:z" + base58btcEncode(prefixed);
  assert.match(did, /^did:key:zDn/); // p256-pub multibase prefix
  // it must NOT parse as an ed25519 did:key (distinct key type)
  assert.throws(() => parseEd25519DidKey(did));
});
