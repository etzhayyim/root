// registerAccount relay unit tests (ADR-2606061800): the same-origin account
// publish. A member proves control of their controller did:key with a CACAO
// carrying the `account:register` capability; the Worker verifies it (no server
// key) and relays the handle↔did:key alias to kotoba via an injected writer.
//   node --experimental-strip-types --test scripts/register-account.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { siweMessage } from "../src/cacao.ts";
import { handleRegisterAccount } from "../src/session.ts";

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
async function genKeyAndDid() {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const raw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  return { privateKey: kp.privateKey, did: didKeyFromEd25519Pub(raw) };
}
function registerCacao(did, overrides = {}) {
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
      resources: ["kotoba://op/account:register"],
      ...overrides,
    },
    s: { t: "EdDSA", s: "" },
  };
}
async function signEdDSA(cacao, privateKey) {
  const msg = new TextEncoder().encode(siweMessage(cacao));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, privateKey, msg));
  return { ...cacao, s: { t: "EdDSA", s: bytesToHex(sig) } };
}
const NOW = Date.parse("2026-06-06T12:00:00Z");
const writeOk = async () => "written";
const writeGated = async () => "gated";
const writeErr = async () => "error";

test("registerAccount: happy path → 200 ok with did+handle, writer invoked", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(registerCacao(did), privateKey);
  let seen = null;
  const writer = async (d, h, p) => {
    seen = { d, h, p };
    return "written";
  };
  const { status, result } = await handleRegisterAccount(
    { cacao: signed, handle: "alice", did, profile: { displayName: "alice" } },
    NOW,
    writer,
  );
  assert.equal(status, 200);
  assert.equal(result.ok, true);
  assert.equal(result.did, did);
  assert.equal(result.handle, "alice");
  assert.deepEqual(seen, { d: did, h: "alice", p: { displayName: "alice" } });
});

test("registerAccount: missing cacao → 400", async () => {
  const { status, result } = await handleRegisterAccount({ handle: "x" }, NOW, writeOk);
  assert.equal(status, 400);
  assert.equal(result.ok, false);
});

test("registerAccount: CACAO bound to another origin → 403", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(
    registerCacao(did, { aud: "did:web:evil.example", domain: "evil.example" }),
    privateKey,
  );
  const { status, result } = await handleRegisterAccount({ cacao: signed, did }, NOW, writeOk);
  assert.equal(status, 403);
  assert.equal(result.ok, false);
});

test("registerAccount: missing account:register capability → 400", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(
    registerCacao(did, { resources: ["kotoba://op/datom:read"] }),
    privateKey,
  );
  const { status, result } = await handleRegisterAccount({ cacao: signed, did }, NOW, writeOk);
  assert.equal(status, 400);
  assert.match(result.reason, /account:register/);
});

test("registerAccount: bad signature → 401 (no write)", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(registerCacao(did), privateKey);
  signed.s.s = "00".repeat(64); // tamper
  let called = false;
  const writer = async () => {
    called = true;
    return "written";
  };
  const { status, result } = await handleRegisterAccount({ cacao: signed, did }, NOW, writer);
  assert.equal(status, 401);
  assert.equal(result.ok, false);
  assert.equal(called, false);
});

test("registerAccount: body.did mismatch → 400 (no write)", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const other = await genKeyAndDid();
  const signed = await signEdDSA(registerCacao(did), privateKey);
  let called = false;
  const writer = async () => {
    called = true;
    return "written";
  };
  const { status, result } = await handleRegisterAccount(
    { cacao: signed, did: other.did },
    NOW,
    writer,
  );
  assert.equal(status, 400);
  assert.equal(result.ok, false);
  assert.equal(called, false);
});

test("registerAccount: kotoba write gated → 202 gated (control proven, not published)", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(registerCacao(did), privateKey);
  const { status, result } = await handleRegisterAccount({ cacao: signed, did }, NOW, writeGated);
  assert.equal(status, 202);
  assert.equal(result.ok, false);
  assert.equal(result.gated, true);
  assert.equal(result.did, did);
});

test("registerAccount: kotoba write error → 502", async () => {
  const { privateKey, did } = await genKeyAndDid();
  const signed = await signEdDSA(registerCacao(did), privateKey);
  const { status, result } = await handleRegisterAccount({ cacao: signed, did }, NOW, writeErr);
  assert.equal(status, 502);
  assert.equal(result.ok, false);
});
