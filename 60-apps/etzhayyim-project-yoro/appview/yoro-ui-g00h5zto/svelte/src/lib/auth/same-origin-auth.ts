/**
 * Same-origin, kotoba-based passkey auth (ADR-2606060000 → ADR-2606061800).
 *
 * Replaces the legacy `authn.etzhayyim.com` → MCP-router (`mcp.etzhayyim.com`)
 * WebAuthn ceremony — which minted a server-held JWT — with a flow that NEVER
 * leaves the apex origin and holds NO server key:
 *
 *   passkey  ──PRF──▶ S_prf ──HKDF──▶ Ed25519 session key ──▶ did:key  (PRIMARY)
 *            ──no PRF──▶ credential P-256 public key ───────▶ did:key  (FALLBACK)
 *
 * DID model (2-layer, confirmed with the operator):
 *   • controller / crypto root = the passkey-derived `did:key` (self-certifying;
 *     verified LOCALLY on the apex Worker via WebCrypto — no registry, no key).
 *   • public handle = `did:web:etzhayyim.com:<handle>` published to the kotoba
 *     Datom log (best-effort; login NEVER depends on it being reachable).
 *
 * The session is established CLIENT-SIDE the instant the key is derived, so
 * login/signup work with ZERO backend dependency. A best-effort POST to the apex
 * `com.etzhayyim.authz.verifyCacao` confirms control server-side (the gating hook
 * for writes); a best-effort `registerAccount` publishes the handle to kotoba.
 *
 * No `authn.etzhayyim.com`. No `mcp.etzhayyim.com`. No server-minted session.
 */

import {
	prfRegistrationEvalExtension,
	prfEvalExtension,
	accountPrfSalt,
	extractPrfSecret,
} from './prf.js';
import { deriveSessionKeyPair, base58btcEncode, type SessionKey } from './session-key.js';
import { buildProfileCacao, signCacaoEd25519, CAP_ACCOUNT_LOGIN } from './cacao.js';
import { publishAccount } from './account-ops.js';

// ─── apex / RP constants ────────────────────────────────────────────────────

/** WebAuthn relying-party id — the apex zone. Passkeys are scoped to this. */
export const RP_ID = 'etzhayyim.com';
export const RP_NAME = 'etzhayyim';
/** Apex origin that serves the same-origin verify/register XRPC (verify-only). */
export const APEX_ORIGIN = 'https://etzhayyim.com';

const VERIFY_PATH = '/xrpc/com.etzhayyim.authz.verifyCacao';

/** localStorage map: WebAuthn credentialId(b64url) → derived account did. Lets the
 *  no-PRF (P-256) path resolve its DID on sign-in (the assertion alone can't). */
const CRED_DID_MAP_KEY = 'etzhayyim-auth-cred-did';

export type SignInMethod = 'prf-ed25519' | 'p256-passkey';

export interface SameOriginAuthResult {
	did: string;
	handle: string;
	/** EdDSA session PoP JWS (PRF path) — a bearer the PDS can verify against the
	 *  registered key. Empty for the P-256 path (no arbitrary-message signer). */
	accessJwt: string;
	refreshJwt: string;
	method: SignInMethod;
	/** apex `verifyCacao` confirmed control (best-effort; false ⇒ local-only). */
	serverConfirmed: boolean;
	/** the derived session key, when available (PRF path) — held in memory only. */
	sessionKey?: SessionKey;
}

// ─── small helpers ──────────────────────────────────────────────────────────

function randomBytes(n: number): Uint8Array {
	return crypto.getRandomValues(new Uint8Array(n));
}

function bytesToHex(b: Uint8Array): string {
	let out = '';
	for (const x of b) out += x.toString(16).padStart(2, '0');
	return out;
}

function b64urlEncode(buf: ArrayBuffer | Uint8Array): string {
	const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
	let bin = '';
	for (const b of bytes) bin += String.fromCharCode(b);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function isoZ(ms: number): string {
	return new Date(ms).toISOString();
}

function bufferSource(u: Uint8Array): Uint8Array<ArrayBuffer> {
	// fresh ArrayBuffer-backed copy → satisfies WebAuthn/WebCrypto BufferSource
	// typing under TS's strict ArrayBufferLike (mirrors key-tree.ts `bs()`).
	const out = new Uint8Array(u.byteLength);
	out.set(u);
	return out as Uint8Array<ArrayBuffer>;
}

// ─── credentialId → did local map (P-256 fallback resolution) ───────────────

function readCredDidMap(): Record<string, string> {
	if (typeof localStorage === 'undefined') return {};
	try {
		return JSON.parse(localStorage.getItem(CRED_DID_MAP_KEY) ?? '{}') as Record<string, string>;
	} catch {
		return {};
	}
}

function rememberCredDid(credentialId: string, did: string): void {
	if (typeof localStorage === 'undefined') return;
	const map = readCredDidMap();
	map[credentialId] = did;
	try {
		localStorage.setItem(CRED_DID_MAP_KEY, JSON.stringify(map));
	} catch {
		/* quota — non-fatal */
	}
}

function lookupCredDid(credentialId: string): string | null {
	return readCredDidMap()[credentialId] ?? null;
}

// ─── DID derivation ─────────────────────────────────────────────────────────

/**
 * PRIMARY: treat the 32-byte WebAuthn PRF secret as the Account Root Key and
 * derive the deterministic Ed25519 session key (→ `did:key`). Deterministic ⇒ the
 * same passkey yields the same DID on any device, with no server-side ARK store.
 */
async function deriveSessionKeyFromPrf(prfSecret: Uint8Array): Promise<SessionKey> {
	// ARK = PRF secret directly; deriveSessionKeyPair runs HKDF(ARK, session-label),
	// so the same passkey deterministically yields the same did:key everywhere.
	return deriveSessionKeyPair(prfSecret);
}

/** p256-pub multicodec (0x1200) as an unsigned-varint prefix. */
const P256_MULTICODEC = Uint8Array.from([0x80, 0x24]);

/** Compress an uncompressed P-256 point (0x04‖X‖Y, 65 B) → 33-byte SEC1. */
function compressP256(uncompressed: Uint8Array): Uint8Array {
	if (uncompressed.length !== 65 || uncompressed[0] !== 0x04) {
		throw new Error('expected 65-byte uncompressed P-256 point');
	}
	const x = uncompressed.slice(1, 33);
	const y = uncompressed.slice(33, 65);
	const prefix = (y[y.length - 1] & 1) === 0 ? 0x02 : 0x03;
	const out = new Uint8Array(33);
	out[0] = prefix;
	out.set(x, 1);
	return out;
}

/**
 * FALLBACK: derive a `did:key` from the WebAuthn credential's own P-256 public
 * key (available at registration via `getPublicKey()`, SPKI DER). Used when the
 * authenticator has no PRF — the account is still a self-certifying did:key, but
 * recovery on a fresh device requires a kotoba lookup (no offline derivation).
 */
async function deriveDidKeyFromP256(spki: ArrayBuffer): Promise<{ did: string; publicKeyMultibase: string }> {
	const key = await crypto.subtle.importKey(
		'spki',
		spki,
		{ name: 'ECDSA', namedCurve: 'P-256' },
		true,
		['verify'],
	);
	const raw = new Uint8Array(await crypto.subtle.exportKey('raw', key)); // 0x04‖X‖Y
	const compressed = compressP256(raw);
	const prefixed = new Uint8Array(P256_MULTICODEC.length + compressed.length);
	prefixed.set(P256_MULTICODEC);
	prefixed.set(compressed, P256_MULTICODEC.length);
	const publicKeyMultibase = 'z' + base58btcEncode(prefixed);
	return { did: `did:key:${publicKeyMultibase}`, publicKeyMultibase };
}

/** Short, human-ish handle derived from a DID (display-only until a kotoba alias
 *  is published). Stable for a given DID. */
export function handleFromDid(did: string): string {
	if (did.startsWith('did:web:')) {
		return did.replace(/^did:web:[^:]+:/, '').replace(/:/g, '.') || did.slice('did:web:'.length);
	}
	if (did.startsWith('did:key:')) {
		const z = did.slice('did:key:'.length);
		return `member-${z.slice(1, 9).toLowerCase()}`;
	}
	return did;
}

// ─── session PoP (EdDSA) ────────────────────────────────────────────────────

const SESSION_TTL_MS = 2 * 3600 * 1000; // 2h

async function signSessionPoP(sessionKey: SessionKey, did: string, nowMs: number): Promise<string> {
	const header = { alg: 'EdDSA', typ: 'pop+jwt', kid: `${did}#session-key` };
	const payload = {
		iss: did,
		sub: did,
		iat: Math.floor(nowMs / 1000),
		exp: Math.floor((nowMs + SESSION_TTL_MS) / 1000),
	};
	const enc = (o: unknown) => b64urlEncode(new TextEncoder().encode(JSON.stringify(o)));
	const signingInput = `${enc(header)}.${enc(payload)}`;
	const sig = new Uint8Array(
		await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, new TextEncoder().encode(signingInput)),
	);
	return `${signingInput}.${b64urlEncode(sig)}`;
}

// ─── apex control confirmation + account publish (both best-effort) ─────────

interface VerifyCacaoResult {
	valid: boolean;
	did?: string;
	gated?: boolean;
	reason?: string;
}

/** POST a control-proof CACAO to the apex `verifyCacao`. Returns true iff the
 *  apex confirmed control. Any failure (offline, gated, not-deployed) ⇒ false —
 *  the local session still stands. */
async function confirmControl(sessionKey: SessionKey, nowMs: number): Promise<boolean> {
	try {
		const unsigned = buildProfileCacao({
			iss: sessionKey.didKey,
			iat: isoZ(nowMs),
			exp: isoZ(nowMs + 5 * 60 * 1000),
			nonce: bytesToHex(randomBytes(16)),
			capabilities: [CAP_ACCOUNT_LOGIN],
			graphs: [],
			statement: 'Sign in to etzhayyim',
		});
		const signed = await signCacaoEd25519(unsigned, sessionKey);
		const resp = await fetch(`${APEX_ORIGIN}${VERIFY_PATH}`, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ cacao: signed }),
		});
		if (!resp.ok) return false;
		const result = (await resp.json()) as VerifyCacaoResult;
		return result.valid === true;
	} catch {
		return false;
	}
}

/**
 * Publish the account record (controller did:key + a self-certifying handle
 * attestation + profile) as a member-signed, content-addressed block via the
 * apex `block.put` (see `account-ops.ts` / `block-publish.ts`). Domain-
 * independent: the record is a CID signed by the `did:key`, dependent on neither
 * the domain nor a central node (IPFS-pinned via kotobase.net). Best-effort,
 * non-blocking — login already stands regardless of the publish result.
 */
export async function registerAccount(
	sessionKey: SessionKey,
	handle: string,
	nowMs: number,
	profile: Record<string, unknown> = {},
): Promise<{ ok: boolean }> {
	const strProfile: Record<string, string> = {};
	for (const [k, v] of Object.entries(profile)) if (typeof v === 'string') strProfile[k] = v;
	const r = await publishAccount(sessionKey, handle, strProfile, { now: () => nowMs });
	return { ok: r.ok };
}

// ─── WebAuthn ceremonies ────────────────────────────────────────────────────

function webauthnAvailable(): boolean {
	return typeof window !== 'undefined' && !!navigator.credentials;
}

/**
 * Sign UP same-origin. Creates a passkey, derives the controller did:key (PRF
 * primary, P-256 fallback), establishes the session locally, and best-effort
 * publishes the account to kotoba. Throws only on hard WebAuthn failure /
 * cancellation; callers surface the error.
 */
export async function signUpSameOrigin(now: () => number = Date.now): Promise<SameOriginAuthResult | null> {
	if (!webauthnAvailable()) throw new Error('WebAuthn not supported on this device');

	const userId = randomBytes(16);
	const salt = accountPrfSalt(RP_ID);
	const credential = (await navigator.credentials.create({
		publicKey: {
			challenge: bufferSource(randomBytes(32)),
			rp: { id: RP_ID, name: RP_NAME },
			user: {
				id: bufferSource(userId),
				name: `member-${b64urlEncode(userId).slice(0, 8)}@etzhayyim.com`,
				displayName: 'etzhayyim member',
			},
			pubKeyCredParams: [
				{ type: 'public-key', alg: -8 }, // Ed25519
				{ type: 'public-key', alg: -7 }, // ES256 (P-256) — fallback + broad support
			],
			authenticatorSelection: { residentKey: 'preferred', userVerification: 'preferred' },
			timeout: 60_000,
			attestation: 'none',
			// Enable PRF AND try to evaluate it in the same ceremony (modern
			// authenticators return prf.results.first directly on create).
			extensions: prfRegistrationEvalExtension(salt),
		},
	})) as PublicKeyCredential | null;
	if (!credential) return null;

	const credentialId = b64urlEncode(credential.rawId);
	const nowMs = now();

	// PRIMARY: PRF secret available → deterministic Ed25519 did:key.
	let prfSecret = extractPrfSecret(credential);
	if (!prfSecret) {
		// Some authenticators enable PRF at create but only return results on get();
		// do one assertion to fetch it before giving up on the PRF path.
		prfSecret = await tryFetchPrfViaGet(credentialId, salt);
	}
	if (prfSecret) {
		const sessionKey = await deriveSessionKeyFromPrf(prfSecret);
		return finishPrf(sessionKey, credentialId, nowMs, true);
	}

	// FALLBACK: no PRF → derive did:key from the credential's P-256 public key.
	const attest = credential.response as AuthenticatorAttestationResponse;
	const spki = attest.getPublicKey?.();
	if (!spki) {
		throw new Error(
			'This device cannot do PRF and did not expose a public key — add the passkey from a PRF-capable device (or scan the QR with your phone).',
		);
	}
	const { did } = await deriveDidKeyFromP256(spki);
	rememberCredDid(credentialId, did);
	return {
		did,
		handle: handleFromDid(did),
		accessJwt: '',
		refreshJwt: '',
		method: 'p256-passkey',
		serverConfirmed: false,
	};
}

/** Try to obtain the PRF secret with a single assertion (for authenticators that
 *  only surface prf.results on get). Returns null on any failure. */
async function tryFetchPrfViaGet(credentialId: string, salt: Uint8Array): Promise<Uint8Array | null> {
	try {
		const assertion = (await navigator.credentials.get({
			publicKey: {
				challenge: bufferSource(randomBytes(32)),
				rpId: RP_ID,
				timeout: 60_000,
				userVerification: 'preferred',
				allowCredentials: [{ type: 'public-key', id: bufferSource(b64urlToBytes(credentialId)) }],
				extensions: prfEvalExtension(salt),
			},
		})) as PublicKeyCredential | null;
		return assertion ? extractPrfSecret(assertion) : null;
	} catch {
		return null;
	}
}

/**
 * Sign IN same-origin. Asserts a passkey, derives the controller did:key (PRF
 * primary), establishes the session locally, and best-effort confirms control on
 * the apex. The no-PRF (P-256) path resolves its DID from the local cred→did map
 * (same device) or returns a clear error prompting a PRF/hybrid sign-in.
 */
export async function signInSameOrigin(now: () => number = Date.now): Promise<SameOriginAuthResult | null> {
	if (!webauthnAvailable()) throw new Error('WebAuthn not supported on this device');

	const salt = accountPrfSalt(RP_ID);
	const assertion = (await navigator.credentials.get({
		publicKey: {
			challenge: bufferSource(randomBytes(32)),
			rpId: RP_ID,
			timeout: 60_000,
			userVerification: 'preferred',
			extensions: prfEvalExtension(salt),
		},
	})) as PublicKeyCredential | null;
	if (!assertion) return null;

	const credentialId = b64urlEncode(assertion.rawId);
	const nowMs = now();

	const prfSecret = extractPrfSecret(assertion);
	if (prfSecret) {
		const sessionKey = await deriveSessionKeyFromPrf(prfSecret);
		return finishPrf(sessionKey, credentialId, nowMs, false);
	}

	// No PRF → resolve the previously-derived P-256 did:key for this credential.
	const did = lookupCredDid(credentialId);
	if (did) {
		return {
			did,
			handle: handleFromDid(did),
			accessJwt: '',
			refreshJwt: '',
			method: 'p256-passkey',
			serverConfirmed: false,
		};
	}
	throw new Error(
		'This device/browser has no PRF and no local record of this passkey. Sign in on the device you registered with, or use a PRF-capable device / phone (QR).',
	);
}

/** Common PRF-path completion: PoP bearer + best-effort apex confirmation +
 *  (on signup) account publish. */
async function finishPrf(
	sessionKey: SessionKey,
	credentialId: string,
	nowMs: number,
	publish: boolean,
): Promise<SameOriginAuthResult> {
	const did = sessionKey.didKey;
	const handle = handleFromDid(did);
	rememberCredDid(credentialId, did);
	const accessJwt = await signSessionPoP(sessionKey, did, nowMs).catch(() => '');
	const serverConfirmed = await confirmControl(sessionKey, nowMs);
	if (publish) {
		// fire-and-forget — never blocks signup, honest if the kotoba relay is gated
		void registerAccount(sessionKey, handle, nowMs, { displayName: handle }).catch(() => undefined);
	}
	return {
		did,
		handle,
		accessJwt,
		refreshJwt: '',
		method: 'prf-ed25519',
		serverConfirmed,
		sessionKey,
	};
}

function b64urlToBytes(s: string): Uint8Array {
	const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
	const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/') + pad);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}
