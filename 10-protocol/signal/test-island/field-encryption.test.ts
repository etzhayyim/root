/**
 * @etzhayyim/signal — field-level encryption tests (coverage loop iter 12).
 *
 * The Signal E2E primitives package (the SSoT for the CRITICAL Signal Protocol
 * E2E convention, ADR-2604261110) had zero tests. This isolated island
 * (fake-indexeddb + node WebCrypto, outside the pnpm workspace glob so the
 * root pnpm-lock is untouched) exercises the field-level AES-GCM path end to
 * end: HKDF key derivation from the X25519 identity key, encrypt/decrypt
 * roundtrip, and the security-relevant separation + failure modes.
 */
import "fake-indexeddb/auto";
import { describe, it, expect, beforeEach } from "vitest";

import {
  isSignalEncrypted,
  isEncryptedVal,
  SIGNAL_VAL_PREFIX,
  SIGNAL_CONTENT_TYPE,
  SIGNAL_MULTI_CONTENT_TYPE,
  generateIdentity,
  deriveFieldKey,
  encryptFieldVal,
  decryptFieldVal,
  clearSignalData,
} from "../src/signal.ts";

const ALICE = "did:web:alice.test";
const BOB = "did:web:bob.test";
const CONVO = "convo-1";

beforeEach(async () => {
  await clearSignalData();
});

// ── pure helpers (no crypto / no IndexedDB) ──────────────────────────────────

describe("content-type + val helpers", () => {
  it("recognizes signal envelope content types", () => {
    expect(isSignalEncrypted(SIGNAL_CONTENT_TYPE)).toBe(true);
    expect(isSignalEncrypted(SIGNAL_MULTI_CONTENT_TYPE)).toBe(true);
    expect(isSignalEncrypted("text/plain")).toBe(false);
  });

  it("detects field-level encrypted vals by prefix", () => {
    expect(isEncryptedVal(SIGNAL_VAL_PREFIX + "abc")).toBe(true);
    expect(isEncryptedVal("plain")).toBe(false);
    expect(isEncryptedVal(123)).toBe(false);
    expect(isEncryptedVal(null)).toBe(false);
  });
});

// ── no identity → plaintext fallback (never throws, never silently drops) ────

describe("encryptFieldVal without an identity", () => {
  it("falls back to returning the plaintext unchanged", async () => {
    expect(await deriveFieldKey(ALICE, CONVO)).toBeNull();
    expect(await encryptFieldVal("secret", ALICE, CONVO)).toBe("secret");
  });

  it("decryptFieldVal returns the input verbatim when it is not a signal val", async () => {
    expect(await decryptFieldVal("not-encrypted", ALICE, CONVO)).toBe("not-encrypted");
  });
});

// ── full roundtrip with a real identity ──────────────────────────────────────

describe("field-level AES-GCM roundtrip", () => {
  it("encrypt → signal:v1: envelope → decrypt recovers the plaintext", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("仕様書のドラフト", ALICE, CONVO);
    expect(enc.startsWith(SIGNAL_VAL_PREFIX)).toBe(true);
    expect(enc).not.toContain("仕様書");
    expect(isEncryptedVal(enc)).toBe(true);
    expect(await decryptFieldVal(enc, ALICE, CONVO)).toBe("仕様書のドラフト");
  });

  it("uses a fresh random IV per call (ciphertext is non-deterministic)", async () => {
    await generateIdentity(ALICE, "device-1");
    const a = await encryptFieldVal("same", ALICE, CONVO);
    const b = await encryptFieldVal("same", ALICE, CONVO);
    expect(a).not.toBe(b);
    expect(await decryptFieldVal(a, ALICE, CONVO)).toBe("same");
    expect(await decryptFieldVal(b, ALICE, CONVO)).toBe("same");
  });

  it("deriveFieldKey is deterministic for the same (did, convoId)", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("x", ALICE, CONVO);
    // a second derive must reproduce the same key → decrypt succeeds
    expect(await decryptFieldVal(enc, ALICE, CONVO)).toBe("x");
  });
});

// ── domain separation + failure modes ────────────────────────────────────────

describe("domain separation and tamper resistance", () => {
  it("a different convoId derives a different key → decrypt fails (null)", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("secret", ALICE, CONVO);
    expect(await decryptFieldVal(enc, ALICE, "other-convo")).toBeNull();
  });

  it("a different identity (did) cannot decrypt", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("secret", ALICE, CONVO);
    await generateIdentity(BOB, "device-2");
    expect(await decryptFieldVal(enc, BOB, CONVO)).toBeNull();
  });

  it("tampered ciphertext fails the GCM tag and returns null", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("secret", ALICE, CONVO);
    const flipped = enc.slice(0, -2) + (enc.endsWith("A") ? "B" : "A");
    expect(await decryptFieldVal(flipped, ALICE, CONVO)).toBeNull();
  });

  it("decrypt with no identity returns null (cannot derive the key)", async () => {
    await generateIdentity(ALICE, "device-1");
    const enc = await encryptFieldVal("secret", ALICE, CONVO);
    await clearSignalData();
    expect(await decryptFieldVal(enc, ALICE, CONVO)).toBeNull();
  });
});
