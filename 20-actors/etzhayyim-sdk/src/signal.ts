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

import {bytesToHex} from "@noble/hashes/utils";
import {sha256} from "@noble/hashes/sha256";

// libsignal is loaded lazily via dynamic import so the SDK still parses
// in environments that cannot link the native module (e.g. browser
// bundles, build hosts without the Rust toolchain).
type LibSignal = typeof import("@signalapp/libsignal-client");
let _libsignal: LibSignal | null = null;

async function getLibSignal(): Promise<LibSignal> {
  if (_libsignal) return _libsignal;
  try {
    _libsignal = (await import(
      "@signalapp/libsignal-client"
    )) as unknown as LibSignal;
    return _libsignal;
  } catch (cause) {
    throw new Error(
      "[etzhayyim-sdk/signal] @signalapp/libsignal-client is not available. " +
        "It is declared as an optionalDependency; install it explicitly " +
        "to enable encrypted record key-wrap.",
      {cause}
    );
  }
}

/** Test hook — drops the cached binding so unit tests can stub it. */
export function _resetLibSignalCache(): void {
  _libsignal = null;
}

const DEFAULT_DEVICE_ID = 1;

// ── Local-store container (per-actor) ────────────────────────────────────────

/**
 * Per-actor opaque handle holding all six libsignal stores (Session, Identity,
 * PreKey, SignedPreKey, KyberPreKey) plus the locally generated identity
 * keypair / registrationId. Treat as opaque outside this module — peers SDK
 * calls accept it through `establishSession` / `wrapKey` / `unwrapKey`.
 */
export interface LocalStores {
  readonly identityStore: import("@signalapp/libsignal-client").IdentityKeyStore;
  readonly sessionStore: import("@signalapp/libsignal-client").SessionStore;
  readonly preKeyStore: import("@signalapp/libsignal-client").PreKeyStore;
  readonly signedPreKeyStore: import("@signalapp/libsignal-client").SignedPreKeyStore;
  readonly kyberPreKeyStore: import("@signalapp/libsignal-client").KyberPreKeyStore;
  readonly identityKeyPair: import("@signalapp/libsignal-client").IdentityKeyPair;
  readonly registrationId: number;
}

// ── In-memory store implementations ──────────────────────────────────────────

async function makeInMemoryStores(
  ls: LibSignal,
  identityKeyPair: import("@signalapp/libsignal-client").IdentityKeyPair,
  registrationId: number
): Promise<LocalStores> {
  const SessionStore = ls.SessionStore;
  const IdentityKeyStore = ls.IdentityKeyStore;
  const PreKeyStore = ls.PreKeyStore;
  const SignedPreKeyStore = ls.SignedPreKeyStore;
  const KyberPreKeyStore = ls.KyberPreKeyStore;

  class _SessionStore extends SessionStore {
    private readonly map = new Map<string, import("@signalapp/libsignal-client").SessionRecord>();
    async saveSession(
      address: import("@signalapp/libsignal-client").ProtocolAddress,
      record: import("@signalapp/libsignal-client").SessionRecord
    ): Promise<void> {
      this.map.set(addressKey(address), record);
    }
    async getSession(
      address: import("@signalapp/libsignal-client").ProtocolAddress
    ): Promise<import("@signalapp/libsignal-client").SessionRecord | null> {
      return this.map.get(addressKey(address)) ?? null;
    }
    async getExistingSessions(
      addresses: import("@signalapp/libsignal-client").ProtocolAddress[]
    ): Promise<import("@signalapp/libsignal-client").SessionRecord[]> {
      const out: import("@signalapp/libsignal-client").SessionRecord[] = [];
      for (const a of addresses) {
        const r = this.map.get(addressKey(a));
        if (r) out.push(r);
      }
      return out;
    }
  }

  class _IdentityKeyStore extends IdentityKeyStore {
    private readonly identities = new Map<string, import("@signalapp/libsignal-client").PublicKey>();
    async getIdentityKey(): Promise<import("@signalapp/libsignal-client").PrivateKey> {
      return identityKeyPair.privateKey;
    }
    async getLocalRegistrationId(): Promise<number> {
      return registrationId;
    }
    async saveIdentity(
      address: import("@signalapp/libsignal-client").ProtocolAddress,
      key: import("@signalapp/libsignal-client").PublicKey
    ): Promise<boolean> {
      const k = addressKey(address);
      const prior = this.identities.get(k);
      this.identities.set(k, key);
      return prior !== undefined && prior.serialize().compare(key.serialize()) !== 0;
    }
    async isTrustedIdentity(): Promise<boolean> {
      return true;
    }
    async getIdentity(
      address: import("@signalapp/libsignal-client").ProtocolAddress
    ): Promise<import("@signalapp/libsignal-client").PublicKey | null> {
      return this.identities.get(addressKey(address)) ?? null;
    }
  }

  class _PreKeyStore extends PreKeyStore {
    private readonly map = new Map<number, import("@signalapp/libsignal-client").PreKeyRecord>();
    async savePreKey(
      id: number,
      record: import("@signalapp/libsignal-client").PreKeyRecord
    ): Promise<void> {
      this.map.set(id, record);
    }
    async getPreKey(id: number): Promise<import("@signalapp/libsignal-client").PreKeyRecord> {
      const r = this.map.get(id);
      if (!r) throw new Error(`prekey ${id} not found`);
      return r;
    }
    async removePreKey(id: number): Promise<void> {
      this.map.delete(id);
    }
  }

  class _SignedPreKeyStore extends SignedPreKeyStore {
    private readonly map = new Map<
      number,
      import("@signalapp/libsignal-client").SignedPreKeyRecord
    >();
    async saveSignedPreKey(
      id: number,
      record: import("@signalapp/libsignal-client").SignedPreKeyRecord
    ): Promise<void> {
      this.map.set(id, record);
    }
    async getSignedPreKey(
      id: number
    ): Promise<import("@signalapp/libsignal-client").SignedPreKeyRecord> {
      const r = this.map.get(id);
      if (!r) throw new Error(`signed prekey ${id} not found`);
      return r;
    }
  }

  class _KyberPreKeyStore extends KyberPreKeyStore {
    private readonly map = new Map<
      number,
      import("@signalapp/libsignal-client").KyberPreKeyRecord
    >();
    private readonly used = new Set<number>();
    async saveKyberPreKey(
      id: number,
      record: import("@signalapp/libsignal-client").KyberPreKeyRecord
    ): Promise<void> {
      this.map.set(id, record);
    }
    async getKyberPreKey(
      id: number
    ): Promise<import("@signalapp/libsignal-client").KyberPreKeyRecord> {
      const r = this.map.get(id);
      if (!r) throw new Error(`kyber prekey ${id} not found`);
      return r;
    }
    async markKyberPreKeyUsed(id: number): Promise<void> {
      this.used.add(id);
    }
  }

  return {
    identityStore: new _IdentityKeyStore(),
    sessionStore: new _SessionStore(),
    preKeyStore: new _PreKeyStore(),
    signedPreKeyStore: new _SignedPreKeyStore(),
    kyberPreKeyStore: new _KyberPreKeyStore(),
    identityKeyPair,
    registrationId,
  };
}

function addressKey(
  address: import("@signalapp/libsignal-client").ProtocolAddress
): string {
  return `${address.name()}::${address.deviceId()}`;
}

// ── Public types ─────────────────────────────────────────────────────────────

export interface SignalSession {
  /** Stable identifier persisted alongside key-wrap records. */
  sessionId: string;
  /** Sender DID this session was established by. */
  senderDid: string;
  /** Recipient DID. */
  recipientDid: string;
}

/** Deterministic sessionId from the directed pair (sender → recipient). */
export function sessionIdOf(senderDid: string, recipientDid: string): string {
  return bytesToHex(
    sha256(new TextEncoder().encode(`${senderDid}|${recipientDid}`))
  ).slice(0, 32);
}

// ── generateLocalIdentity ────────────────────────────────────────────────────

export interface LocalIdentityBundle {
  /** Publishable fields — go into `app.etzhayyim.encrypted.signalIdentity`. */
  publishable: {
    signalIdentityKey: Uint8Array;
    signalRegistrationId: number;
    signedPreKey: Uint8Array;
    signedPreKeyId: number;
    signedPreKeySignature: Uint8Array;
  };
  /** Local-only stores — keep in process memory or persist out-of-band. */
  stores: LocalStores;
}

export interface GenerateLocalIdentityOpts {
  /** SignedPreKey ID to allocate. Default: 1. */
  signedPreKeyId?: number;
  /** RegistrationId. Default: cryptographically random 14-bit. */
  registrationId?: number;
}

/**
 * Generate a fresh libsignal IdentityKey + RegistrationId + signed pre-key
 * bundle, returning both the publishable bytes (for
 * `app.etzhayyim.encrypted.signalIdentity`) and the local-only stores.
 *
 * The caller is responsible for signing the publishable bundle with their
 * DID key (see `did-signal.ts#signSignalIdentity`) and writing it to PDS.
 */
export async function generateLocalIdentity(
  opts: GenerateLocalIdentityOpts = {}
): Promise<LocalIdentityBundle> {
  const ls = await getLibSignal();
  const identityKeyPair = ls.IdentityKeyPair.generate();
  const registrationId =
    opts.registrationId ?? (1 + Math.floor(Math.random() * ((1 << 14) - 1)));

  const signedPreKeyId = opts.signedPreKeyId ?? 1;
  const signedPreKeyKeyPair = ls.PrivateKey.generate();
  const signedPreKeySignature = identityKeyPair.privateKey.sign(
    signedPreKeyKeyPair.getPublicKey().serialize()
  );
  const signedPreKeyRecord = ls.SignedPreKeyRecord.new(
    signedPreKeyId,
    Date.now(),
    signedPreKeyKeyPair.getPublicKey(),
    signedPreKeyKeyPair,
    signedPreKeySignature
  );

  const stores = await makeInMemoryStores(ls, identityKeyPair, registrationId);
  await stores.signedPreKeyStore.saveSignedPreKey(
    signedPreKeyId,
    signedPreKeyRecord
  );

  return {
    publishable: {
      signalIdentityKey: Uint8Array.from(identityKeyPair.publicKey.serialize()),
      signalRegistrationId: registrationId,
      signedPreKey: Uint8Array.from(signedPreKeyKeyPair.getPublicKey().serialize()),
      signedPreKeyId,
      signedPreKeySignature: Uint8Array.from(signedPreKeySignature),
    },
    stores,
  };
}

// ── establishSession ─────────────────────────────────────────────────────────

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
  /** Sender's local stores (returned by `generateLocalIdentity`). */
  senderStores: LocalStores;
}

/**
 * Establish (or rehydrate from store) a Signal session between sender and
 * recipient DIDs. Returns a session handle suitable for `wrapKey`.
 */
export async function establishSession(
  opts: EstablishSessionOpts
): Promise<SignalSession> {
  const ls = await getLibSignal();
  const {senderDid, recipientDid, recipientIdentity, senderStores} = opts;

  if (
    !recipientIdentity.signedPreKey ||
    recipientIdentity.signedPreKeyId == null ||
    !recipientIdentity.signedPreKeySignature
  ) {
    throw new Error(
      "[etzhayyim-sdk/signal] establishSession requires recipient signedPreKey " +
        "+ signedPreKeyId + signedPreKeySignature (from their published " +
        "app.etzhayyim.encrypted.signalIdentity record)."
    );
  }

  const recipientAddress = ls.ProtocolAddress.new(
    recipientDid,
    DEFAULT_DEVICE_ID
  );

  const identityPub = ls.PublicKey.deserialize(
    Buffer.from(recipientIdentity.signalIdentityKey)
  );
  const signedPrekeyPub = ls.PublicKey.deserialize(
    Buffer.from(recipientIdentity.signedPreKey)
  );

  const bundle = ls.PreKeyBundle.new(
    recipientIdentity.signalRegistrationId,
    DEFAULT_DEVICE_ID,
    null, // one-time prekey id (none)
    null, // one-time prekey (none) — long-form key-wrap operates on the SPK
    recipientIdentity.signedPreKeyId,
    signedPrekeyPub,
    Buffer.from(recipientIdentity.signedPreKeySignature),
    identityPub
  );

  await ls.processPreKeyBundle(
    bundle,
    recipientAddress,
    senderStores.sessionStore,
    senderStores.identityStore
  );

  return {
    sessionId: sessionIdOf(senderDid, recipientDid),
    senderDid,
    recipientDid,
  };
}

// ── wrapKey ──────────────────────────────────────────────────────────────────

export interface WrapKeyOpts {
  session: SignalSession;
  /** The 32-byte symmetric record key to wrap. */
  symmetricKey: Uint8Array;
  /** Sender's local stores (same instance as passed to establishSession). */
  senderStores: LocalStores;
}

export interface WrapKeyResult {
  /** libsignal-encrypted ciphertext stored in keyWrap.ciphertext. */
  ciphertext: Uint8Array;
  /** Session id propagated to keyWrap.signalSessionId. */
  signalSessionId: string;
  /** Message type — 2=Whisper (post-bootstrap) or 3=PreKey (first send). */
  messageType: number;
}

/** Encrypt a symmetric record key for the recipient via the Signal session. */
export async function wrapKey(opts: WrapKeyOpts): Promise<WrapKeyResult> {
  const ls = await getLibSignal();
  const {session, symmetricKey, senderStores} = opts;
  const recipientAddress = ls.ProtocolAddress.new(
    session.recipientDid,
    DEFAULT_DEVICE_ID
  );
  const cipher = await ls.signalEncrypt(
    Buffer.from(symmetricKey),
    recipientAddress,
    senderStores.sessionStore,
    senderStores.identityStore
  );
  return {
    ciphertext: Uint8Array.from(cipher.serialize()),
    signalSessionId: session.sessionId,
    messageType: cipher.type(),
  };
}

// ── unwrapKey ────────────────────────────────────────────────────────────────

export interface UnwrapKeyOpts {
  /**
   * Session metadata. The recipient is `session.recipientDid` (== self), the
   * sender is `session.senderDid` (the keyWrap author). On first contact the
   * recipient has no prior session; `messageType` distinguishes PreKey vs
   * Whisper so we route to the right libsignal decrypt fn.
   */
  session: SignalSession;
  /** Ciphertext field of the app.etzhayyim.encrypted.keyWrap record. */
  ciphertext: Uint8Array;
  /**
   * Optional explicit message type (from wrapKey result). Required when the
   * recipient cannot infer the type from the bytes alone; libsignal exposes
   * it via the wrapped CiphertextMessage but we keep it as a defensive hint.
   */
  messageType?: number;
  /** Recipient's local stores. */
  recipientStores: LocalStores;
}

/** Decrypt a symmetric record key from a keyWrap record. */
export async function unwrapKey(opts: UnwrapKeyOpts): Promise<Uint8Array> {
  const ls = await getLibSignal();
  const {session, ciphertext, recipientStores} = opts;
  const senderAddress = ls.ProtocolAddress.new(
    session.senderDid,
    DEFAULT_DEVICE_ID
  );

  // Type discriminator: byte 0 high nibble in libsignal's wire format is the
  // message type. PreKeySignalMessage.deserialize / SignalMessage.deserialize
  // will throw on the wrong type, so we use the explicit hint when given and
  // try-fall through otherwise.
  const hint = opts.messageType;
  const ct = Buffer.from(ciphertext);

  if (hint === ls.CiphertextMessageType.PreKey || hint == null) {
    try {
      const msg = ls.PreKeySignalMessage.deserialize(ct);
      const out = await ls.signalDecryptPreKey(
        msg,
        senderAddress,
        recipientStores.sessionStore,
        recipientStores.identityStore,
        recipientStores.preKeyStore,
        recipientStores.signedPreKeyStore,
        recipientStores.kyberPreKeyStore
      );
      return Uint8Array.from(out);
    } catch (err) {
      if (hint === ls.CiphertextMessageType.PreKey) throw err;
      // fall through to Whisper attempt
    }
  }

  // Whisper (or hint==Whisper / Plaintext).
  const SignalMessageCtor = (ls as unknown as {
    SignalMessage: {deserialize(b: Buffer): import("@signalapp/libsignal-client").SignalMessage};
  }).SignalMessage;
  const wmsg = SignalMessageCtor.deserialize(ct);
  const out = await ls.signalDecrypt(
    wmsg,
    senderAddress,
    recipientStores.sessionStore,
    recipientStores.identityStore
  );
  return Uint8Array.from(out);
}
