import { describe, it, expect } from 'vitest';
import { deriveSessionKeyPair } from './session-key.js';
import { signInWithPasskey, signInWithWallet, type VerifyCacaoResult } from './profile-signin.js';
import { siweMessage, type Eip1193Provider } from './cacao.js';

const ARK = new Uint8Array(32).fill(0x42);
const GRAPH = 'bafyreigh2akiscaildc';
const NOW = Date.parse('2026-06-06T00:00:00.000Z');

function deps(captured: { url?: string; body?: any }, response: VerifyCacaoResult, status = 200) {
	return {
		now: () => NOW,
		nonce: () => 'deadbeef',
		origin: 'https://etzhayyim.com',
		fetch: (async (url: string, init: RequestInit) => {
			captured.url = url;
			captured.body = JSON.parse(init.body as string);
			return new Response(JSON.stringify(response), { status });
		}) as unknown as typeof fetch,
	};
}

describe('profile sign-in orchestrator (ADR-2606060000)', () => {
	it('passkey: posts a same-origin EdDSA CACAO to verifyCacao and returns the verdict', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const cap = {};
		const res = await signInWithPasskey(sk, GRAPH, deps(cap, {
			valid: true,
			did: sk.didKey,
			method: 'ed25519-local',
			scope: { capabilities: ['kotoba://op/datom:transact'], graphs: [`kotoba://graph/${GRAPH}`] },
		}));
		expect((cap as any).url).toBe('https://etzhayyim.com/xrpc/com.etzhayyim.authz.verifyCacao');
		expect((cap as any).body.cacao.s.t).toBe('EdDSA');
		expect((cap as any).body.cacao.p.iss).toBe(sk.didKey);
		expect((cap as any).body.cacao.p.aud).toBe('did:web:etzhayyim.com');
		expect((cap as any).body.cacao.p.resources).toContain(`kotoba://graph/${GRAPH}`);
		expect(res.valid).toBe(true);
		expect(res.did).toBe(sk.didKey);
	});

	it('passkey: iat/exp are strict-UTC Z and exp = iat + ttl', async () => {
		const sk = await deriveSessionKeyPair(ARK);
		const cap = {};
		await signInWithPasskey(sk, GRAPH, { ...deps(cap, { valid: true }), ttlSecs: 600 });
		const p = (cap as any).body.cacao.p;
		expect(p.iat).toBe('2026-06-06T00:00:00.000Z');
		expect(p.exp).toBe('2026-06-06T00:10:00.000Z'); // +600s
	});

	it('wallet: posts an eip191 CACAO and returns the signed token + gated verdict', async () => {
		const address = '0xabc0000000000000000000000000000000000001';
		const provider: Eip1193Provider = {
			async request() {
				return ('0x' + '11'.repeat(65)) as never;
			},
		};
		const cap = {};
		const res = await signInWithWallet(provider, address, GRAPH, {
			...deps(cap, { valid: false, gated: true, sigType: 'eip191' }, 202),
		});
		expect((cap as any).body.cacao.s.t).toBe('eip191');
		expect((cap as any).body.cacao.p.iss).toBe(`did:pkh:eip155:8453:${address}`);
		expect(res.gated).toBe(true);
		expect(res.cacao.s.s).toBe('0x' + '11'.repeat(65));
		// the returned token carries the exact SIWE plaintext that was signed
		expect(siweMessage(res.cacao)).toMatch(new RegExp(`\\n${address}\\n`));
	});
});
