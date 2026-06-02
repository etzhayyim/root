import { describe, it, expect } from 'vitest';
import {
	createTransferRequest,
	sealArkForTransfer,
	openTransferredArk,
	acceptTransferredArk,
} from './device-transfer.js';
import { enrollAccount, recoverHierarchy, type PutWrap, type GetWrap } from './key-hierarchy.js';

const hex = (b: Uint8Array) => Array.from(b).map((x) => x.toString(16).padStart(2, '0')).join('');
const DID = 'did:web:etzhayyim.com:actor:alice';
const enc = (s: string) => new TextEncoder().encode(s.padEnd(32, '.').slice(0, 32));

function memStore() {
	const m = new Map<string, string>();
	const k = (d: string, c: string) => `${d}::${c}`;
	const put: PutWrap = async (d, c, b) => (m.set(k(d, c), b), true);
	const get: GetWrap = async (d, c) => m.get(k(d, c)) ?? null;
	return { put, get, size: () => m.size };
}

describe('cross-device ARK transfer (ADR-2606014000 multi-device)', () => {
	it('seals on the existing device and unseals on the new device', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest(); // new device
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID); // existing device
		const got = await openTransferredArk(req.transferPrivateKey, sealed, DID); // new device
		expect(hex(got)).toBe(hex(ark));
	});

	it('a different transfer key cannot open the payload', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID);
		const attacker = await createTransferRequest();
		await expect(openTransferredArk(attacker.transferPrivateKey, sealed, DID)).rejects.toThrow();
	});

	it('a wrong account DID (AAD) fails to open', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID);
		await expect(
			openTransferredArk(req.transferPrivateKey, sealed, 'did:web:etzhayyim.com:actor:bob'),
		).rejects.toThrow();
	});

	it('a tampered ciphertext fails to open', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID);
		// flip a char in the base64url ciphertext
		const bad = { ...sealed, ciphertextB64: sealed.ciphertextB64.slice(0, -2) + (sealed.ciphertextB64.endsWith('A') ? 'B' : 'A') };
		await expect(openTransferredArk(req.transferPrivateKey, bad, DID)).rejects.toThrow();
	});

	it('a truncated transfer payload fails to open', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID);
		// Chop the ciphertext down to below iv length → AES-GCM open must fail.
		const truncated = { ...sealed, ciphertextB64: sealed.ciphertextB64.slice(0, 4) };
		await expect(openTransferredArk(req.transferPrivateKey, truncated, DID)).rejects.toThrow();
	});

	it('a malformed ephemeral public key fails to open', async () => {
		const ark = crypto.getRandomValues(new Uint8Array(32));
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(ark, req.transferPublicKeyB64, DID);
		const bad = { ...sealed, ephemeralPublicKeyB64: 'not-a-valid-key' };
		await expect(openTransferredArk(req.transferPrivateKey, bad, DID)).rejects.toThrow();
	});

	it('full accept: new device recovers the SAME account ARK afterwards', async () => {
		const store = memStore();
		// Existing device (device 1) enrolls the account.
		const d1 = await enrollAccount(DID, 'cred-1', enc('device-1-prf'), store.put);
		// New device (device 2) creates a transfer request; device 1 seals the ARK.
		const req = await createTransferRequest();
		const sealed = await sealArkForTransfer(d1.ark, req.transferPublicKeyB64, DID);
		// Device 2 accepts → unseals + re-wraps under ITS OWN passkey PRF + stores.
		const d2 = await acceptTransferredArk(sealed, req.transferPrivateKey, DID, 'cred-2', enc('device-2-prf'), store.put);
		expect(hex(d2.ark)).toBe(hex(d1.ark));
		expect(d2.sessionKey.publicKeyMultibase).toBe(d1.sessionKey.publicKeyMultibase);
		expect(store.size()).toBe(2);
		// Device 2 can now independently recover with its own PRF (no transfer needed).
		const again = await recoverHierarchy(DID, 'cred-2', enc('device-2-prf'), store.get);
		expect(again).not.toBeNull();
		expect(hex(again!.ark)).toBe(hex(d1.ark));
	});
});
