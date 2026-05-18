/**
 * Unit tests for `@etzhayyim/sdk/crypto`.
 *
 * Scope: AEAD round-trip, AAD binding, tamper detection, key-id derivation.
 * Out of scope: PDS write/read integration (covered when encryptedWrite/
 * encryptedRead land on the main Etzhayyim class).
 */

import {describe, it, expect} from "vitest";
import {
  AEAD_ALG,
  ENVELOPE_VERSION,
  KEY_BYTES,
  NONCE_BYTES,
  decrypt,
  encrypt,
  generateKey,
  generateNonce,
  keyIdOf,
} from "../src/crypto.js";

const SENDER = "did:web:alice.example";

describe("crypto envelope round-trip", () => {
  it("encrypts and decrypts a CBOR-serializable plaintext", () => {
    const key = generateKey();
    const plaintext = {hello: "world", n: 42, list: [1, 2, 3]};

    const env = encrypt({key, sender: SENDER, plaintext});

    expect(env.v).toBe(ENVELOPE_VERSION);
    expect(env.alg).toBe(AEAD_ALG);
    expect(env.nonce).toHaveLength(NONCE_BYTES);
    expect(env.sender).toBe(SENDER);
    expect(env.keyId).toBe(keyIdOf(key));

    const out = decrypt<typeof plaintext>({key, envelope: env});
    expect(out).toEqual(plaintext);
  });

  it("propagates innerType when supplied", () => {
    const key = generateKey();
    const env = encrypt({
      key,
      sender: SENDER,
      plaintext: {x: 1},
      innerType: "app.etzhayyim.governance.proposal",
    });
    expect(env.innerType).toBe("app.etzhayyim.governance.proposal");
  });

  it("uses a deterministic nonce when caller supplies one", () => {
    const key = generateKey();
    const nonce = generateNonce();
    const env = encrypt({key, sender: SENDER, plaintext: {a: 1}, nonce});
    expect(env.nonce).toEqual(nonce);
  });
});

describe("crypto AEAD binding", () => {
  it("rejects ciphertext when AAD differs at decrypt", () => {
    const key = generateKey();
    const env = encrypt({
      key,
      sender: SENDER,
      plaintext: {confidential: true},
      aad: new Uint8Array([1, 2, 3]),
    });
    expect(() =>
      decrypt({key, envelope: env, aad: new Uint8Array([9, 9, 9])})
    ).toThrow();
  });

  it("rejects ciphertext when AAD is missing at decrypt", () => {
    const key = generateKey();
    const env = encrypt({
      key,
      sender: SENDER,
      plaintext: {confidential: true},
      aad: new Uint8Array([1, 2, 3]),
    });
    expect(() => decrypt({key, envelope: env})).toThrow();
  });

  it("detects ciphertext tampering", () => {
    const key = generateKey();
    const env = encrypt({key, sender: SENDER, plaintext: {x: 1}});
    env.ciphertext[0] ^= 0xff;
    expect(() => decrypt({key, envelope: env})).toThrow();
  });

  it("rejects wrong key", () => {
    const key1 = generateKey();
    const key2 = generateKey();
    const env = encrypt({key: key1, sender: SENDER, plaintext: {x: 1}});
    expect(() => decrypt({key: key2, envelope: env})).toThrow();
  });
});

describe("crypto invariants", () => {
  it("rejects key of wrong length", () => {
    const badKey = new Uint8Array(16) as ReturnType<typeof generateKey>;
    expect(() => encrypt({key: badKey, sender: SENDER, plaintext: {}})).toThrow();
  });

  it("rejects nonce of wrong length", () => {
    const key = generateKey();
    const badNonce = new Uint8Array(12);
    expect(() =>
      encrypt({key, sender: SENDER, plaintext: {}, nonce: badNonce})
    ).toThrow();
  });

  it("rejects unknown envelope version at decrypt", () => {
    const key = generateKey();
    const env = encrypt({key, sender: SENDER, plaintext: {}});
    const bumped = {...env, v: 99 as unknown as typeof ENVELOPE_VERSION};
    expect(() => decrypt({key, envelope: bumped})).toThrow(/envelope version/);
  });

  it("keyIdOf is deterministic and 16 hex chars", () => {
    const key = generateKey();
    const id1 = keyIdOf(key);
    const id2 = keyIdOf(key);
    expect(id1).toBe(id2);
    expect(id1).toHaveLength(16);
    expect(id1).toMatch(/^[0-9a-f]+$/);
  });

  it("generateKey returns 32 bytes", () => {
    expect(generateKey()).toHaveLength(KEY_BYTES);
  });
});
