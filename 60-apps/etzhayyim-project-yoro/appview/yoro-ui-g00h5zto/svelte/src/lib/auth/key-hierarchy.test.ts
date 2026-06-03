import { describe, it, expect } from 'vitest';
import {
	enrollAccount,
	recoverHierarchy,
	enrollDevice,
	type PutWrap,
	type GetWrap,
} from './key-hierarchy.js';

const hex = (b: Uint8Array) => Array.from(b).map((x) => x.toString(16).padStart(2, '0')).join('');

/** In-memory wrapped-ARK store standing in for kotoba-server account_xrpc. */
function memStore() {
	const m = new Map<string, string>();
	const key = (did: string, cred: string) => `${did}::${cred}`;
	const put: PutWrap = async (did, cred, b64) => {
		m.set(key(did, cred), b64);
		return true;
	};
	const get: GetWrap = async (did, cred) => m.get(key(did, cred)) ?? null;
	return { put, get, size: () => m.size };
}

const DID = 'did:web:etzhayyim.com:actor:alice';
const enc = (s: string) => new TextEncoder().encode(s.padEnd(32, '.').slice(0, 32));

describe('key hierarchy end-to-end (ADR-2606014000 L0→L2)', () => {
	it('enroll then recover yields the SAME keys', async () => {
		const store = memStore();
		const prf = enc('device-1-prf');
		const enrolled = await enrollAccount(DID, 'cred-1', prf, store.put);
		const recovered = await recoverHierarchy(DID, 'cred-1', prf, store.get);
		expect(recovered).not.toBeNull();
		expect(hex(recovered!.ark)).toBe(hex(enrolled.ark));
		expect(hex(recovered!.storageKey)).toBe(hex(enrolled.storageKey));
		expect(hex(recovered!.signalSeed)).toBe(hex(enrolled.signalSeed));
		expect(recovered!.sessionKey.publicKeyMultibase).toBe(enrolled.sessionKey.publicKeyMultibase);
	});

	it('recover on an UN-enrolled device returns null (no silent new ARK)', async () => {
		const store = memStore();
		await enrollAccount(DID, 'cred-1', enc('device-1-prf'), store.put);
		// A different passkey credential that was never enrolled.
		const r = await recoverHierarchy(DID, 'cred-2', enc('device-2-prf'), store.get);
		expect(r).toBeNull();
	});

	it('add-device: enrollDevice re-wraps the SAME ARK for a new passkey', async () => {
		const store = memStore();
		const d1 = await enrollAccount(DID, 'cred-1', enc('device-1-prf'), store.put);
		// Device 1 (holding the ARK) enrolls device 2 under device 2's PRF.
		const ok = await enrollDevice(DID, 'cred-2', enc('device-2-prf'), d1.ark, store.put);
		expect(ok).toBe(true);
		// Device 2 can now recover the SAME account ARK with its own PRF.
		const d2 = await recoverHierarchy(DID, 'cred-2', enc('device-2-prf'), store.get);
		expect(d2).not.toBeNull();
		expect(hex(d2!.ark)).toBe(hex(d1.ark));
		expect(d2!.sessionKey.publicKeyMultibase).toBe(d1.sessionKey.publicKeyMultibase);
		expect(store.size()).toBe(2); // two wraps, one per device
	});

	it('wrong PRF on an enrolled device fails to recover (AEAD)', async () => {
		const store = memStore();
		await enrollAccount(DID, 'cred-1', enc('device-1-prf'), store.put);
		await expect(recoverHierarchy(DID, 'cred-1', enc('attacker-prf'), store.get)).rejects.toThrow();
	});

	it('enrollAccount throws if the wrap store rejects the put', async () => {
		const failingPut: PutWrap = async () => false;
		await expect(enrollAccount(DID, 'cred-1', enc('device-1-prf'), failingPut)).rejects.toThrow(
			/failed to store wrapped ARK/,
		);
	});

	it('enrollDevice propagates the store result', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const okPut: PutWrap = async () => true;
		const failPut: PutWrap = async () => false;
		expect(await enrollDevice(DID, 'cred-2', enc('device-2-prf'), ark, okPut)).toBe(true);
		expect(await enrollDevice(DID, 'cred-2', enc('device-2-prf'), ark, failPut)).toBe(false);
	});

	it('the recovered session key is a usable Ed25519 signer', async () => {
		const store = memStore();
		const h = await enrollAccount(DID, 'cred-1', enc('device-1-prf'), store.put);
		const msg = new TextEncoder().encode('hello');
		const sig = new Uint8Array(await crypto.subtle.sign({ name: 'Ed25519' }, h.sessionKey.privateKey, msg));
		const pub = await crypto.subtle.importKey('raw', h.sessionKey.publicKey, { name: 'Ed25519' }, false, ['verify']);
		expect(await crypto.subtle.verify({ name: 'Ed25519' }, pub, sig, msg)).toBe(true);
	});
});
