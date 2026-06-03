import { describe, it, expect } from 'vitest';
import {
	generateArk,
	wrapArk,
	unwrapArk,
	deriveStorageKey,
	deriveSignalSeed,
	deriveSessionSeed,
} from './key-tree.js';

const hex = (b: Uint8Array) => Array.from(b).map((x) => x.toString(16).padStart(2, '0')).join('');

describe('passkey key-tree (ADR-2606014000) — Rust interop', () => {
	// Known-answer vectors computed from the Rust `kotoba_crypto::key_tree`
	// (examples/kat_keytree.rs) with ARK = [0x11; 32]. These MUST match so a key
	// wrapped/derived on the client interoperates with the Rust substrate.
	const ARK_11 = new Uint8Array(32).fill(0x11);
	const KAT = {
		storage: 'c4427c366a1d8210f5a830a187eb020cbafb027367d65462dedb620c800ed9ef',
		signal: '733bfafb37e5df7ffe8942b1c2ad87efd4041ff93a2c5be141825bc7b86ac7e4',
		session: 'de723cd3417f151b14bd524a5ef80d0df708784b3da02bd8eb076e17974fa7a5',
	};

	it('derives the same purpose keys as Rust (HKDF KAT)', async () => {
		expect(hex(await deriveStorageKey(ARK_11))).toBe(KAT.storage);
		expect(hex(await deriveSignalSeed(ARK_11))).toBe(KAT.signal);
		expect(hex(await deriveSessionSeed(ARK_11))).toBe(KAT.session);
	});

	it('purpose keys are distinct', async () => {
		const s = hex(await deriveStorageKey(ARK_11));
		const g = hex(await deriveSignalSeed(ARK_11));
		const k = hex(await deriveSessionSeed(ARK_11));
		expect(new Set([s, g, k]).size).toBe(3);
	});

	const DID = 'did:web:etzhayyim.com:actor:alice';
	const prf = new TextEncoder().encode('webauthn-prf-output-device-1....');

	it('wraps and unwraps the ARK (60-byte layout: iv||ct||tag)', async () => {
		const ark = generateArk();
		const wrapped = await wrapArk(prf, ark, DID);
		expect(wrapped.length).toBe(12 + 32 + 16);
		const recovered = await unwrapArk(prf, wrapped, DID);
		expect(hex(recovered)).toBe(hex(ark));
	});

	it('rejects a wrong account DID (AAD binding)', async () => {
		const ark = generateArk();
		const wrapped = await wrapArk(prf, ark, DID);
		await expect(unwrapArk(prf, wrapped, 'did:web:etzhayyim.com:actor:bob')).rejects.toThrow();
	});

	it('rejects a wrong PRF secret (different device)', async () => {
		const ark = generateArk();
		const wrapped = await wrapArk(prf, ark, DID);
		const otherPrf = new TextEncoder().encode('webauthn-prf-output-device-2....');
		await expect(unwrapArk(otherPrf, wrapped, DID)).rejects.toThrow();
	});

	it('a second device wraps the SAME ARK under its own PRF', async () => {
		const ark = generateArk();
		const prf2 = new TextEncoder().encode('webauthn-prf-output-device-2....');
		const w1 = await wrapArk(prf, ark, DID);
		const w2 = await wrapArk(prf2, ark, DID);
		const a1 = await unwrapArk(prf, w1, DID);
		const a2 = await unwrapArk(prf2, w2, DID);
		expect(hex(a1)).toBe(hex(a2));
	});
});
