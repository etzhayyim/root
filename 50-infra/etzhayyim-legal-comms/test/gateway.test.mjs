/**
 * G18 regression tests for the counsel-operated comms gateway.
 * Run: node --experimental-strip-types --test test/gateway.test.mjs
 *
 * Locks in ADR-2605302345 §D2: no legal act leaves without a human
 * licensed-counsel actuation; the corp holds no legal-act signing key.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { sendLegalAct, transmitNonLegalAct } from "../src/gateway.ts";

const transports = { fax: { async transmit() {} } };
const artifact = {
  destinationJurisdiction: "jpn",
  artifactClass: "court-filing",
  transport: "fax",
  payloadCid: "bafy",
  destinationEndpoint: "fax:+81",
};
const validActuation = {
  counselDid: "did:web:lawyer.jp",
  licenseJurisdiction: "jpn",
  counselSignatureRef: "sig:counsel-own-key",
  actuatedAt: "2026-05-30T00:00:00Z",
};

test("G18: legal act without actuation is refused", async () => {
  await assert.rejects(() => sendLegalAct(artifact, undefined, transports), /G18/);
});

test("G18: counsel licensed in wrong jurisdiction is refused", async () => {
  await assert.rejects(
    () => sendLegalAct(artifact, { ...validActuation, licenseJurisdiction: "usa" }, transports),
    /G18/,
  );
});

test("G18: actuation missing the lawyer's own signature is refused", async () => {
  await assert.rejects(
    () => sendLegalAct(artifact, { ...validActuation, counselSignatureRef: "" }, transports),
    /G18/,
  );
});

test("G18: valid in-jurisdiction counsel actuation transmits", async () => {
  const r = await sendLegalAct(artifact, validActuation, transports);
  assert.equal(r.ok, true);
  assert.equal(r.counselDid, "did:web:lawyer.jp");
  assert.equal(r.transport, "fax");
});

test("non-legal-act transport needs no actuation", async () => {
  const r = await transmitNonLegalAct("scheduling", "fax", "fax:+81", "bafy", transports);
  assert.equal(r.ok, true);
  assert.equal(r.counselDid, ""); // no counsel involved, by design
});
