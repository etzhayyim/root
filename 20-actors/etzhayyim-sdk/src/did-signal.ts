/**
 * @etzhayyim/sdk/did-signal — DID ↔ Signal IdentityKey binding verification.
 *
 * Per ADR-2605181100. An actor publishes their Signal IdentityKey in their
 * own PDS as `com.etzhayyim.encrypted.signalIdentity`, signed by the DID
 * document's signing key. Verifiers MUST check this signature before
 * trusting any PreKeyBundle to belong to that DID, otherwise a malicious
 * PDS could substitute a different Signal identity to MitM key-wrap traffic.
 *
 * Signature scheme: Ed25519 over CBOR-encoded canonical body. did:web key
 * resolution per W3C DID core spec; did:plc key resolution per atproto
 * `did:plc` spec. did:key resolution is supported for testing.
 */

import {encode as cborEncode} from "@ipld/dag-cbor";
import {ed25519} from "@noble/curves/ed25519";
import {sha256} from "@noble/hashes/sha256";
import {bytesToHex} from "@noble/hashes/utils";

export interface SignalIdentityBody {
  did: string;
  signalIdentityKey: Uint8Array;
  signalRegistrationId: number;
  signedPreKey?: Uint8Array;
  signedPreKeyId?: number;
  signedPreKeySignature?: Uint8Array;
  createdAt: string;
}

export interface SignedSignalIdentity extends SignalIdentityBody {
  /** Ed25519 signature over canonical CBOR(SignalIdentityBody). */
  signature: Uint8Array;
}

/**
 * Canonical bytes to sign / verify. CBOR-encoded body without the signature
 * field, in lexicographic key order (dag-cbor enforces this).
 */
export function canonicalSigningBytes(body: SignalIdentityBody): Uint8Array {
  return cborEncode(body);
}

/**
 * Sign a SignalIdentityBody with the actor's DID Ed25519 signing key. The
 * caller is responsible for ensuring `signingKey` corresponds to the
 * verification method published in `body.did`'s DID document.
 */
export function signSignalIdentity(
  body: SignalIdentityBody,
  signingKey: Uint8Array
): SignedSignalIdentity {
  const msg = canonicalSigningBytes(body);
  const signature = ed25519.sign(msg, signingKey);
  return {...body, signature};
}

export interface VerifyOpts {
  signed: SignedSignalIdentity;
  /**
   * Ed25519 public verification key resolved from the DID document
   * (`verificationMethod` of type `Ed25519VerificationKey2020` or the
   * multikey-encoded equivalent). The caller resolves the DID upstream;
   * this function does only cryptographic verification.
   */
  didVerificationKey: Uint8Array;
}

/**
 * Verify the binding signature. Returns `true` only if:
 *   - `signed.did` is non-empty,
 *   - the Ed25519 signature over CBOR(body) verifies under `didVerificationKey`.
 */
export function verifySignalIdentity(opts: VerifyOpts): boolean {
  const {signed, didVerificationKey} = opts;
  if (!signed.did) return false;
  const {signature, ...body} = signed;
  const msg = canonicalSigningBytes(body);
  try {
    return ed25519.verify(signature, msg, didVerificationKey);
  } catch {
    return false;
  }
}

/**
 * Fingerprint of a Signal IdentityKey, suitable for human-readable
 * confirmation ("safety number" pattern). First 16 hex chars of SHA-256.
 */
export function signalIdentityFingerprint(identityKey: Uint8Array): string {
  return bytesToHex(sha256(identityKey)).slice(0, 16);
}
