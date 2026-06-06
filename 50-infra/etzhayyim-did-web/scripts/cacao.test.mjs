// CACAO verify-only unit tests (ADR-2606060000): the `/profile` same-origin
// auth gate. Ed25519 (passkey/did:key) is verified LOCALLY with WebCrypto, so
// these are real end-to-end signature checks — generate a key, sign the SIWE
// plaintext, verify; tamper / expiry / cross-origin / eip191-gated all asserted.
//   node --experimental-strip-types --test scripts/cacao.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  base58btcDecode,
  parseEd25519DidKey,
  siweMessage,
  isExpired,
  isStrictUtcIso8601,
  verifyCacao,
} from "../src/cacao.ts";
import { handleVerifyCacao } from "../src/session.ts";

// ── base58btc encode (test helper; module only needs decode) ────────────────
const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function base58btcEncode(bytes) {
  const digits = [0];
  for (const b of bytes) {
    let carry = b;
    for (let j = 0; j < digits.length; j += 1) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = (carry / 58) | 0;
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = (carry / 58) | 0;
    }
  }
  let out = "";
  for (let k = 0; k < bytes.length && bytes[k] === 0; k += 1) out += "1";
  for (let i = digits.length - 1; i >= 0; i -= 1) out += B58[digits[i]];
  return out;
}

function bytesToHex(bytes) {
  let out = "";
  for (const b of bytes) out += b.toString(16).padStart(2, "0");
  return out;
}

function didKeyFromEd25519Pub(raw) {
  const prefixed = new Uint8Array(2 + raw.length);
  prefixed[0] = 0xed;
  prefixed[1] = 0x01;
  prefixed.set(raw, 2);
  return "did:key:z" + base58btcEncode(prefixed);
}

// Generate an Ed25519 keypair + the did:key for it.
async function genKeyAndDid() {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, [
    "sign",
    "verify",
  ]);
  const raw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  return { privateKey: kp.privateKey, did: didKeyFromEd25519Pub(raw) };
}

function baseCacao(did, overrides = {}) {
  return {
    h: { t: "eip4361" },
    p: {
      iss: did,
      aud: "did:web:etzhayyim.com",
      iat: "2026-06-06T00:00:00Z",
      exp: "2099-01-01T00:00:00Z",
      nonce: "0123456789abcdef",
      domain: "etzhayyim.com",
      version: "1",
      resources: [
        "kotoba://op/datom:transact",
        "kotoba://graph/bafyreigh2akiscaildc",
      ],
      ...overrides,
    },
    s: { t: "EdDSA", s: "" },
  };
}

async function signEdDSA(cacao, privateKey) {
  const msg = new TextEncoder().encode(siweMessage(cacao));
  const sig = new Uint8Array(
    await crypto.subtle.sign({ name: "Ed25519" }, privateKey, msg),
  );
  return { ...cacao, s: { t: "EdDSA", s: bytesToHex(sig) } };
}

const NOW = Date.parse("2026-06-06T12:00:00Z");

// ── base58 + did:key ────────────────────────────────────────────────────────
test("base58btc decode round-trips a known did:key pub", () => {
  const raw = new Uint8Array(32).fill(7);
  const did = didKeyFromEd25519Pub(raw);
  const decoded = parseEd25519DidKey(did);
  assert.equal(bytesToHex(decoded), bytesToHex(raw));
});

test("parseEd25519DidKey rejects non-ed25519 / non-base58 dids", () => {
  assert.throws(() => parseEd25519DidKey("did:web:etzhayyim.com"));
  assert.throws(() => parseEd25519DidKey("did:key:z" + "0".repeat(4)));
});

test("base58btcDecode rejects an invalid alphabet char", () => {
  assert.throws(() => base58btcDecode("0OIl")); // none are in the alphabet
});

// ── strict UTC + expiry ─────────────────────────────────────────────────────
test("isStrictUtcIso8601 accepts Z form, rejects offset/space", () => {
  assert.equal(isStrictUtcIso8601("2026-06-06T00:00:00Z"), true);
  assert.equal(isStrictUtcIso8601("2026-06-06T00:00:00.500Z"), true);
  assert.equal(isStrictUtcIso8601("2026-06-06T00:00:00+09:00"), false);
  assert.equal(isStrictUtcIso8601("2026-06-06 00:00:00Z"), false);
});

test("isExpired: no exp = never; malformed exp = fail-safe expired", () => {
  const did = "did:key:zXX";
  assert.equal(isExpired(baseCacao(did, { exp: undefined }), NOW), false);
  assert.equal(isExpired(baseCacao(did, { exp: "garbage" }), NOW), true);
  assert.equal(isExpired(baseCacao(did, { exp: "2020-01-01T00:00:00Z" }), NOW), true);
  assert.equal(isExpired(baseCacao(did, { exp: "2099-01-01T00:00:00Z" }), NOW), false);
});

// ── SIWE message reconstruction ─────────────────────────────────────────────
test("siweMessage matches the kotoba-auth canonical layout", () => {
  const c = baseCacao("did:key:z6MkExample", { statement: "Sign in to etzhayyim" });
  const msg = siweMessage(c);
  assert.match(msg, /^etzhayyim\.com wants you to sign in with your Ethereum account:\n/);
  assert.match(msg, /\nURI: did:web:etzhayyim\.com\n/);
  assert.match(msg, /\nChain ID: 1\n/); // did:key → CAIP-122 default
  assert.match(msg, /\nResources:\n- kotoba:\/\/op\/datom:transact\n- kotoba:\/\/graph\//);
  assert.match(msg, /\nSign in to etzhayyim\n/);
});

// ── Ed25519 verify (real WebCrypto) ─────────────────────────────────────────
test("verifyCacao: valid Ed25519 CACAO verifies and returns the issuer DID", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(baseCacao(did), privateKey);
  const out = await verifyCacao(signed, NOW);
  assert.equal(out.valid, true);
  assert.equal(out.did, did);
  assert.equal(out.method, "ed25519-local");
});

test("verifyCacao: tampered payload fails signature", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(baseCacao(did), privateKey);
  // mutate the nonce AFTER signing → SIWE plaintext changes → verify must fail
  const tampered = { ...signed, p: { ...signed.p, nonce: "ffffffffffffffff" } };
  const out = await verifyCacao(tampered, NOW);
  assert.equal(out.valid, false);
  assert.match(out.reason, /mismatch/);
});

test("verifyCacao: expired CACAO is rejected before signature work", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(baseCacao(did, { exp: "2020-01-01T00:00:00Z" }), privateKey);
  const out = await verifyCacao(signed, NOW);
  assert.equal(out.valid, false);
  assert.match(out.reason, /expired/);
});

test("verifyCacao: wrong key cannot impersonate another did:key", async () => {
  const a = await genKeyAndDid();
  const b = await genKeyAndDid();
  // sign with A's key but claim B's DID
  const cacao = baseCacao(b.did);
  const signed = await signEdDSA(cacao, a.privateKey);
  const out = await verifyCacao(signed, NOW);
  assert.equal(out.valid, false);
});

test("verifyCacao: eip191 is structurally validated then gated", async () => {
  const c = {
    h: { t: "eip4361" },
    p: {
      iss: "did:pkh:eip155:8453:0x1111111111111111111111111111111111111111",
      aud: "did:web:etzhayyim.com",
      iat: "2026-06-06T00:00:00Z",
      exp: "2099-01-01T00:00:00Z",
      nonce: "abc",
      domain: "etzhayyim.com",
      resources: ["kotoba://op/datom:transact"],
    },
    s: { t: "eip191", s: "0x" + "11".repeat(65) },
  };
  const out = await verifyCacao(c, NOW);
  assert.equal(out.valid, false);
  assert.equal(out.gated, true);
  assert.equal(out.sigType, "eip191");
});

// ── session handler (audience/domain binding + scope) ───────────────────────
test("handleVerifyCacao: happy path → 200 + scope", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(baseCacao(did), privateKey);
  const { status, result } = await handleVerifyCacao({ cacao: signed }, NOW);
  assert.equal(status, 200);
  assert.equal(result.valid, true);
  assert.equal(result.did, did);
  assert.deepEqual(result.scope.capabilities, ["kotoba://op/datom:transact"]);
  assert.equal(result.scope.graphs.length, 1);
});

test("handleVerifyCacao: CACAO bound to another origin is 403", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(
    baseCacao(did, { aud: "did:web:evil.example", domain: "evil.example" }),
    privateKey,
  );
  const { status, result } = await handleVerifyCacao({ cacao: signed }, NOW);
  assert.equal(status, 403);
  assert.equal(result.valid, false);
});

test("handleVerifyCacao: no capability resource is 400", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(
    baseCacao(did, { resources: ["kotoba://graph/bafyreigh2akiscaildc"] }),
    privateKey,
  );
  const { status, result } = await handleVerifyCacao({ cacao: signed }, NOW);
  assert.equal(status, 400);
  assert.match(result.reason, /no kotoba:\/\/op/);
});

test("handleVerifyCacao: missing cacao is 400", async () => {
  const { status, result } = await handleVerifyCacao({}, NOW);
  assert.equal(status, 400);
  assert.equal(result.valid, false);
});

test("handleVerifyCacao: eip191 → 202 gated (honest, not a false session)", async () => {
  const c = {
    h: { t: "eip4361" },
    p: {
      iss: "did:pkh:eip155:8453:0x1111111111111111111111111111111111111111",
      aud: "did:web:etzhayyim.com",
      iat: "2026-06-06T00:00:00Z",
      exp: "2099-01-01T00:00:00Z",
      nonce: "abc",
      domain: "etzhayyim.com",
      resources: ["kotoba://op/datom:transact"],
    },
    s: { t: "eip191", s: "0x" + "11".repeat(65) },
  };
  const { status, result } = await handleVerifyCacao({ cacao: c }, NOW);
  assert.equal(status, 202);
  assert.equal(result.gated, true);
});
