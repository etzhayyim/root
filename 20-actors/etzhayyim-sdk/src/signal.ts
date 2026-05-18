/**
 * @etzhayyim/sdk/signal — Signal Protocol session wrapper for per-recipient
 * key-wrap delivery (X3DH + Double Ratchet via @signalapp/libsignal-client).
 *
 * Per ADR-2605181100. Apps MUST NOT import @signalapp/libsignal-client
 * directly; this is the SDK seam.
 *
 * Scope: encrypt/decrypt of the *symmetric record key* (typically 32 bytes)
 * for one (sender DID, recipient DID) pair. Bulk record encryption is the
 * crypto.ts module's job; this module only handles the wrap channel.
 *
 * libsignal is declared as an optionalDependency: installs that cannot
 * build the native module (e.g. browser-only bundles) will fail any
 * encryptedWrite/encryptedRead at runtime with a clear error, but the
 * rest of the SDK keeps working.
 */

export interface SignalSession {
  /** Stable identifier persisted alongside key-wrap records. */
  sessionId: string;
  /** Sender DID this session was established by. */
  senderDid: string;
  /** Recipient DID. */
  recipientDid: string;
}

export interface EstablishSessionOpts {
  senderDid: string;
  recipientDid: string;
  /**
   * Recipient's DID-attested SignalIdentity record
   * (`app.etzhayyim.encrypted.signalIdentity`). The caller MUST verify the
   * DID-binding signature before passing the bundle here; see
   * `@etzhayyim/sdk/did-signal#verifySignalIdentity`.
   */
  recipientIdentity: {
    signalIdentityKey: Uint8Array;
    signalRegistrationId: number;
    signedPreKey?: Uint8Array;
    signedPreKeyId?: number;
    signedPreKeySignature?: Uint8Array;
  };
}

/**
 * Establish (or rehydrate from store) a Signal session between sender and
 * recipient DIDs. Returns a session handle suitable for `wrapKey`/`unwrapKey`.
 *
 * v0.0.0 scaffold: throws "not yet implemented". Real impl lazy-imports
 * `@signalapp/libsignal-client`, builds a PreKeyBundle from
 * `opts.recipientIdentity`, and either creates a new session via X3DH or
 * loads an existing one from the local session store.
 */
export async function establishSession(
  _opts: EstablishSessionOpts
): Promise<SignalSession> {
  throw new Error(
    "[etzhayyim-sdk/signal] establishSession() not yet implemented. " +
      "TODO: (1) dynamic import @signalapp/libsignal-client, " +
      "(2) build PreKeyBundle from recipientIdentity, " +
      "(3) processPreKeyBundle into local SessionStore keyed by " +
      "(senderDid, recipientDid), (4) return {sessionId, senderDid, recipientDid}."
  );
}

export interface WrapKeyOpts {
  session: SignalSession;
  /** The 32-byte symmetric record key to wrap. */
  symmetricKey: Uint8Array;
}

export interface WrapKeyResult {
  /** libsignal-encrypted ciphertext stored in keyWrap.ciphertext. */
  ciphertext: Uint8Array;
  /** Session id propagated to keyWrap.signalSessionId. */
  signalSessionId: string;
}

/**
 * Encrypt a symmetric record key for the recipient via the Signal session.
 *
 * v0.0.0 scaffold: throws "not yet implemented". Real impl calls
 * `SessionCipher.encrypt(symmetricKey)` and returns the serialized
 * CiphertextMessage bytes.
 */
export async function wrapKey(_opts: WrapKeyOpts): Promise<WrapKeyResult> {
  throw new Error(
    "[etzhayyim-sdk/signal] wrapKey() not yet implemented. " +
      "TODO: SessionCipher(localStore, recipientAddress).encrypt(symmetricKey) " +
      "→ serialize() → {ciphertext, signalSessionId}."
  );
}

export interface UnwrapKeyOpts {
  /** Session for the (sender, self) pair the keyWrap was authored under. */
  session: SignalSession;
  /** Ciphertext field of the app.etzhayyim.encrypted.keyWrap record. */
  ciphertext: Uint8Array;
}

/**
 * Decrypt a symmetric record key from a keyWrap record.
 *
 * v0.0.0 scaffold: throws "not yet implemented". Real impl reconstructs a
 * CiphertextMessage from `ciphertext` bytes and calls
 * `SessionCipher.decrypt*()` (pre-key vs whisper distinguished by the
 * Signal envelope type).
 */
export async function unwrapKey(_opts: UnwrapKeyOpts): Promise<Uint8Array> {
  throw new Error(
    "[etzhayyim-sdk/signal] unwrapKey() not yet implemented. " +
      "TODO: parse CiphertextMessage type prefix, dispatch to " +
      "decryptPreKeyWhisperMessage or decryptWhisperMessage, return 32-byte key."
  );
}

/**
 * Generate a fresh libsignal IdentityKey + RegistrationId + signed pre-key
 * bundle for self-publication as `app.etzhayyim.encrypted.signalIdentity`.
 *
 * v0.0.0 scaffold: throws "not yet implemented". Real impl calls
 * `IdentityKeyPair.generate()`, allocates a random 14-bit registrationId,
 * generates a signed pre-key, and returns the publishable bundle (the
 * caller signs it with their DID signing key — see did-signal.ts).
 */
export async function generateLocalIdentity(): Promise<{
  signalIdentityKey: Uint8Array;
  signalRegistrationId: number;
  signedPreKey: Uint8Array;
  signedPreKeyId: number;
  signedPreKeySignature: Uint8Array;
}> {
  throw new Error(
    "[etzhayyim-sdk/signal] generateLocalIdentity() not yet implemented. " +
      "TODO: IdentityKeyPair.generate(); random 14-bit registrationId; " +
      "signed pre-key via Curve.calculateSignature(idKey, prekey.pub)."
  );
}
