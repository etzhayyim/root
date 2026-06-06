import { describe, it, expect } from 'vitest';
import { deriveSessionKeyPair, base58btcDecode } from './session-key.js';
import {
	buildProfileCacao,
	siweMessage,
	signCacaoEd25519,
	signCacaoSiwe,
	didPkhEip155,
	graphResource,
	CAP_DATOM_TRANSACT,
	type Eip1193Provider,
} from './cacao.js';

const ARK = new Uint8Array(32).fill(0x42);

function ed25519PubFromDidKey(didKey: string): Uint8Array {
	const decoded = base58btcDecode(didKey.replace('did:key:z', ''));
	// 0xed 0x01 multicodec prefix + 32-byte key
	return decoded.slice(2);
}

const PARAMS = {
	iat: '2026-06-06T00:00:00.000Z',
	exp: '2026-06-06T00:15:00.000Z',
	nonce: 'deadbeef',
	capabilities: [CAP_DATOM_TRANSACT],
	graphs: [graphResource('bafyreigh2akiscaildc')],
};

describe('CACAO client builder/signer (ADR-2606060000)', () => {
	it('builds a profile CACAO bound to the apex origin', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const c = buildProfileCacao({ iss: sk.didKey, ...PARAMS });
		expect(c.p.aud).toBe('did:web:etzhayyim.com');
		expect(c.p.domain).toBe('etzhayyim.com');
		expect(c.p.resources).toContain(CAP_DATOM_TRANSACT);
		expect(c.h.t).toBe('eip4361');
	});

	it('siweMessage uses the canonical kotoba-auth layout', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const c = buildProfileCacao({ iss: sk.didKey, ...PARAMS });
		const msg = siweMessage(c);
		expect(msg).toMatch(/^etzhayyim\.com wants you to sign in with your Ethereum account:\n/);
		expect(msg).toMatch(/\nURI: did:web:etzhayyim\.com\n/);
		expect(msg).toMatch(/\nChain ID: 1\n/); // did:key → CAIP-122 default
		expect(msg).toMatch(/\nNonce: deadbeef\n/);
		expect(msg).toMatch(/\nResources:\n- kotoba:\/\/op\/datom:transact\n/);
	});

	it('EdDSA signature verifies against the key embedded in the did:key', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const c = await signCacaoEd25519(buildProfileCacao({ iss: sk.didKey, ...PARAMS }), sk);
		expect(c.s.t).toBe('EdDSA');
		const pub = ed25519PubFromDidKey(sk.didKey);
		const key = await crypto.subtle.importKey('raw', pub, { name: 'Ed25519' }, false, ['verify']);
		const sig = Uint8Array.from(c.s.s.match(/.{2}/g)!.map((h) => parseInt(h, 16)));
		const ok = await crypto.subtle.verify(
			{ name: 'Ed25519' },
			key,
			sig,
			new TextEncoder().encode(siweMessage(c)),
		);
		expect(ok).toBe(true);
	});

	it('refuses to EdDSA-sign when iss is not the session did:key', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const c = buildProfileCacao({ iss: 'did:key:zSomeoneElse', ...PARAMS });
		await expect(signCacaoEd25519(c, sk)).rejects.toThrow();
	});

	it('didPkhEip155 produces a lowercase Base-mainnet did:pkh', () => {
		expect(didPkhEip155('0xAbC0000000000000000000000000000000000001')).toBe(
			'did:pkh:eip155:8453:0xabc0000000000000000000000000000000000001',
		);
	});

	it('SIWE/eip191 signing calls personal_sign over the SIWE plaintext', async () => {
		const address = '0xabc0000000000000000000000000000000000001';
		let seenMsg = '';
		const provider: Eip1193Provider = {
			async request({ method, params }) {
				expect(method).toBe('personal_sign');
				seenMsg = (params as string[])[0];
				return ('0x' + '11'.repeat(65)) as never;
			},
		};
		const c = buildProfileCacao({ iss: didPkhEip155(address), ...PARAMS });
		const signed = await signCacaoSiwe(c, provider, address);
		expect(signed.s.t).toBe('eip191');
		expect(seenMsg).toBe(siweMessage(c));
		expect(seenMsg).toMatch(new RegExp(`\\n${address}\\n`));
		expect(seenMsg).toMatch(/\nChain ID: 8453\n/);
	});
});
