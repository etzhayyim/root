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
 * The standalone functions below take their dependencies explicitly
 * (agent, sender DID, sender stores, recipient resolver). The
 * `Etzhayyim` class methods in index.ts are thin wrappers that pull
 * the same dependencies out of the instance config.
 */

import type {AtpAgent} from "@atproto/api";

import {
  decrypt,
  encrypt,
  generateKey,
  type EncryptedEnvelope,
  type SymmetricKey,
} from "./crypto.js";
import {
  verifySignalIdentity,
  type SignedSignalIdentity,
} from "./did-signal.js";
import * as pds from "./pds.js";
import {
  establishSession,
  unwrapKey,
  wrapKey,
  type LocalStores,
  type SignalSession,
} from "./signal.js";

const COLLECTION_RECORD = "app.etzhayyim.encrypted.record";
const COLLECTION_KEYWRAP = "app.etzhayyim.encrypted.keyWrap";
const COLLECTION_SIGNAL_IDENTITY = "app.etzhayyim.encrypted.signalIdentity";

// ── Public types ─────────────────────────────────────────────────────────────

export interface ResolvedRecipientIdentity {
  /** Publishable bundle stored in `app.etzhayyim.encrypted.signalIdentity`. */
  publishable: {
    signalIdentityKey: Uint8Array;
    signalRegistrationId: number;
    signedPreKey?: Uint8Array;
    signedPreKeyId?: number;
    signedPreKeySignature?: Uint8Array;
  };
  /** Full signed-record form, used for DID-binding verification. */
  signed: SignedSignalIdentity;
  /** Recipient's Ed25519 DID verification key (resolved from DID document). */
  didVerificationKey: Uint8Array;
}

/**
 * Resolve a recipient's Signal identity + DID-binding key. Apps with a real
 * did:web / did:plc resolver wire it in here. Tests pass an in-process map.
 */
export type RecipientIdentityResolver = (
  recipientDid: string
) => Promise<ResolvedRecipientIdentity | null>;

export interface EncryptedWriteOpts<T extends Record<string, unknown>> {
  /** Lexicon NSID of the wrapper record. Default: app.etzhayyim.encrypted.record. */
  collection?: string;

  /** Lexicon NSID describing the inner plaintext shape (informational). */
  innerType?: string;

  /** Plaintext record body. CBOR-serializable. */
  record: T;

  /** DIDs to grant read-cap. Sender is auto-added unless `wrapToSelf: false`. */
  recipients: string[];

  /** Also wrap to sender DID (default true). */
  wrapToSelf?: boolean;

  /** Optional override rkey for the envelope record. Default: SDK-generated. */
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
  /**
   * DIDs that could not be resolved or whose signalIdentity binding failed
   * to verify. These recipients did not receive a keyWrap. The envelope is
   * still written (the caller can republish keyWraps later).
   */
  skipped: Array<{recipient: string; reason: string}>;
}

export interface EncryptedReadOpts {
  collection?: string;
  innerType?: string;
  cursor?: string;
  limit?: number;
  /**
   * DIDs whose keyWrap collections to enumerate. The recipient discovers
   * keys by scanning each declared sender's PDS for keyWrap records whose
   * `recipient` field matches `selfDid`. Default: [selfDid] — covers the
   * wrapToSelf-only flow (journal records). For DM-style flows the
   * caller passes the set of known counterparties.
   */
  fromSenders?: string[];
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
  /** keyWraps that resolved but whose envelope decrypt failed. */
  failed: Array<{uri: string; reason: string}>;
}

// ── Lexicon record shapes ────────────────────────────────────────────────────

interface EncryptedRecordLex {
  v: 1;
  alg: string;
  nonce: Uint8Array;
  ciphertext: Uint8Array;
  keyId: string;
  sender: string;
  innerType?: string;
  createdAt: string;
}

interface KeyWrapLex {
  v: 1;
  keyId: string;
  sender: string;
  recipient: string;
  ciphertext: Uint8Array;
  messageType: number;
  signalSessionId: string;
  /** AT URI of the encrypted envelope this wrap unlocks. */
  recordUri: string;
  createdAt: string;
}

// ── Standalone write ─────────────────────────────────────────────────────────

export interface StandaloneWriteDeps {
  /** PDS agent authenticated to write under `senderDid`. */
  agent: AtpAgent;
  /** Sender's DID. */
  senderDid: string;
  /** Sender's libsignal local stores (from `signal.generateLocalIdentity`). */
  senderStores: LocalStores;
  /** Resolver for recipient identities. See `RecipientIdentityResolver`. */
  resolveRecipientIdentity: RecipientIdentityResolver;
}

export async function encryptedWriteStandalone<T extends Record<string, unknown>>(
  deps: StandaloneWriteDeps,
  opts: EncryptedWriteOpts<T>
): Promise<EncryptedWriteReceipt> {
  const collection = opts.collection ?? COLLECTION_RECORD;
  const wrapToSelf = opts.wrapToSelf ?? true;

  // 1. Generate a fresh symmetric key and seal the plaintext.
  const symKey = generateKey();
  const envelope: EncryptedEnvelope = encrypt({
    key: symKey,
    sender: deps.senderDid,
    plaintext: opts.record,
    innerType: opts.innerType,
  });

  // 2. Write the envelope record to the sender's PDS.
  const envelopeLex: EncryptedRecordLex = {
    v: 1,
    alg: envelope.alg,
    nonce: envelope.nonce,
    ciphertext: envelope.ciphertext,
    keyId: envelope.keyId,
    sender: envelope.sender,
    innerType: envelope.innerType,
    createdAt: envelope.createdAt,
  };
  const envelopeReceipt = await pds.createRecord(
    deps.agent,
    deps.senderDid,
    collection,
    envelopeLex,
    opts.rkey
  );

  // 3. For each recipient (incl. self when wrapToSelf): establish Signal
  //    session, wrap the symKey, write the keyWrap record. Skip recipients
  //    whose identity cannot be resolved/verified — caller can retry later.
  const recipientSet = new Set<string>(opts.recipients);
  if (wrapToSelf) recipientSet.add(deps.senderDid);

  const keyWraps: Array<{recipient: string; uri: string; cid: string}> = [];
  const skipped: Array<{recipient: string; reason: string}> = [];

  for (const recipientDid of recipientSet) {
    let resolved: ResolvedRecipientIdentity | null;
    try {
      resolved = await deps.resolveRecipientIdentity(recipientDid);
    } catch (err) {
      skipped.push({
        recipient: recipientDid,
        reason: `identity resolver threw: ${(err as Error).message ?? String(err)}`,
      });
      continue;
    }
    if (!resolved) {
      skipped.push({
        recipient: recipientDid,
        reason: "no app.etzhayyim.encrypted.signalIdentity record found",
      });
      continue;
    }
    const binding = verifySignalIdentity({
      signed: resolved.signed,
      didVerificationKey: resolved.didVerificationKey,
    });
    if (!binding) {
      skipped.push({
        recipient: recipientDid,
        reason: "DID-binding signature failed verification",
      });
      continue;
    }

    let session: SignalSession;
    let wrap: Awaited<ReturnType<typeof wrapKey>>;
    try {
      session = await establishSession({
        senderDid: deps.senderDid,
        recipientDid,
        recipientIdentity: resolved.publishable,
        senderStores: deps.senderStores,
      });
      wrap = await wrapKey({
        session,
        symmetricKey: symKey,
        senderStores: deps.senderStores,
      });
    } catch (err) {
      skipped.push({
        recipient: recipientDid,
        reason: `Signal session/wrap failed: ${(err as Error).message ?? String(err)}`,
      });
      continue;
    }

    const keyWrapLex: KeyWrapLex = {
      v: 1,
      keyId: envelope.keyId,
      sender: deps.senderDid,
      recipient: recipientDid,
      ciphertext: wrap.ciphertext,
      messageType: wrap.messageType,
      signalSessionId: wrap.signalSessionId,
      recordUri: envelopeReceipt.uri,
      createdAt: envelope.createdAt,
    };
    const kwReceipt = await pds.createRecord(
      deps.agent,
      deps.senderDid,
      COLLECTION_KEYWRAP,
      keyWrapLex
    );
    keyWraps.push({recipient: recipientDid, uri: kwReceipt.uri, cid: kwReceipt.cid});
  }

  return {
    uri: envelopeReceipt.uri,
    cid: envelopeReceipt.cid,
    keyId: envelope.keyId,
    keyWraps,
    skipped,
  };
}

// ── Standalone read ──────────────────────────────────────────────────────────

export interface StandaloneReadDeps {
  /** PDS agent authenticated to read under `selfDid`. */
  agent: AtpAgent;
  /** Self DID — the recipient enumerating their own keyWrap collection. */
  selfDid: string;
  /** Self's libsignal local stores. */
  selfStores: LocalStores;
  /**
   * Resolver to fetch a sender's envelope record. The envelope lives in the
   * sender's PDS (not the recipient's), so callers with a multi-PDS view
   * inject a sender-PDS-aware fetcher here. Default: same agent as `agent`
   * (single-PDS model used by tests).
   */
  fetchEnvelope?: (senderDid: string, recordUri: string) => Promise<EncryptedRecordLex | null>;
}

export async function encryptedReadStandalone<T>(
  deps: StandaloneReadDeps,
  opts: EncryptedReadOpts = {}
): Promise<EncryptedReadResponse<T>> {
  const fetchEnvelope =
    deps.fetchEnvelope ?? defaultEnvelopeFetcher(deps.agent);

  // 1. Enumerate keyWraps. Scan each declared sender's PDS for keyWrap
  //    records targeting us. Default scan set is just self (for the
  //    self-wrap / journal use case).
  const senders = opts.fromSenders ?? [deps.selfDid];
  // cursor pagination is single-sender-scoped. When fromSenders has >1 entry
  // the caller can only meaningfully paginate one sender at a time; on a
  // multi-sender call we honor opts.cursor for the first sender then start
  // fresh for the rest.
  let cursor = opts.cursor;
  let lastCursor: string | undefined;
  const allKwRecords: Array<{
    uri: string;
    cid: string;
    value: unknown;
  }> = [];
  for (const senderDid of senders) {
    const list = await pds.listRecords(
      deps.agent,
      senderDid,
      COLLECTION_KEYWRAP,
      {
        limit: opts.limit ?? 50,
        cursor,
        reverse: true,
      }
    );
    lastCursor = list.cursor;
    for (const r of list.records) {
      if ((r.value as KeyWrapLex).recipient === deps.selfDid) {
        allKwRecords.push(r);
      }
    }
    cursor = undefined;
  }

  const records: EncryptedReadResponse<T>["records"] = [];
  const failed: EncryptedReadResponse<T>["failed"] = [];

  for (const kwRecord of allKwRecords) {
    const kw = kwRecord.value as KeyWrapLex;
    // 2. Unwrap the symmetric key via Signal session.
    let symKey: Uint8Array;
    try {
      symKey = await unwrapKey({
        session: {
          sessionId: kw.signalSessionId,
          senderDid: kw.sender,
          recipientDid: deps.selfDid,
        },
        ciphertext: ensureBytes(kw.ciphertext),
        messageType: kw.messageType,
        recipientStores: deps.selfStores,
      });
    } catch (err) {
      failed.push({
        uri: kwRecord.uri,
        reason: `unwrap failed: ${(err as Error).message ?? String(err)}`,
      });
      continue;
    }

    // 3. Fetch the referenced envelope record.
    let envelopeLex: EncryptedRecordLex | null;
    try {
      envelopeLex = await fetchEnvelope(kw.sender, kw.recordUri);
    } catch (err) {
      failed.push({
        uri: kwRecord.uri,
        reason: `envelope fetch failed: ${(err as Error).message ?? String(err)}`,
      });
      continue;
    }
    if (!envelopeLex) {
      failed.push({uri: kwRecord.uri, reason: "envelope record not found"});
      continue;
    }

    // 4. Optional innerType filter.
    if (opts.innerType && envelopeLex.innerType !== opts.innerType) {
      continue;
    }

    // 5. Decrypt the envelope.
    let plaintext: T;
    try {
      plaintext = decrypt<T>({
        key: symKey as SymmetricKey,
        envelope: {
          v: 1,
          alg: envelopeLex.alg as "xchacha20poly1305",
          nonce: ensureBytes(envelopeLex.nonce),
          ciphertext: ensureBytes(envelopeLex.ciphertext),
          keyId: envelopeLex.keyId,
          sender: envelopeLex.sender,
          innerType: envelopeLex.innerType,
          createdAt: envelopeLex.createdAt,
        },
      });
    } catch (err) {
      failed.push({
        uri: kwRecord.uri,
        reason: `decrypt failed: ${(err as Error).message ?? String(err)}`,
      });
      continue;
    }

    records.push({
      uri: kw.recordUri,
      cid: "", // CID is on the envelope record, not the keyWrap; left empty here.
      value: plaintext,
      sender: kw.sender,
      createdAt: envelopeLex.createdAt,
    });
  }

  return {records, cursor: lastCursor, failed};
}

function defaultEnvelopeFetcher(
  agent: AtpAgent
): (senderDid: string, recordUri: string) => Promise<EncryptedRecordLex | null> {
  return async (senderDid, recordUri) => {
    // recordUri is `at://<sender>/<collection>/<rkey>`.
    const parts = recordUri.replace(/^at:\/\//, "").split("/");
    if (parts.length < 3) return null;
    const collection = parts[1];
    const rkey = parts[2];
    const r = await pds.getRecord(agent, senderDid, collection, rkey);
    return (r?.value as EncryptedRecordLex | undefined) ?? null;
  };
}

function ensureBytes(v: unknown): Uint8Array {
  if (v instanceof Uint8Array) return v;
  if (Array.isArray(v)) return new Uint8Array(v as number[]);
  if (
    typeof v === "object" &&
    v !== null &&
    (v as {type?: unknown}).type === "Buffer" &&
    Array.isArray((v as {data?: unknown}).data)
  ) {
    // Node JSON serialization of Buffer.
    return new Uint8Array((v as {data: number[]}).data);
  }
  throw new TypeError("encrypted.ts: expected Uint8Array");
}

// ── Helper to publish your signalIdentity record ─────────────────────────────

export interface PublishSignalIdentityOpts {
  agent: AtpAgent;
  selfDid: string;
  signed: SignedSignalIdentity;
}

export async function publishSignalIdentity(
  opts: PublishSignalIdentityOpts
): Promise<{uri: string; cid: string}> {
  return pds.createRecord(
    opts.agent,
    opts.selfDid,
    COLLECTION_SIGNAL_IDENTITY,
    {
      did: opts.signed.did,
      signalIdentityKey: opts.signed.signalIdentityKey,
      signalRegistrationId: opts.signed.signalRegistrationId,
      signedPreKey: opts.signed.signedPreKey,
      signedPreKeyId: opts.signed.signedPreKeyId,
      signedPreKeySignature: opts.signed.signedPreKeySignature,
      createdAt: opts.signed.createdAt,
      signature: opts.signed.signature,
    }
  );
}

// ── Etzhayyim-class wrappers (legacy) ────────────────────────────────────────

import type {Etzhayyim} from "./index.js";

/**
 * Class-instance shim. The instance must have:
 *   - `pdsAgent` (set via `e.pdsAgent = ...` or future config)
 *   - `signalStores`
 *   - `resolveRecipientIdentity`
 *
 * For now these are stubbed-out shims that surface a clearer error if the
 * caller forgot to wire them. Apps that want the class-method ergonomic
 * should configure the instance once at startup.
 */
export async function encryptedWrite<T extends Record<string, unknown>>(
  e: Etzhayyim & {
    pdsAgent?: AtpAgent;
    signalStores?: LocalStores;
    resolveRecipientIdentity?: RecipientIdentityResolver;
  },
  opts: EncryptedWriteOpts<T>
): Promise<EncryptedWriteReceipt> {
  if (!e.pdsAgent || !e.signalStores || !e.resolveRecipientIdentity) {
    throw new Error(
      "[etzhayyim-sdk/encrypted] Etzhayyim instance missing pdsAgent / " +
        "signalStores / resolveRecipientIdentity. Configure these on the " +
        "instance, or use encryptedWriteStandalone() directly."
    );
  }
  return encryptedWriteStandalone(
    {
      agent: e.pdsAgent,
      senderDid: e.config.did,
      senderStores: e.signalStores,
      resolveRecipientIdentity: e.resolveRecipientIdentity,
    },
    opts
  );
}

export async function encryptedRead<T>(
  e: Etzhayyim & {
    pdsAgent?: AtpAgent;
    signalStores?: LocalStores;
    fetchEnvelope?: StandaloneReadDeps["fetchEnvelope"];
  },
  opts: EncryptedReadOpts
): Promise<EncryptedReadResponse<T>> {
  if (!e.pdsAgent || !e.signalStores) {
    throw new Error(
      "[etzhayyim-sdk/encrypted] Etzhayyim instance missing pdsAgent / " +
        "signalStores. Configure these on the instance, or use " +
        "encryptedReadStandalone() directly."
    );
  }
  return encryptedReadStandalone<T>(
    {
      agent: e.pdsAgent,
      selfDid: e.config.did,
      selfStores: e.signalStores,
      fetchEnvelope: e.fetchEnvelope,
    },
    opts
  );
}
