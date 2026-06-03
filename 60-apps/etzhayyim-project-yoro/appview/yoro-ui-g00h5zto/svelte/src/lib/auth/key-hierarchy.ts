/**
 * End-to-end orchestration of the passkey-rooted key hierarchy (ADR-2606014000).
 * Ties L0 (PRF) → L1 (ARK + wrapped-ARK store) → L2 (purpose keys) → session key.
 *
 * Transport is injected (`PutWrap`/`GetWrap`) so this is unit-testable without a
 * live server; `account.ts` provides the real fetch-based implementation against
 * kotoba-server `com.etzhayyim.account.{put,get}.wrapped.ark`.
 *
 * Multi-device semantics are explicit and correct:
 *   • enrollAccount   — FIRST device of a NEW account: mint ARK, wrap, store.
 *   • recoverHierarchy— a device whose passkey wrap exists: unwrap → derive.
 *                       Returns null if THIS device is not enrolled (→ caller
 *                       runs add-device from another device, or guardian recovery;
 *                       it must NOT silently mint a new ARK and orphan existing data).
 *   • enrollDevice    — add a device: re-wrap an already-recovered ARK under the
 *                       new passkey's PRF (called from an already-unlocked device).
 */

import {
	generateArk,
	wrapArk,
	unwrapArk,
	deriveStorageKey,
	deriveSignalSeed,
} from './key-tree.js';
import { deriveSessionKeyPair, type SessionKey } from './session-key.js';

export interface KeyHierarchy {
	ark: Uint8Array;
	storageKey: Uint8Array;
	signalSeed: Uint8Array;
	sessionKey: SessionKey;
}

/** Persist `wrappedArkB64` for (did, credentialId). Returns success. */
export type PutWrap = (did: string, credentialId: string, wrappedArkB64: string) => Promise<boolean>;
/** Fetch the stored wrap for (did, credentialId), or null if none. */
export type GetWrap = (did: string, credentialId: string) => Promise<string | null>;

function b64uEncode(bytes: Uint8Array): string {
	let bin = '';
	for (const b of bytes) bin += String.fromCharCode(b);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
function b64uDecode(s: string): Uint8Array {
	const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
	const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/') + pad);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}

async function deriveAll(ark: Uint8Array): Promise<KeyHierarchy> {
	const [storageKey, signalSeed, sessionKey] = await Promise.all([
		deriveStorageKey(ark),
		deriveSignalSeed(ark),
		deriveSessionKeyPair(ark),
	]);
	return { ark, storageKey, signalSeed, sessionKey };
}

/** FIRST device of a NEW account: mint a random ARK, wrap it under this passkey's
 *  PRF, store the wrap, and derive the hierarchy. */
export async function enrollAccount(
	accountDid: string,
	credentialId: string,
	prfSecret: Uint8Array,
	put: PutWrap,
): Promise<KeyHierarchy> {
	const ark = generateArk();
	const wrapped = await wrapArk(prfSecret, ark, accountDid);
	const ok = await put(accountDid, credentialId, b64uEncode(wrapped));
	if (!ok) throw new Error('failed to store wrapped ARK');
	return deriveAll(ark);
}

/** Recover the hierarchy on a device whose passkey wrap is stored. Returns null
 *  if this device is not enrolled (caller must add-device or guardian-recover). */
export async function recoverHierarchy(
	accountDid: string,
	credentialId: string,
	prfSecret: Uint8Array,
	get: GetWrap,
): Promise<KeyHierarchy | null> {
	const wrappedB64 = await get(accountDid, credentialId);
	if (!wrappedB64) return null;
	const ark = await unwrapArk(prfSecret, b64uDecode(wrappedB64), accountDid);
	return deriveAll(ark);
}

/** Add a device: wrap an already-recovered ARK under a new passkey's PRF and
 *  store it. Run from a device that already holds the ARK. */
export async function enrollDevice(
	accountDid: string,
	newCredentialId: string,
	newPrfSecret: Uint8Array,
	ark: Uint8Array,
	put: PutWrap,
): Promise<boolean> {
	const wrapped = await wrapArk(newPrfSecret, ark, accountDid);
	return put(accountDid, newCredentialId, b64uEncode(wrapped));
}
