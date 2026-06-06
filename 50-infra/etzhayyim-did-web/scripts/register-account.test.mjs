// account-write relay unit tests (ADR-2606061800): the same-origin → kotoba
// relay. A member signs a kotoba-scoped CACAO (aud = node operator_did,
// kotoba://op/datom:transact); the Worker re-encodes it to cacaoB64 (CBOR) and
// forwards an account.<did> entity to kg.ingest. The Worker holds no key and
// does NOT verify the signature (the kotoba node does) — so these tests inject
// the CBOR encoder + the relay and assert shape/capability/claim handling.
//   node --experimental-strip-types --test scripts/register-account.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { handleAccountWrite } from "../src/session.ts";

const OPERATOR_DID = "did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f";
const MEMBER_DID = "did:key:z6MkfE7UHEzqj3AgWKy89G4uZt9Qzh1JfLW3ubVHxg5opmgZ";

// well-formed kotoba-scoped CACAO (signature value is opaque to the Worker)
function kotobaCacao(overrides = {}) {
  return {
    h: { t: "eip4361" },
    p: {
      iss: MEMBER_DID,
      aud: OPERATOR_DID,
      iat: "2026-06-06T12:00:00Z",
      exp: "2026-06-06T12:05:00Z",
      nonce: "deadbeefdeadbeef",
      domain: "etzhayyim.com",
      statement: "Publish your etzhayyim account",
      version: "1",
      resources: ["kotoba://op/datom:transact"],
      ...overrides,
    },
    s: { t: "EdDSA", s: "ZmFrZXNpZw" },
  };
}
const cbor = (c) => `CBOR(${c.p.iss})`; // marker encoder
function recordingRelay(outcome = "written") {
  const calls = [];
  const fn = async (cacaoB64, id, claims, labelEn) => {
    calls.push({ cacaoB64, id, claims, labelEn });
    return outcome;
  };
  fn.calls = calls;
  return fn;
}

test("register happy path → 200, relay gets account.<did> + standard claims", async () => {
  const relay = recordingRelay("written");
  const { status, result } = await handleAccountWrite(
    { cacao: kotobaCacao(), handle: "alice", did: MEMBER_DID, profile: { displayName: "Alice" } },
    cbor,
    relay,
  );
  assert.equal(status, 200);
  assert.equal(result.ok, true);
  assert.equal(result.did, MEMBER_DID);
  assert.equal(relay.calls.length, 1);
  const c = relay.calls[0];
  assert.equal(c.id, `account.${MEMBER_DID}`);
  assert.equal(c.cacaoB64, `CBOR(${MEMBER_DID})`);
  const preds = c.claims.map((x) => x.pred);
  assert.ok(preds.includes("account/did") && preds.includes("account/controller") && preds.includes("account/handle"));
  assert.ok(c.claims.find((x) => x.pred === "account/displayName")?.value === "Alice");
});

test("missing cacao → 400 (no relay)", async () => {
  const relay = recordingRelay();
  const { status } = await handleAccountWrite({ handle: "x" }, cbor, relay);
  assert.equal(status, 400);
  assert.equal(relay.calls.length, 0);
});

test("non-EdDSA CACAO → 400", async () => {
  const c = kotobaCacao();
  c.s.t = "eip191";
  const { status, result } = await handleAccountWrite({ cacao: c }, cbor, recordingRelay());
  assert.equal(status, 400);
  assert.match(result.reason, /EdDSA/);
});

test("CACAO without datom:transact capability → 400", async () => {
  const { status, result } = await handleAccountWrite(
    { cacao: kotobaCacao({ resources: ["kotoba://op/datom:read"] }) },
    cbor,
    recordingRelay(),
  );
  assert.equal(status, 400);
  assert.match(result.reason, /datom:transact/);
});

test("body.did mismatch → 400 (no relay)", async () => {
  const relay = recordingRelay();
  const { status } = await handleAccountWrite(
    { cacao: kotobaCacao(), did: "did:key:zOTHER" },
    cbor,
    relay,
  );
  assert.equal(status, 400);
  assert.equal(relay.calls.length, 0);
});

test("explicit claims (device-wrap / rotation) are forwarded verbatim", async () => {
  const relay = recordingRelay("written");
  const claims = [
    { pred: "account/device/abc123", value: "wrappedArkB64xyz" },
    { pred: "account/controller", value: MEMBER_DID },
  ];
  const { status } = await handleAccountWrite(
    { cacao: kotobaCacao(), id: `account.${MEMBER_DID}`, claims },
    cbor,
    relay,
  );
  assert.equal(status, 200);
  assert.deepEqual(relay.calls[0].claims, claims);
});

test("bad explicit claim shape → 400", async () => {
  const { status } = await handleAccountWrite(
    { cacao: kotobaCacao(), claims: [{ pred: "account/x" }] },
    cbor,
    recordingRelay(),
  );
  assert.equal(status, 400);
});

test("non-account id → 400", async () => {
  const { status } = await handleAccountWrite(
    { cacao: kotobaCacao(), id: "device.evil" },
    cbor,
    recordingRelay(),
  );
  assert.equal(status, 400);
});

test("relay gated → 202 gated", async () => {
  const { status, result } = await handleAccountWrite({ cacao: kotobaCacao(), handle: "a" }, cbor, recordingRelay("gated"));
  assert.equal(status, 202);
  assert.equal(result.gated, true);
});

test("relay error → 502", async () => {
  const { status } = await handleAccountWrite({ cacao: kotobaCacao(), handle: "a" }, cbor, recordingRelay("error"));
  assert.equal(status, 502);
});
