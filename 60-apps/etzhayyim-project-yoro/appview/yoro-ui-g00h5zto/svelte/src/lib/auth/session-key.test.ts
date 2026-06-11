import { describe, it, expect } from 'vitest';
import {
	deriveSessionKeyPair,
	base58btcEncode,
	base58btcDecode,
	ed25519PublicKeyMultibase,
} from './session-key.js';

const hex = (b: Uint8Array) => Array.from(b).map((x) => x.toString(16).padStart(2, '0')).join('');

describe('Ed25519 session key (ADR-2606014500 C-2 client)', () => {
	it('base58btc encode/decode round-trips (incl. leading zeros)', () => {
		for (const v of [[0, 0, 1, 2, 3], [255, 254, 0, 1], [0, 0, 0], [42]]) {
			const bytes = Uint8Array.from(v);
			expect(hex(base58btcDecode(base58btcEncode(bytes)))).toBe(hex(bytes));
		}
	});

	it('base58 decode rejects an invalid alphabet char', () => {
		// '0', 'O', 'I', 'l' are NOT in the base58btc alphabet.
		expect(() => base58btcDecode('z0OIl')).toThrow();
	});

	it('base58 preserves leading-zero bytes as leading "1"s', () => {
		const bytes = Uint8Array.from([0, 0, 5, 9]);
		const enc = base58btcEncode(bytes);
		expect(enc.startsWith('11')).toBe(true);
		expect(hex(base58btcDecode(enc))).toBe(hex(bytes));
	});

	it('decodes a real W3C did:key Ed25519 fingerprint to 0xed01 || 32-byte key', () => {
		// Canonical did:key spec example.
		const mb = 'z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK';
		const decoded = base58btcDecode(mb.slice(1)); // strip 'z' multibase prefix
		expect(decoded.length).toBe(34); // 2-byte multicodec + 32-byte key
		expect(decoded[0]).toBe(0xed);
		expect(decoded[1]).toBe(0x01);
	});

	it('multibase form has the ed25519 multicodec and z prefix', () => {
		const pub = new Uint8Array(32).fill(9);
		const mb = ed25519PublicKeyMultibase(pub);
		expect(mb.startsWith('z')).toBe(true);
		const decoded = base58btcDecode(mb.slice(1));
		expect(decoded[0]).toBe(0xed);
		expect(decoded[1]).toBe(0x01);
		expect(hex(decoded.slice(2))).toBe(hex(pub));
	});

	it('derives a deterministic session keypair from the ARK', async () => {
		const ark = new Uint8Array(32).fill(0x11);
		const a = await deriveSessionKeyPair(ark);
		const b = await deriveSessionKeyPair(ark);
		expect(a.publicKeyMultibase).toBe(b.publicKeyMultibase);
		expect(a.didKey).toBe(`did:key:${a.publicKeyMultibase}`);
		expect(a.publicKey.length).toBe(32);
		// did:key is the trustless form — worker accepts a z… multibase 40–120 chars.
		expect(a.publicKeyMultibase.length).toBeGreaterThanOrEqual(40);
		expect(a.publicKeyMultibase.length).toBeLessThanOrEqual(120);
	});

	it('different ARKs yield different session keys', async () => {
		const a = await deriveSessionKeyPair(new Uint8Array(32).fill(1));
		const b = await deriveSessionKeyPair(new Uint8Array(32).fill(2));
		expect(a.publicKeyMultibase).not.toBe(b.publicKeyMultibase);
	});

	it('the derived key actually signs (Ed25519)', async () => {
		const ark = new Uint8Array(32).fill(0x11);
		const { privateKey, publicKey } = await deriveSessionKeyPair(ark);
		const msg = new TextEncoder().encode('cacao-session-payload');
		const sig = new Uint8Array(await crypto.subtle.sign({ name: 'Ed25519' }, privateKey, msg));
		const pub = await crypto.subtle.importKey('raw', publicKey, { name: 'Ed25519' }, false, ['verify']);
		expect(await crypto.subtle.verify({ name: 'Ed25519' }, pub, sig, msg)).toBe(true);
	});

	it('signSessionPoP produces a verifiable EdDSA JWS (C-3)', async () => {
		const { signSessionPoP } = await import('./session-key.js');
		const ark = new Uint8Array(32).fill(0x11);
		const sk = await deriveSessionKeyPair(ark);
		const did = 'did:web:etzhayyim.com:actor:alice';
		const token = await signSessionPoP(sk, did, 1_750_000_000, 1_750_003_600, { htu: '/xrpc/x' });
		const [h, p, s] = token.split('.');
		expect(h && p && s).toBeTruthy();
		// header/payload decode
		const dec = (b64: string) => JSON.parse(new TextDecoder().decode(base58Free(b64)));
		expect(dec(h).alg).toBe('EdDSA');
		expect(dec(p).iss).toBe(did);
		expect(dec(p).htu).toBe('/xrpc/x');
		// signature verifies against the session public key
		const pub = await crypto.subtle.importKey('raw', sk.publicKey, { name: 'Ed25519' }, false, ['verify']);
		const sigBytes = base58Free(s);
		const ok = await crypto.subtle.verify({ name: 'Ed25519' }, pub, sigBytes, new TextEncoder().encode(`${h}.${p}`));
		expect(ok).toBe(true);
	});
});

// base64url → bytes (test helper; the module's own encoder is exercised above).
function base58Free(b64: string): Uint8Array {
	const pad = b64.length % 4 === 0 ? '' : '='.repeat(4 - (b64.length % 4));
	const bin = atob(b64.replace(/-/g, '+').replace(/_/g, '/') + pad);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}
