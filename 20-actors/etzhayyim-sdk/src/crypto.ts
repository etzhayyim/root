/**
 * @etzhayyim/sdk/crypto — Tahoe-pattern AEAD envelope for AT Protocol MST.
 *
 * Per ADR-2605181100. Apps MUST NOT import @noble/ciphers directly; this is
 * the SDK seam for record-at-rest confidentiality. The CID over the envelope
 * inherits the MST verify-cap and L2 anchor finality from ADR-2605172000.
 *
 * Algorithm: XChaCha20-Poly1305 (24-byte nonce, 16-byte tag).
 * AAD: the record's own CID bytes, bound at decryption time to prevent
 *      intra-MST swap attacks.
 */

import {xchacha20poly1305} from "@noble/ciphers/chacha";
import {randomBytes} from "@noble/ciphers/webcrypto";
import {sha256} from "@noble/hashes/sha256";
import {bytesToHex} from "@noble/hashes/utils";
import {encode as cborEncode, decode as cborDecode} from "@ipld/dag-cbor";

export const AEAD_ALG = "xchacha20poly1305" as const;
export const ENVELOPE_VERSION = 1 as const;
export const NONCE_BYTES = 24;
export const KEY_BYTES = 32;

export type SymmetricKey = Uint8Array & {readonly __brand: "SymmetricKey"};

/** Generate a fresh 32-byte XChaCha20-Poly1305 key. */
export function generateKey(): SymmetricKey {
  return randomBytes(KEY_BYTES) as SymmetricKey;
}

/** Generate a fresh 24-byte XChaCha20-Poly1305 nonce. */
export function generateNonce(): Uint8Array {
  return randomBytes(NONCE_BYTES);
}

/**
 * keyId = first 16 hex chars of SHA-256(key). Used as the lookup handle in
 * `app.etzhayyim.encrypted.keyWrap.keyId` so recipients can match a wrap to
 * the encrypted record without revealing the key itself.
 */
export function keyIdOf(key: SymmetricKey): string {
  return bytesToHex(sha256(key)).slice(0, 16);
}

export interface EncryptedEnvelope {
  v: typeof ENVELOPE_VERSION;
  alg: typeof AEAD_ALG;
  nonce: Uint8Array;
  ciphertext: Uint8Array;
  keyId: string;
  sender: string;
  innerType?: string;
  createdAt: string;
}

export interface EncryptOpts {
  key: SymmetricKey;
  sender: string;
  plaintext: unknown;
  /**
   * Additional authenticated data. SHOULD be the CID of the record this
   * envelope will be stored under so swap attacks within the same MST are
   * detected at decrypt time. Caller passes the CID bytes once known (or
   * a stable record identifier if encrypting before CID assignment, with
   * the trade-off documented in ADR-2605181100).
   */
  aad?: Uint8Array;
  innerType?: string;
  nonce?: Uint8Array;
  createdAt?: string;
}

/**
 * Encrypt a CBOR-serializable plaintext into the envelope format described
 * in lexicon `app.etzhayyim.encrypted.record`.
 */
export function encrypt(opts: EncryptOpts): EncryptedEnvelope {
  if (opts.key.length !== KEY_BYTES) {
    throw new Error(`[etzhayyim-sdk/crypto] key must be ${KEY_BYTES} bytes`);
  }
  const nonce = opts.nonce ?? generateNonce();
  if (nonce.length !== NONCE_BYTES) {
    throw new Error(`[etzhayyim-sdk/crypto] nonce must be ${NONCE_BYTES} bytes`);
  }
  const cipher = xchacha20poly1305(opts.key, nonce, opts.aad);
  const plaintextBytes = cborEncode(opts.plaintext);
  const ciphertext = cipher.encrypt(plaintextBytes);
  return {
    v: ENVELOPE_VERSION,
    alg: AEAD_ALG,
    nonce,
    ciphertext,
    keyId: keyIdOf(opts.key),
    sender: opts.sender,
    innerType: opts.innerType,
    createdAt: opts.createdAt ?? new Date().toISOString(),
  };
}

export interface DecryptOpts {
  key: SymmetricKey;
  envelope: EncryptedEnvelope;
  /** Same AAD passed at encrypt time. MUST match or decryption fails. */
  aad?: Uint8Array;
}

/**
 * Decrypt an envelope back to its CBOR plaintext. Throws on AEAD tag failure,
 * version mismatch, or algorithm mismatch.
 */
export function decrypt<T = unknown>(opts: DecryptOpts): T {
  const {envelope, key, aad} = opts;
  if (envelope.v !== ENVELOPE_VERSION) {
    throw new Error(
      `[etzhayyim-sdk/crypto] unsupported envelope version: ${envelope.v}`
    );
  }
  if (envelope.alg !== AEAD_ALG) {
    throw new Error(
      `[etzhayyim-sdk/crypto] unsupported AEAD algorithm: ${envelope.alg}`
    );
  }
  if (keyIdOf(key) !== envelope.keyId) {
    throw new Error(
      "[etzhayyim-sdk/crypto] key does not match envelope.keyId"
    );
  }
  const cipher = xchacha20poly1305(key, envelope.nonce, aad);
  const plaintextBytes = cipher.decrypt(envelope.ciphertext);
  return cborDecode(plaintextBytes) as T;
}
