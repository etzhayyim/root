/**
 * Cross-device ARK transfer (ADR-2606014000 multi-device, follow-up leg).
 *
 * Adding a brand-new PHYSICAL device can't use the same-device path (the new
 * device has its own passkey PRF but no ARK). This module moves the ARK from an
 * already-unlocked device to a new one over an HPKE-style sealed envelope, so the
 * ARK is never exposed in plaintext to the channel (QR / relay) or the server:
 *
 *   new device:      createTransferRequest()  → ephemeral X25519 keypair; show pubkey (QR)
 *   existing device: sealArkForTransfer(ark, newPubKey, accountDid) → sealed payload
 *   new device:      acceptTransferredArk(payload, transferPrivateKey, …) → unseal ARK,
 *                    re-wrap under its OWN passkey PRF (enrollDevice), derive hierarchy.
 *
 * Construction: ephemeral X25519 ECDH → HKDF-SHA256 → AES-256-GCM (AAD = account
 * DID) — the same ECIES shape as the Rust `kotoba_crypto::hpke`.
 */

import { unwrapArk, wrapArk, deriveStorageKey, deriveSignalSeed } from './key-tree.js';
import { deriveSessionKeyPair } from './session-key.js';
import type { KeyHierarchy, PutWrap } from './key-hierarchy.js';

const enc = new TextEncoder();
const TRANSFER_INFO = 'kotoba/device-transfer/v1';
const HKDF_ZERO_SALT = new Uint8Array(32);

function bs(u: Uint8Array): Uint8Array<ArrayBuffer> {
	const out = new Uint8Array(u.byteLength);
	out.set(u);
	return out as Uint8Array<ArrayBuffer>;
}
function b64u(bytes: Uint8Array): string {
	let s = '';
	for (const x of bytes) s += String.fromCharCode(x);
	return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
function unb64u(s: string): Uint8Array {
	const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
	const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/') + pad);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}

async function ecdhAesKey(
	privateKey: CryptoKey,
	peerPublicRaw: Uint8Array,
	usage: KeyUsage[],
): Promise<CryptoKey> {
	const peer = await crypto.subtle.importKey('raw', bs(peerPublicRaw), { name: 'X25519' }, false, []);
	const ss = new Uint8Array(
		await crypto.subtle.deriveBits({ name: 'X25519', public: peer }, privateKey, 256),
	);
	const hk = await crypto.subtle.importKey('raw', bs(ss), 'HKDF', false, ['deriveBits']);
	const raw = new Uint8Array(
		await crypto.subtle.deriveBits(
			{ name: 'HKDF', hash: 'SHA-256', salt: bs(HKDF_ZERO_SALT), info: bs(enc.encode(TRANSFER_INFO)) },
			hk,
			256,
		),
	);
	return crypto.subtle.importKey('raw', bs(raw), 'AES-GCM', false, usage);
}

export interface TransferRequest {
	/** Kept in memory on the NEW device; never transmitted. */
	transferPrivateKey: CryptoKey;
	/** base64url X25519 public key — show as QR / hand to the existing device. */
	transferPublicKeyB64: string;
}

/** NEW device: generate an ephemeral X25519 keypair to receive the ARK. */
export async function createTransferRequest(): Promise<TransferRequest> {
	const kp = (await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits'])) as CryptoKeyPair;
	const pub = new Uint8Array(await crypto.subtle.exportKey('raw', kp.publicKey));
	return { transferPrivateKey: kp.privateKey, transferPublicKeyB64: b64u(pub) };
}

export interface SealedTransfer {
	/** Ephemeral sender X25519 public key (base64url). */
	ephemeralPublicKeyB64: string;
	/** `iv(12) || ciphertext || tag(16)` of the ARK, base64url. */
	ciphertextB64: string;
}

/** EXISTING device: seal the ARK to the new device's transfer public key. */
export async function sealArkForTransfer(
	ark: Uint8Array,
	transferPublicKeyB64: string,
	accountDid: string,
): Promise<SealedTransfer> {
	const eph = (await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits'])) as CryptoKeyPair;
	const ephPub = new Uint8Array(await crypto.subtle.exportKey('raw', eph.publicKey));
	const key = await ecdhAesKey(eph.privateKey, unb64u(transferPublicKeyB64), ['encrypt']);
	const iv = crypto.getRandomValues(new Uint8Array(12));
	const ct = new Uint8Array(
		await crypto.subtle.encrypt({ name: 'AES-GCM', iv: bs(iv), additionalData: bs(enc.encode(accountDid)) }, key, bs(ark)),
	);
	const payload = new Uint8Array(12 + ct.length);
	payload.set(iv);
	payload.set(ct, 12);
	return { ephemeralPublicKeyB64: b64u(ephPub), ciphertextB64: b64u(payload) };
}

/** NEW device: unseal the ARK from a transfer payload. */
export async function openTransferredArk(
	transferPrivateKey: CryptoKey,
	sealed: SealedTransfer,
	accountDid: string,
): Promise<Uint8Array> {
	const key = await ecdhAesKey(transferPrivateKey, unb64u(sealed.ephemeralPublicKeyB64), ['decrypt']);
	const payload = unb64u(sealed.ciphertextB64);
	const iv = payload.slice(0, 12);
	const body = payload.slice(12);
	const pt = await crypto.subtle.decrypt(
		{ name: 'AES-GCM', iv: bs(iv), additionalData: bs(enc.encode(accountDid)) },
		key,
		bs(body),
	);
	return new Uint8Array(pt);
}

/**
 * NEW device, full accept: unseal the transferred ARK, re-wrap it under this
 * device's OWN passkey PRF (so it can recover independently thereafter), store
 * the wrap, and derive the hierarchy. Returns the established hierarchy.
 */
export async function acceptTransferredArk(
	sealed: SealedTransfer,
	transferPrivateKey: CryptoKey,
	accountDid: string,
	newCredentialId: string,
	newPrfSecret: Uint8Array,
	put: PutWrap,
): Promise<KeyHierarchy> {
	const ark = await openTransferredArk(transferPrivateKey, sealed, accountDid);
	const wrapped = await wrapArk(newPrfSecret, ark, accountDid);
	const ok = await put(accountDid, newCredentialId, b64u(wrapped));
	if (!ok) throw new Error('failed to store wrapped ARK for new device');
	const [storageKey, signalSeed, sessionKey] = await Promise.all([
		deriveStorageKey(ark),
		deriveSignalSeed(ark),
		deriveSessionKeyPair(ark),
	]);
	return { ark, storageKey, signalSeed, sessionKey };
}

// `unwrapArk` is re-exported for symmetry / advanced callers that already hold a wrap.
export { unwrapArk };
