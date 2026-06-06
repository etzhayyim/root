/**
 * Site-wide CACAO session — JWT-free interactive auth (ADR-2606061500).
 *
 * Extends the `/profile` same-origin gate (ADR-2606060000) to the GLOBAL header
 * login. The signed-in session is no longer a server-minted `accessJwt`; it is a
 * member-held CACAO ceremony produced ON `etzhayyim.com`:
 *
 *   passkey assertion (same-origin, client challenge)
 *     → PRF secret → ARK (kotoba zero-access wrap store)
 *     → Ed25519 session key (deterministic, never persisted)
 *     → EdDSA-signed CACAO bound to the apex
 *     → POST /xrpc/com.etzhayyim.authz.verifyCacao  (apex verifies locally, no key)
 *
 * The session key lives in memory only and is re-derivable from the passkey, so
 * "the session" is a re-mintable proof of DID control, not a stored bearer token.
 * Writes are authorized by a freshly session-key-signed CACAO per call (see
 * `makeCacaoTokenProvider`), NOT by a JWT.
 *
 * Dependencies (clock, randomness, fetch, origin, wrap-store accessors) are
 * injected so the core (`establishCacaoSession`) is unit-testable without a
 * browser, a passkey, or a live Worker. The browser entrypoint
 * (`signInWithPasskeyCacao`) is a thin WebAuthn wrapper over the core.
 */

import {
	isSignedIn,
	clerkUser,
	clerkLoaded,
	sessionToken,
} from './stores.js';
import { setSession, clearSession, setTokenProvider } from '$lib/atproto-agent';
import { deriveSessionKeyPair, type SessionKey } from './session-key.js';
import { recoverHierarchy, enrollAccount, type GetWrap, type PutWrap } from './key-hierarchy.js';
import {
	buildProfileCacao,
	signCacaoEd25519,
	graphResource,
	CAP_DATOM_TRANSACT,
	type Cacao,
} from './cacao.js';
import { accountPrfSalt, prfEvalExtension, extractPrfSecret } from './prf.js';

const VERIFY_PATH = '/xrpc/com.etzhayyim.authz.verifyCacao';
/** Apex rpId for the same-origin WebAuthn ceremony (no authn subdomain). */
const APEX_RP_ID = 'etzhayyim.com';
/** Actor-profile graph CID the default capability is scoped to (ADR-2606013800). */
const DEFAULT_GRAPH_CID = 'actors-v1';

const DID_STORAGE_KEY = 'etzhayyim-auth-did';
const CREDENTIAL_STORAGE_KEY = 'etzhayyim-auth-credential';

// ── injected verify result (mirror of session.ts VerifyCacaoResult) ──────────
export interface VerifyCacaoResult {
	valid: boolean;
	did?: string;
	sigType?: string;
	method?: string;
	scope?: { capabilities: string[]; graphs: string[] };
	gated?: boolean;
	reason?: string;
}

export interface CacaoSessionDeps {
	/** millis since epoch — injected (no Date.now in the core). */
	now: () => number;
	/** opaque single-use nonce (hex). */
	nonce: () => string;
	/** fetch impl (defaults to global). */
	fetch?: typeof fetch;
	/** apex origin (defaults to '' → same-origin POST on the current host). */
	origin?: string;
	/** session/CACAO lifetime in seconds (default 15 min). */
	ttlSecs?: number;
	/** kotoba wrap-store reader (ARK custody). */
	getWrap: GetWrap;
	/** kotoba wrap-store writer (first-device enroll). */
	putWrap: PutWrap;
	/** graph CID the edit capability is scoped to. */
	graphCid?: string;
}

/** The established, in-memory CACAO session (no persisted private key). */
export interface CacaoSession {
	accountDid: string;
	sessionKey: SessionKey;
	verifiedCacao: Cacao;
	scope: { capabilities: string[]; graphs: string[] };
	/** millis-since-epoch expiry of the verified CACAO. */
	exp: number;
}

export interface EstablishOutcome {
	status: 'verified' | 'gated' | 'error';
	did?: string;
	reason?: string;
	session?: CacaoSession;
}

// Module-level in-memory session (mirrors passkey.ts's _keyHierarchy holder).
let _session: CacaoSession | null = null;
/** Read the live CACAO session, or null if signed out. */
export function getCacaoSession(): CacaoSession | null {
	return _session;
}

function isoZ(ms: number): string {
	return new Date(ms).toISOString();
}

async function postVerify(
	cacao: Cacao,
	deps: CacaoSessionDeps,
): Promise<{ status: number; result: VerifyCacaoResult }> {
	const f = deps.fetch ?? fetch;
	const base = deps.origin ?? '';
	const resp = await f(`${base}${VERIFY_PATH}`, {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ cacao }),
	});
	const result = (await resp.json()) as VerifyCacaoResult;
	return { status: resp.status, result };
}

/**
 * Sign a fresh, apex-bound, EdDSA CACAO with the given session key. Exported so
 * the write token-provider can mint per-call capability proofs from the same
 * primitive the login ceremony uses.
 */
export async function mintSessionCacao(
	sessionKey: SessionKey,
	deps: Pick<CacaoSessionDeps, 'now' | 'nonce' | 'ttlSecs' | 'graphCid'>,
): Promise<Cacao> {
	const nowMs = deps.now();
	const ttl = (deps.ttlSecs ?? 900) * 1000;
	const unsigned = buildProfileCacao({
		iss: sessionKey.didKey,
		iat: isoZ(nowMs),
		exp: isoZ(nowMs + ttl),
		nonce: deps.nonce(),
		capabilities: [CAP_DATOM_TRANSACT],
		graphs: [graphResource(deps.graphCid ?? DEFAULT_GRAPH_CID)],
	});
	return signCacaoEd25519(unsigned, sessionKey);
}

/**
 * Core ceremony (no browser, no WebAuthn): given an unlocked passkey PRF secret +
 * the account DID + credential id, recover/enroll the key hierarchy, sign an
 * EdDSA CACAO, and verify it same-origin on the apex. On success, flips the
 * stores into signed-in and registers the CACAO write token-provider.
 *
 * Returns `gated` (honest, no false session) when the account DID is unknown
 * (first-device/sign-up bootstrap, kotoba-node follow-up) or the apex can only
 * structurally accept the CACAO (e.g. a relayed sig type).
 */
export async function establishCacaoSession(
	prfSecret: Uint8Array,
	accountDid: string | null,
	credentialId: string,
	deps: CacaoSessionDeps,
): Promise<EstablishOutcome> {
	if (!accountDid) {
		return {
			status: 'gated',
			reason:
				'account DID bootstrap runs on the kotoba node (first-device / sign-up). ' +
				'No authn fallback (ADR-2606061500 §4).',
		};
	}

	// 1. Recover the ARK from the kotoba zero-access wrap store; first device → enroll.
	let hierarchy = await recoverHierarchy(accountDid, credentialId, prfSecret, deps.getWrap);
	if (!hierarchy) {
		hierarchy = await enrollAccount(accountDid, credentialId, prfSecret, deps.putWrap);
	}
	const sessionKey = hierarchy.sessionKey;

	// 2. Mint + 3. verify the CACAO same-origin on the apex (Ed25519, verified locally).
	const cacao = await mintSessionCacao(sessionKey, deps);
	const { result } = await postVerify(cacao, deps);

	if (result.valid) {
		const session: CacaoSession = {
			accountDid,
			sessionKey,
			verifiedCacao: cacao,
			scope: result.scope ?? { capabilities: [CAP_DATOM_TRANSACT], graphs: [] },
			exp: deps.now() + (deps.ttlSecs ?? 900) * 1000,
		};
		activateSession(session, deps);
		return { status: 'verified', did: accountDid, session };
	}

	if (result.gated) {
		return { status: 'gated', did: accountDid, reason: result.reason };
	}
	return { status: 'error', reason: result.reason ?? 'CACAO verification failed.' };
}

/** Flip the app into signed-in state from a verified CACAO (no accessJwt). */
function activateSession(session: CacaoSession, deps: CacaoSessionDeps): void {
	_session = session;
	// DID-only atproto session: the agent knows WHO we are; writes carry a CACAO
	// (not accessJwt), so the bearer field is intentionally empty.
	setSession({ did: session.accountDid, handle: didToHandle(session.accountDid), accessJwt: '' });
	setTokenProvider(makeCacaoTokenProvider(() => _session?.sessionKey ?? null, deps));
	isSignedIn.set(true);
	sessionToken.set(null); // no JWT — CACAO-only
	clerkUser.set(didToUser(session.accountDid));
	clerkLoaded.set(true);
	try {
		localStorage?.setItem(DID_STORAGE_KEY, session.accountDid);
	} catch {
		/* non-browser / storage-less */
	}
}

/** Drop the in-memory key + verified CACAO and clear all auth state. */
export function signOutCacao(): void {
	_session = null;
	setTokenProvider(null);
	clearSession();
	isSignedIn.set(false);
	sessionToken.set(null);
	clerkUser.set(null);
}

/**
 * A write-authorization token provider that mints a fresh, single-use CACAO per
 * call from the live session key. `atproto-agent` attaches it as a CACAO
 * Authorization (see ADR-2606061500 §2) instead of `Bearer <jwt>`; the kotoba
 * node verifies the delegation + nonce. Returns '' when signed out.
 */
export function makeCacaoTokenProvider(
	getKey: () => SessionKey | null,
	deps: Pick<CacaoSessionDeps, 'now' | 'nonce' | 'ttlSecs' | 'graphCid'>,
): () => Promise<string> {
	return async () => {
		const key = getKey();
		if (!key) return '';
		const cacao = await mintSessionCacao(key, deps);
		// Compact, transport-safe encoding the kotoba node + apex already parse.
		return 'cacao:' + base64urlJson(cacao);
	};
}

function base64urlJson(value: unknown): string {
	const json = JSON.stringify(value);
	if (typeof btoa === 'function') {
		return btoa(unescape(encodeURIComponent(json)))
			.replace(/\+/g, '-')
			.replace(/\//g, '_')
			.replace(/=+$/g, '');
	}
	// Node / SSR fallback.
	return Buffer.from(json, 'utf-8').toString('base64url');
}

function didToHandle(did: string): string {
	return did
		.replace(/^did:web:[^:]+:actor:/, '')
		.replace(/^did:web:[^:]+:/, '')
		.replace(/^did:web:/, '')
		.replace(/:/g, '.');
}

function didToUser(did: string) {
	const handle = didToHandle(did);
	return {
		id: did,
		firstName: null,
		lastName: null,
		fullName: handle,
		username: handle,
		emailAddress: null,
		phoneNumber: null,
		hasVerifiedEmail: false,
		hasVerifiedPhone: false,
		imageUrl: '',
		externalAccounts: [],
		web3Wallets: [],
		publicMetadata: {},
	};
}

// ── Browser entrypoint ───────────────────────────────────────────────────────

function getStoredDid(): string | null {
	try {
		return localStorage?.getItem(DID_STORAGE_KEY) ?? null;
	} catch {
		return null;
	}
}
function getStoredCredentialId(): string | null {
	try {
		return localStorage?.getItem(CREDENTIAL_STORAGE_KEY) ?? null;
	} catch {
		return null;
	}
}

function base64urlEncode(buffer: ArrayBuffer): string {
	const bytes = new Uint8Array(buffer);
	let binary = '';
	for (const b of bytes) binary += String.fromCharCode(b);
	return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function defaultNonce(): string {
	const b = crypto.getRandomValues(new Uint8Array(16));
	return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
}

/**
 * Same-origin passkey → CACAO sign-in (the header "ログイン" path).
 *
 * The WebAuthn challenge is CLIENT-generated: the assertion only unlocks the
 * passkey PRF to derive the session key; it is not the proof presented to a
 * server, so no `passkeyBeginAuth` (authn) round-trip is needed (ADR-2606061500
 * §1). Wrap-store accessors are injected (kotoba zero-access custody).
 */
export async function signInWithPasskeyCacao(
	wrap: { getWrap: GetWrap; putWrap: PutWrap },
	overrides: Partial<CacaoSessionDeps> = {},
): Promise<EstablishOutcome> {
	if (typeof window === 'undefined' || !navigator.credentials) {
		return { status: 'error', reason: 'WebAuthn unavailable in this environment.' };
	}
	const challenge = crypto.getRandomValues(new Uint8Array(32));
	const storedCredId = getStoredCredentialId();
	const credential = (await navigator.credentials.get({
		publicKey: {
			challenge,
			rpId: APEX_RP_ID,
			timeout: 60_000,
			userVerification: 'preferred',
			allowCredentials: storedCredId
				? [{ type: 'public-key', id: base64urlDecodeToBytes(storedCredId) }]
				: [],
			extensions: prfEvalExtension(accountPrfSalt(APEX_RP_ID)),
		},
	})) as PublicKeyCredential | null;

	if (!credential) return { status: 'error', reason: 'Passkey assertion cancelled.' };

	const prfSecret = extractPrfSecret(credential);
	if (!prfSecret) {
		return {
			status: 'gated',
			reason:
				'This passkey has no PRF — the zero-access key hierarchy (ARK → session key) ' +
				'cannot be derived on-device. Re-enroll a PRF-capable passkey (ADR-2606014000).',
		};
	}
	const credentialId = base64urlEncode(credential.rawId);
	try {
		localStorage?.setItem(CREDENTIAL_STORAGE_KEY, credentialId);
	} catch {
		/* storage-less */
	}

	const deps: CacaoSessionDeps = {
		now: () => Date.now(),
		nonce: defaultNonce,
		origin: '',
		...wrap,
		...overrides,
	};
	return establishCacaoSession(prfSecret, getStoredDid(), credentialId, deps);
}

function base64urlDecodeToBytes(s: string): Uint8Array {
	s = s.replace(/-/g, '+').replace(/_/g, '/');
	while (s.length % 4) s += '=';
	const binary = atob(s);
	const out = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
	return out;
}

/** Re-derive a session key from a known ARK (used in tests + recovery paths). */
export async function sessionKeyFromArk(ark: Uint8Array): Promise<SessionKey> {
	return deriveSessionKeyPair(ark);
}
