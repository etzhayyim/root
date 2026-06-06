import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the app-shell deps so the test is hermetic + fast: the value lives in the
// REAL crypto ceremony (enroll → ARK → Ed25519 session key → EdDSA CACAO).
// `vi.hoisted` shares the mock fns with the hoisted `vi.mock` factories.
const mocks = vi.hoisted(() => ({
	setSession: vi.fn(),
	clearSession: vi.fn(),
	setTokenProvider: vi.fn(),
	stores: {
		isSignedIn: { set: vi.fn() },
		clerkUser: { set: vi.fn() },
		clerkLoaded: { set: vi.fn() },
		sessionToken: { set: vi.fn() },
	},
}));
const { setSession, clearSession, setTokenProvider, stores } = mocks;
vi.mock('$lib/atproto-agent', () => ({
	setSession: mocks.setSession,
	clearSession: mocks.clearSession,
	setTokenProvider: mocks.setTokenProvider,
}));
vi.mock('./stores.js', () => mocks.stores);

import {
	establishCacaoSession,
	mintSessionCacao,
	makeCacaoTokenProvider,
	signOutCacao,
	getCacaoSession,
	sessionKeyFromArk,
	type CacaoSessionDeps,
} from './cacao-session.js';
import { CAP_DATOM_TRANSACT } from './cacao.js';

const PRF = new Uint8Array(32).fill(7);
const ACCOUNT = 'did:web:etzhayyim.com:actor:tester';

let nonceCounter = 0;
function baseDeps(over: Partial<CacaoSessionDeps> = {}): CacaoSessionDeps {
	const store = new Map<string, string>();
	return {
		now: () => 1_750_000_000_000,
		nonce: () => `nonce-${++nonceCounter}`,
		origin: '',
		ttlSecs: 900,
		// in-memory kotoba wrap store (zero-access): first call has no row → enroll.
		getWrap: async (did, cred) => store.get(`${did}:${cred}`) ?? null,
		putWrap: async (did, cred, b64) => {
			store.set(`${did}:${cred}`, b64);
			return true;
		},
		...over,
	};
}

beforeEach(() => {
	nonceCounter = 0;
	vi.clearAllMocks();
	signOutCacao();
	vi.clearAllMocks(); // clear the calls signOutCacao just made
});

describe('mintSessionCacao', () => {
	it('produces an EdDSA, apex-bound CACAO scoped to datom:transact', async () => {
		const key = await sessionKeyFromArk(new Uint8Array(32).fill(3));
		const cacao = await mintSessionCacao(key, {
			now: () => 1_750_000_000_000,
			nonce: () => 'n1',
		});
		expect(cacao.s.t).toBe('EdDSA');
		expect(cacao.s.s).toMatch(/^[0-9a-f]+$/); // hex signature
		expect(cacao.p.iss).toBe(key.didKey);
		expect(cacao.p.aud).toBe('did:web:etzhayyim.com');
		expect(cacao.p.domain).toBe('etzhayyim.com');
		expect(cacao.p.resources).toContain(CAP_DATOM_TRANSACT);
	});
});

describe('establishCacaoSession', () => {
	it('gates (no false session) when the account DID is unknown', async () => {
		const out = await establishCacaoSession(PRF, null, 'cred-1', baseDeps());
		expect(out.status).toBe('gated');
		expect(getCacaoSession()).toBeNull();
		expect(stores.isSignedIn.set).not.toHaveBeenCalledWith(true);
	});

	it('enrolls + verifies end-to-end and flips into a JWT-free signed-in state', async () => {
		const fetchMock = vi.fn(async () => ({
			json: async () => ({
				valid: true,
				did: ACCOUNT,
				sigType: 'EdDSA',
				scope: { capabilities: [CAP_DATOM_TRANSACT], graphs: [] },
			}),
		})) as unknown as typeof fetch;

		const out = await establishCacaoSession(PRF, ACCOUNT, 'cred-1', baseDeps({ fetch: fetchMock }));

		expect(out.status).toBe('verified');
		expect(out.did).toBe(ACCOUNT);
		// posted same-origin to the apex verifier
		expect(fetchMock).toHaveBeenCalledWith(
			'/xrpc/com.etzhayyim.authz.verifyCacao',
			expect.objectContaining({ method: 'POST' }),
		);
		// signed-in via CACAO, NOT a JWT
		expect(stores.isSignedIn.set).toHaveBeenCalledWith(true);
		expect(stores.sessionToken.set).toHaveBeenCalledWith(null);
		expect(setSession).toHaveBeenCalledWith(
			expect.objectContaining({ did: ACCOUNT, accessJwt: '' }),
		);
		expect(setTokenProvider).toHaveBeenCalled(); // CACAO write provider registered
		expect(getCacaoSession()?.accountDid).toBe(ACCOUNT);
	});

	it('reports an apex rejection as error, not a session', async () => {
		const fetchMock = vi.fn(async () => ({
			json: async () => ({ valid: false, reason: 'bad signature' }),
		})) as unknown as typeof fetch;
		const out = await establishCacaoSession(PRF, ACCOUNT, 'cred-1', baseDeps({ fetch: fetchMock }));
		expect(out.status).toBe('error');
		expect(getCacaoSession()).toBeNull();
	});
});

describe('makeCacaoTokenProvider (write-auth)', () => {
	it('returns empty when signed out, and a cacao: token when a key is present', async () => {
		const provider = makeCacaoTokenProvider(() => null, {
			now: () => 1_750_000_000_000,
			nonce: () => 'n',
		});
		expect(await provider()).toBe('');

		const key = await sessionKeyFromArk(new Uint8Array(32).fill(9));
		const provider2 = makeCacaoTokenProvider(() => key, {
			now: () => 1_750_000_000_000,
			nonce: () => 'n2',
		});
		const tok = await provider2();
		expect(tok.startsWith('cacao:')).toBe(true);
		expect(tok.length).toBeGreaterThan('cacao:'.length + 20);
	});
});

describe('signOutCacao', () => {
	it('clears the in-memory session and auth stores', async () => {
		const fetchMock = vi.fn(async () => ({
			json: async () => ({ valid: true, did: ACCOUNT, scope: { capabilities: [CAP_DATOM_TRANSACT], graphs: [] } }),
		})) as unknown as typeof fetch;
		await establishCacaoSession(PRF, ACCOUNT, 'cred-1', baseDeps({ fetch: fetchMock }));
		expect(getCacaoSession()).not.toBeNull();

		signOutCacao();
		expect(getCacaoSession()).toBeNull();
		expect(clearSession).toHaveBeenCalled();
		expect(setTokenProvider).toHaveBeenLastCalledWith(null);
		expect(stores.isSignedIn.set).toHaveBeenLastCalledWith(false);
	});
});
