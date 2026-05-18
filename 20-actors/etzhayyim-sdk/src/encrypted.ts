/**
 * @etzhayyim/sdk/encrypted — orchestration for Tahoe-pattern encrypted
 * records on the AT Protocol substrate.
 *
 * Per ADR-2605181100. Combines:
 *   - crypto.ts        AEAD record-at-rest encryption
 *   - signal.ts        per-recipient key-wrap via Signal session
 *   - did-signal.ts    DID ↔ Signal identity binding verification
 *   - pds.ts           PDS write/read of envelope + keyWrap records
 *
 * v0.0.0 scaffold: write/read paths throw `not yet implemented`. The crypto
 * envelope round-trip is real (see crypto.ts) — this module wires it to
 * PDS once Signal sessions and PDS write methods land.
 */

import type {Etzhayyim} from "./index.js";

export interface EncryptedWriteOpts<T extends Record<string, unknown>> {
  /** Lexicon NSID of the wrapper record. Default: app.etzhayyim.encrypted.record. */
  collection?: string;

  /** Lexicon NSID describing the inner plaintext shape (informational). */
  innerType?: string;

  /** Plaintext record body. CBOR-serializable. */
  record: T;

  /** DIDs to grant read-cap. Sender is auto-added unless `wrapToSelf: false`. */
  recipients: string[];

  /** Also wrap to sender DID (default true) so self-decrypt from another device works. */
  wrapToSelf?: boolean;

  /** Optional override rkey for the envelope record. Default: SDK-generated TID. */
  rkey?: string;
}

export interface EncryptedWriteReceipt {
  /** AT URI of the encrypted envelope record. */
  uri: string;
  /** CID of the envelope record. */
  cid: string;
  /** keyId (matches envelope.keyId + keyWrap.keyId). */
  keyId: string;
  /** AT URIs of the per-recipient keyWrap records. */
  keyWraps: Array<{recipient: string; uri: string; cid: string}>;
}

export interface EncryptedReadOpts {
  collection?: string;
  innerType?: string;
  cursor?: string;
  limit?: number;
}

export interface EncryptedReadResponse<T> {
  records: Array<{
    uri: string;
    cid: string;
    value: T;
    sender: string;
    createdAt: string;
  }>;
  cursor?: string;
  /** Records the caller had a keyWrap for but whose decryption failed (e.g. AEAD tag mismatch, malformed envelope). */
  failed: Array<{uri: string; reason: string}>;
}

export async function encryptedWrite<T extends Record<string, unknown>>(
  _e: Etzhayyim,
  _opts: EncryptedWriteOpts<T>
): Promise<EncryptedWriteReceipt> {
  throw new Error(
    "[etzhayyim-sdk/encrypted] encryptedWrite() not yet implemented. " +
      "TODO: (1) crypto.generateKey() + crypto.encrypt(plaintext, sender=e.config.did), " +
      "(2) PDS createRecord(app.etzhayyim.encrypted.record, envelope) → uri + cid, " +
      "(3) for each recipient: resolve signalIdentity record from their PDS, " +
      "verifySignalIdentity() against their DID document, establishSession(), " +
      "wrapKey(symKey), createRecord(app.etzhayyim.encrypted.keyWrap, {...}), " +
      "(4) return EncryptedWriteReceipt."
  );
}

export async function encryptedRead<T>(
  _e: Etzhayyim,
  _opts: EncryptedReadOpts
): Promise<EncryptedReadResponse<T>> {
  throw new Error(
    "[etzhayyim-sdk/encrypted] encryptedRead() not yet implemented. " +
      "TODO: (1) listRecords(app.etzhayyim.encrypted.keyWrap) in caller's PDS, " +
      "(2) for each keyWrap: establishSession(sender=keyWrap.sender, self) if " +
      "needed, unwrapKey(keyWrap.ciphertext) → symKey, " +
      "(3) fetch referenced envelope record (keyWrap.recordUri or via keyId join), " +
      "(4) crypto.decrypt(envelope, symKey) → plaintext, " +
      "(5) if innerType filter set, drop non-matching envelopes."
  );
}
