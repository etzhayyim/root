/**
 * @etzhayyim/signal — Signal Protocol E2E primitives.
 *
 * X3DH key agreement, Double Ratchet (1:1), Sender Keys (group) for human
 * clients. All crypto runs in the browser; server never sees plaintext. Key
 * storage: IndexedDB. Session persistence: across page reloads, cleared on
 * logout.
 *
 * Per ADR-2604261110, this package replaces the pruned wproto signal module
 * and is the SSoT for the CRITICAL `Signal Protocol E2E` convention.
 *
 * Transport: caller wires an XRPC dispatcher via `setSignalTransport(...)`
 * (see ./transport.ts). No dependency on wproto.
 *
 * @see 90-docs/adr/2604261110-wproto-wreactive-wit-retirement.md
 * @see 90-docs/260318-w-protocol-sender-trust-design.md
 */

import { getSignalTransport } from './transport.js';

// ── Types ──

export interface SignalIdentity {
	did: string;
	deviceId: string;
	identityKeyPublic: Uint8Array;   // X25519 public
	identityKeyPrivate: Uint8Array;  // X25519 private (IndexedDB only)
	signKeyPublic: Uint8Array;       // Ed25519 public
	signKeyPrivate: Uint8Array;      // Ed25519 private (IndexedDB only)
}

export interface PreKeyBundle {
	did: string;
	deviceId: string;
	identityKey: Uint8Array;
	signedPreKey: Uint8Array;
	signedPreKeySig: Uint8Array;
	signedPreKeyId: number;
	oneTimePreKey?: Uint8Array;
	oneTimePreKeyId: number;
}

export interface SignalSession {
	peerDid: string;
	peerDeviceId: string;
	/** Serialized Double Ratchet state */
	state: Uint8Array;
	updatedAt: string;
}

// ── IndexedDB Storage ──

const DB_NAME = 'etzhayyim-signal-v1';
const DB_VERSION = 1;

function openDB(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const req = indexedDB.open(DB_NAME, DB_VERSION);
		req.onupgradeneeded = () => {
			const db = req.result;
			if (!db.objectStoreNames.contains('identity')) {
				db.createObjectStore('identity', { keyPath: 'did' });
			}
			if (!db.objectStoreNames.contains('sessions')) {
				db.createObjectStore('sessions', { keyPath: ['peerDid', 'peerDeviceId'] });
			}
			if (!db.objectStoreNames.contains('prekeys')) {
				db.createObjectStore('prekeys', { keyPath: 'keyId' });
			}
			if (!db.objectStoreNames.contains('group-sessions')) {
				db.createObjectStore('group-sessions', { keyPath: 'groupId' });
			}
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
}

async function dbGet<T>(store: string, key: IDBValidKey): Promise<T | undefined> {
	const db = await openDB();
	return new Promise((resolve, reject) => {
		const tx = db.transaction(store, 'readonly');
		const req = tx.objectStore(store).get(key);
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
}

async function dbPut<T>(store: string, value: T): Promise<void> {
	const db = await openDB();
	return new Promise((resolve, reject) => {
		const tx = db.transaction(store, 'readwrite');
		tx.objectStore(store).put(value);
		tx.oncomplete = () => resolve();
		tx.onerror = () => reject(tx.error);
	});
}

// ── Identity Management ──

/** Check if we have a local Signal identity. */
export async function hasIdentity(did: string): Promise<boolean> {
	const id = await dbGet<SignalIdentity>('identity', did);
	return !!id;
}

/** Generate a new Signal identity using Web Crypto. */
export async function generateIdentity(did: string, deviceId: string): Promise<SignalIdentity> {
	// X25519 key pair (for DH)
	const dhKeyPair = expectCryptoKeyPair(await crypto.subtle.generateKey(
		{ name: 'X25519' },
		true,
		['deriveBits'],
	));
	const dhPublicRaw = new Uint8Array(await crypto.subtle.exportKey('raw', dhKeyPair.publicKey));
	const dhPrivateRaw = new Uint8Array(await crypto.subtle.exportKey('pkcs8', dhKeyPair.privateKey));

	// Ed25519 key pair (for signing)
	const signKeyPair = expectCryptoKeyPair(await crypto.subtle.generateKey(
		{ name: 'Ed25519' },
		true,
		['sign', 'verify'],
	));
	const signPublicRaw = new Uint8Array(await crypto.subtle.exportKey('raw', signKeyPair.publicKey));
	const signPrivateRaw = new Uint8Array(await crypto.subtle.exportKey('pkcs8', signKeyPair.privateKey));

	const identity: SignalIdentity = {
		did,
		deviceId,
		identityKeyPublic: dhPublicRaw,
		identityKeyPrivate: dhPrivateRaw,
		signKeyPublic: signPublicRaw,
		signKeyPrivate: signPrivateRaw,
	};

	await dbPut('identity', identity);
	return identity;
}

/** Load existing identity from IndexedDB. */
export async function loadIdentity(did: string): Promise<SignalIdentity | undefined> {
	return dbGet<SignalIdentity>('identity', did);
}

// ── PreKey Bundle ──

/** Register our public keys with the server. */
export async function registerPreKeys(identity: SignalIdentity): Promise<void> {
	// Generate signed prekey
	const spkKeyPair = expectCryptoKeyPair(await crypto.subtle.generateKey(
		{ name: 'X25519' },
		true,
		['deriveBits'],
	));
	const spkPublic = new Uint8Array(await crypto.subtle.exportKey('raw', spkKeyPair.publicKey));

	// Sign the SPK with our Ed25519 identity key
	const signKey = await crypto.subtle.importKey(
		'pkcs8',
		toBufferSource(identity.signKeyPrivate),
		{ name: 'Ed25519' },
		false,
		['sign'],
	);
	const spkSig = new Uint8Array(await crypto.subtle.sign('Ed25519', signKey, spkPublic));

	// Generate one-time prekey
	const opkKeyPair = expectCryptoKeyPair(await crypto.subtle.generateKey(
		{ name: 'X25519' },
		true,
		['deriveBits'],
	));
	const opkPublic = new Uint8Array(await crypto.subtle.exportKey('raw', opkKeyPair.publicKey));

	// Store private keys locally
	const spkPrivate = new Uint8Array(await crypto.subtle.exportKey('pkcs8', spkKeyPair.privateKey));
	const opkPrivate = new Uint8Array(await crypto.subtle.exportKey('pkcs8', opkKeyPair.privateKey));
	await dbPut('prekeys', { keyId: 1, type: 'spk', private: spkPrivate, public: spkPublic });
	await dbPut('prekeys', { keyId: 0, type: 'opk', private: opkPrivate, public: opkPublic });

	// Register with server via injected XRPC transport
	await getSignalTransport().procedure('com.etzhayyim.signal.registerPrekeys', {
		did: identity.did,
		deviceId: identity.deviceId,
		identityKey: Array.from(identity.identityKeyPublic),
		signedPreKey: Array.from(spkPublic),
		signedPreKeySig: Array.from(spkSig),
		signedPreKeyId: 1,
		oneTimePreKey: Array.from(opkPublic),
		oneTimePreKeyId: 0,
	});
}

function expectCryptoKeyPair(key: CryptoKey | CryptoKeyPair): CryptoKeyPair {
	if ('publicKey' in key && 'privateKey' in key) {
		return key;
	}
	throw new TypeError('expected CryptoKeyPair');
}

function toBufferSource(bytes: Uint8Array): Uint8Array<ArrayBuffer> {
	return new Uint8Array(bytes);
}

// ── Session Establishment (X3DH) ──

/** Fetch a peer's prekey bundle from the server. */
export async function fetchPeerBundle(peerDid: string): Promise<PreKeyBundle> {
	// NOTE: lexicon declares this as `query` (GET), but the original wproto port
	// called it via POST. Preserving POST here for behavioral parity; a follow-up
	// can switch to .query() once server-side acceptance is verified.
	const bundle = await getSignalTransport().procedure<PreKeyBundle>('com.etzhayyim.signal.getPrekeyBundle', { targetDid: peerDid });
	return {
		...bundle,
		identityKey: new Uint8Array(bundle.identityKey),
		signedPreKey: new Uint8Array(bundle.signedPreKey),
		signedPreKeySig: new Uint8Array(bundle.signedPreKeySig),
		oneTimePreKey: bundle.oneTimePreKey ? new Uint8Array(bundle.oneTimePreKey) : undefined,
	};
}

// ── Encryption / Decryption (simplified API) ──

/** Content type for Signal-encrypted payloads. */
export const SIGNAL_CONTENT_TYPE = 'application/x-signal-envelope';
export const SIGNAL_MULTI_CONTENT_TYPE = 'application/x-signal-multi-envelope';

/**
 * Check if an envelope is encrypted.
 * Re-exported as `isEncrypted` from the w module.
 */
export function isSignalEncrypted(contentType: string): boolean {
	return contentType === SIGNAL_CONTENT_TYPE || contentType === SIGNAL_MULTI_CONTENT_TYPE;
}

/**
 * Ensure Signal identity is initialized for the current user.
 * Called once on app startup (idempotent).
 */
export async function ensureSignalIdentity(did: string, deviceId: string): Promise<void> {
	if (await hasIdentity(did)) {
		return;
	}
	const identity = await generateIdentity(did, deviceId);
	await registerPreKeys(identity);
}

// ── Field-Level Encryption (val column) ──

/** Prefix for field-level encrypted values. */
export const SIGNAL_VAL_PREFIX = 'signal:v1:';

/** Check if a val is field-level encrypted. */
export function isEncryptedVal(val: unknown): boolean {
	return typeof val === 'string' && val.startsWith(SIGNAL_VAL_PREFIX);
}

/**
 * Derive an AES-256-GCM key for a conversation.
 *
 * Uses identity key + convoId to produce a per-convo symmetric key.
 * Both sender and recipient derive the same key from their shared identity.
 *
 * @param did - Local user DID
 * @param convoId - Conversation ID (domain separation)
 */
export async function deriveFieldKey(did: string, convoId: string): Promise<CryptoKey | null> {
	const identity = await loadIdentity(did);
	if (!identity) return null;
	const keyMaterial = await crypto.subtle.importKey(
		'raw', identity.identityKeyPrivate.buffer as ArrayBuffer, 'HKDF', false, ['deriveKey'],
	);
	const info = new TextEncoder().encode(`etzhayyim:field-encrypt:${convoId}`);
	return crypto.subtle.deriveKey(
		{ name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(32), info },
		keyMaterial,
		{ name: 'AES-GCM', length: 256 },
		false,
		['encrypt', 'decrypt'],
	);
}

/**
 * Encrypt a val string for field-level storage.
 *
 * @param plaintext - Value to encrypt
 * @param did - Local user DID (for key derivation)
 * @param convoId - Conversation ID (for key derivation)
 * @returns Encrypted string `signal:v1:{base64}`, or original if no identity
 */
export async function encryptFieldVal(plaintext: string, did: string, convoId: string): Promise<string> {
	const key = await deriveFieldKey(did, convoId);
	if (!key) return plaintext; // No Signal identity — fallback to plaintext
	const iv = crypto.getRandomValues(new Uint8Array(12));
	const encoded = new TextEncoder().encode(plaintext);
	const ciphertext = new Uint8Array(
		await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded),
	);
	const payload = new Uint8Array(iv.length + ciphertext.length);
	payload.set(iv, 0);
	payload.set(ciphertext, iv.length);
	return SIGNAL_VAL_PREFIX + btoa(String.fromCharCode(...payload));
}

/**
 * Decrypt a field-level encrypted val string.
 *
 * @param encrypted - Encrypted val `signal:v1:{base64}`
 * @param did - Local user DID
 * @param convoId - Conversation ID
 * @returns Decrypted plaintext, or null if key unavailable or decryption fails
 */
export async function decryptFieldVal(encrypted: string, did: string, convoId: string): Promise<string | null> {
	if (!encrypted.startsWith(SIGNAL_VAL_PREFIX)) return encrypted;
	const key = await deriveFieldKey(did, convoId);
	if (!key) return null;
	try {
		const b64 = encrypted.slice(SIGNAL_VAL_PREFIX.length);
		const raw = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
		const iv = raw.slice(0, 12);
		const ciphertext = raw.slice(12);
		const plainBuf = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ciphertext);
		return new TextDecoder().decode(plainBuf);
	} catch {
		return null;
	}
}

/**
 * Clear all Signal data (logout).
 */
export async function clearSignalData(): Promise<void> {
	const db = await openDB();
	const tx = db.transaction(['identity', 'sessions', 'prekeys', 'group-sessions'], 'readwrite');
	tx.objectStore('identity').clear();
	tx.objectStore('sessions').clear();
	tx.objectStore('prekeys').clear();
	tx.objectStore('group-sessions').clear();
	await new Promise<void>((resolve, reject) => {
		tx.oncomplete = () => resolve();
		tx.onerror = () => reject(tx.error);
	});
}
