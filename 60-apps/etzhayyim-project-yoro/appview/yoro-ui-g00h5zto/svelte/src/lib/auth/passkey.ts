/**
 * Passkey (WebAuthn) auth — drop-in replacement for clerk.ts.
 * Same exported interface: initClerk → initAuth, signIn/signUp/signOut, getSessionToken, etc.
 * Uses navigator.credentials (WebAuthn) + AUTH_SERVICE for session management.
 */

import type { AuthConfig, Organization, UsernameSignUpInput } from './types.js';
import {
	clerkLoaded,
	isSignedIn,
	clerkUser,
	sessionToken,
	onboardingCompleted,
	currentOrg,
	userOrganizations,
	orgLoading,
} from './stores.js';
import { setSession, clearSession } from '$lib/atproto-agent';
import {
	prfRegistrationEvalExtension,
	accountPrfSalt,
	extractPrfSecret,
} from './prf.js';
import {
	enrollAccount,
	recoverHierarchy,
	enrollDevice,
	type KeyHierarchy,
} from './key-hierarchy.js';
import { makePutWrap, makeGetWrap } from './account.js';
import { registerSessionKey } from './session-key.js';
import {
	signInSameOrigin,
	signUpSameOrigin,
	handleFromDid,
	type SameOriginAuthResult,
} from './same-origin-auth.js';

// In-memory holder for the WebAuthn PRF secret (S_prf, ADR-2606014000 L0).
// Device-resident only — never persisted, never sent to the server. Consumed by
// the key hierarchy to unwrap the Account Root Key.
let _prfSecret: Uint8Array | null = null;
/** Store the captured PRF secret for this session. */
export function setPrfSecret(secret: Uint8Array): void {
	_prfSecret = secret;
}
/** Read the current session's PRF secret, or null if this device has no PRF. */
export function getPrfSecret(): Uint8Array | null {
	return _prfSecret;
}

// In-memory holder for the established key hierarchy (L1/L2 + session key).
// Device-resident only. Apps read it for at-rest encryption / Signal / signing.
let _keyHierarchy: KeyHierarchy | null = null;
/** Store the established key hierarchy for this session. */
export function setKeyHierarchy(h: KeyHierarchy): void {
	_keyHierarchy = h;
}
/** Read the established key hierarchy, or null if not yet established. */
export function getKeyHierarchy(): KeyHierarchy | null {
	return _keyHierarchy;
}

const AUTH_BASE = 'https://atproto.etzhayyim.com';
const AUTH_RPC_BASE = 'https://authn.etzhayyim.com';
const SESSION_STORAGE_KEY = 'etzhayyim-auth-session';
const CREDENTIAL_STORAGE_KEY = 'etzhayyim-auth-credential';
const DID_STORAGE_KEY = 'etzhayyim-auth-did';
const AUTH_TRANSFER_STORAGE_KEY = 'etzhayyim-auth-transfer';

// Keep the same export name for backward compat
export const DEFAULT_CLERK_PUBLISHABLE_KEY = '';

let initialized = false;
let sessionRefreshTimer: ReturnType<typeof setInterval> | null = null;
let onOrgSwitchCallback: (() => void) | null = null;

interface StoredSession {
	accessJwt: string;
	refreshJwt: string;
	did: string;
	handle: string;
	expiresAt: number;
}

function getSessionStorage(): Storage | null {
	if (typeof sessionStorage === 'undefined') return null;
	return sessionStorage;
}

function getLocalStorage(): Storage | null {
	if (typeof localStorage === 'undefined') return null;
	return localStorage;
}

function readSessionFrom(storage: Storage | null): StoredSession | null {
	if (!storage) return null;
	try {
		const raw = storage.getItem(SESSION_STORAGE_KEY);
		if (!raw) return null;
		return JSON.parse(raw) as StoredSession;
	} catch {
		return null;
	}
}

function getStoredSession(): StoredSession | null {
	const sessionStore = getSessionStorage();
	const localStore = getLocalStorage();
	const session = readSessionFrom(sessionStore) ?? readSessionFrom(localStore);
	if (!session) return null;
	if (sessionStore && localStore?.getItem(SESSION_STORAGE_KEY)) {
		sessionStore.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
		localStore.removeItem(SESSION_STORAGE_KEY);
	}
	return session;
}

function storeSession(session: StoredSession): void {
	const sessionStore = getSessionStorage();
	sessionStore?.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
	getLocalStorage()?.removeItem(SESSION_STORAGE_KEY);
}

function clearStoredSession(): void {
	getSessionStorage()?.removeItem(SESSION_STORAGE_KEY);
	getSessionStorage()?.removeItem(AUTH_TRANSFER_STORAGE_KEY);
	getLocalStorage()?.removeItem(SESSION_STORAGE_KEY);
	getLocalStorage()?.removeItem(CREDENTIAL_STORAGE_KEY);
	getLocalStorage()?.removeItem(DID_STORAGE_KEY);
}

function storeCredentialId(credentialId: string): void {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(CREDENTIAL_STORAGE_KEY, credentialId);
}

function getStoredCredentialId(): string | null {
	if (typeof localStorage === 'undefined') return null;
	return localStorage.getItem(CREDENTIAL_STORAGE_KEY);
}

/** Sync session to $lib/atproto-agent client so getCurrentDID() returns the DID immediately. */
function syncAtprotoSession(session: StoredSession): void {
	setSession({
		did: session.did,
		handle: session.handle,
		accessJwt: session.accessJwt,
		refreshJwt: session.refreshJwt,
	});
}

function storeDid(did: string): void {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(DID_STORAGE_KEY, did);
}

function getStoredDid(): string | null {
	if (typeof localStorage === 'undefined') return null;
	return localStorage.getItem(DID_STORAGE_KEY);
}

async function authRpc(path: string, body?: unknown): Promise<any> {
	const resp = await fetch(`${AUTH_RPC_BASE}${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: body ? JSON.stringify(body) : undefined,
	});
	if (!resp.ok) {
		const err = await resp.text().catch((_err) => '');
		throw new Error(`auth RPC ${path} failed: ${resp.status} ${err}`);
	}
	return resp.json();
}

function base64urlEncode(buffer: ArrayBuffer): string {
	const bytes = new Uint8Array(buffer);
	let binary = '';
	for (const b of bytes) binary += String.fromCharCode(b);
	return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function base64urlDecode(s: string): ArrayBuffer {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    const binary = atob(s);
    const result = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
        result[i] = binary.charCodeAt(i);
    }
    return result.buffer.slice(result.byteOffset, result.byteOffset + result.byteLength);
}

export function setOnOrgSwitch(callback: () => void): void {
	onOrgSwitchCallback = callback;
}

/**
 * Initialize auth. Compatible with initClerk signature.
 * Restores existing session from localStorage if available.
 */
export async function initClerk(config?: AuthConfig): Promise<any> {
	if (initialized) return null;
	initialized = true;

	// Receive session from auth.etzhayyim.com via temporary sessionStorage transfer,
	// falling back to the legacy hash fragment path for backward compatibility.
	const transferredRaw = (() => {
		const storage = getSessionStorage();
		const fromStorage = storage?.getItem(AUTH_TRANSFER_STORAGE_KEY);
		if (fromStorage) {
			storage?.removeItem(AUTH_TRANSFER_STORAGE_KEY);
			return fromStorage;
		}
		if (typeof window !== 'undefined' && window.location.hash.startsWith('#auth=')) {
			return window.location.hash.slice('#auth='.length);
		}
		return null;
	})();
	if (transferredRaw) {
		try {
			const transferred = JSON.parse(decodeURIComponent(transferredRaw)) as StoredSession;
			if (transferred?.accessJwt && transferred?.did) {
				storeSession(transferred);
				storeCredentialId(''); // no credential ID from cross-origin
				storeDid(transferred.did);
				sessionToken.set(transferred.accessJwt);
				isSignedIn.set(true);
				syncAtprotoSession(transferred);
				updateUserFromDid(transferred.did);
				if (typeof window !== 'undefined') {
					history.replaceState(null, '', window.location.pathname + window.location.search);
				}
			}
		} catch (e) {
			console.warn('Auth hash fragment parse failed:', e);
		}
	}

	try {
		const stored = getStoredSession();
		if (stored?.accessJwt) {
			// Always restore session — PDS auth fallback handles expired tokens
			sessionToken.set(stored.accessJwt);
			isSignedIn.set(true);
			syncAtprotoSession(stored);
			updateUserFromDid(stored.did);
			// Attempt refresh in background if expired
			const expired = stored.expiresAt && Date.now() >= stored.expiresAt;
			if (expired && stored.refreshJwt) {
				refreshSessionFromStored(stored).catch((error) => {
					console.warn('[silent-fail] passkey.ts: refreshSessionFromStored failed', error);
				});
			}
		}
	} catch (e) {
		console.warn('Session restore failed:', e);
	}

	clerkLoaded.set(true);

	// Periodic session refresh (50s interval — same as Clerk keepalive)
	sessionRefreshTimer = setInterval(async () => {
		const stored = getStoredSession();
		if (stored?.refreshJwt) {
			// Refresh 30s before expiry
			if (stored.expiresAt && Date.now() > stored.expiresAt - 30_000) {
				await refreshSessionFromStored(stored);
			}
		}
	}, 50_000);

	return null;
}

async function refreshSessionFromStored(stored: StoredSession): Promise<void> {
	try {
		let result: any;
		try {
			result = await authRpc('/xrpc/com.atproto.server.refreshSession', {
				refreshToken: stored.refreshJwt,
			});
		} catch (primaryError) {
			// Fallback: route refresh via atproto.etzhayyim.com (AUTH_SERVICE delegate) when auth.etzhayyim.com CORS blocks browser calls.
			const fallbackResp = await fetch(`${AUTH_BASE}/xrpc/com.atproto.server.refreshSession`, {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${stored.refreshJwt}`,
				},
			});
			if (!fallbackResp.ok) {
				const fallbackText = await fallbackResp.text().catch(() => '');
				throw new Error(`refresh fallback failed: ${fallbackResp.status} ${fallbackText || String(primaryError)}`);
			}
			result = await fallbackResp.json();
		}
		const newSession: StoredSession = {
			accessJwt: result.accessJwt as string,
			refreshJwt: result.refreshJwt as string,
			did: (result.did || stored.did) as string,
			handle: (result.handle || stored.handle) as string,
			expiresAt: Date.now() + 2 * 3600 * 1000 - 60_000, // 2h minus 1min buffer
		};
		storeSession(newSession);
		sessionToken.set(newSession.accessJwt);
		isSignedIn.set(true);
		syncAtprotoSession(newSession);
		updateUserFromDid(newSession.did);
	} catch (e) {
		console.warn('Session refresh failed, keeping existing session:', e);
		// Keep existing session — PDS auth fallback extracts DID from JWT payload
		sessionToken.set(stored.accessJwt);
		isSignedIn.set(true);
		syncAtprotoSession(stored);
		updateUserFromDid(stored.did);
	}
}

function updateUserFromDid(did: string): void {
	const handle = handleFromDid(did);
	clerkUser.set({
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
	});
	storeDid(did);
}

/**
 * Apply a same-origin auth result: persist the session locally and flip the
 * signed-in stores. No server-minted token — the session is the client-held
 * did:key + (PRF path) an EdDSA PoP bearer. NSK-preserving.
 */
function applyAuthResult(result: SameOriginAuthResult): void {
	const session: StoredSession = {
		accessJwt: result.accessJwt,
		refreshJwt: result.refreshJwt,
		did: result.did,
		handle: result.handle,
		expiresAt: Date.now() + 2 * 3600 * 1000 - 60_000,
	};
	storeSession(session);
	storeDid(result.did);
	sessionToken.set(session.accessJwt);
	isSignedIn.set(true);
	syncAtprotoSession(session);
	updateUserFromDid(session.did);
}

/**
 * Sign in with Passkey — same-origin, kotoba-based (ADR-2606061800). No
 * `authn.etzhayyim.com`, no `mcp.etzhayyim.com`, no server-held key. Throws on a
 * real error so the UI can surface it; returns quietly on user cancellation.
 */
export async function signIn(): Promise<void> {
	const result = await signInSameOrigin();
	if (!result) return; // user cancelled the WebAuthn prompt
	applyAuthResult(result);
}

/**
 * Recover (or, for a brand-new first device, enroll) the account key hierarchy
 * from the captured PRF secret and the wrapped-ARK store, then register the
 * derived Ed25519 session key (Stage C-2). Never throws.
 *
 * NOTE (multi-device): a recover() miss is treated as first-device enrollment.
 * Adding a SECOND device to an existing account must instead use the explicit
 * add-device flow (enrollDevice from an already-unlocked device) so it re-wraps
 * the SAME ARK — that UX is a follow-up.
 */
async function establishKeyHierarchy(
	accountDid: string,
	credentialId: string,
	accessToken: string,
): Promise<void> {
	try {
		const prfSecret = getPrfSecret();
		if (!prfSecret) return; // authenticator has no PRF → server-assisted fallback
		const put = makePutWrap(accessToken);
		const get = makeGetWrap(accessToken);
		let h = await recoverHierarchy(accountDid, credentialId, prfSecret, get);
		if (!h) h = await enrollAccount(accountDid, credentialId, prfSecret, put);
		setKeyHierarchy(h);
		// Register the public half of the session key (zero-access custody, C-2).
		await registerSessionKey(accountDid, h.sessionKey.publicKeyMultibase, accessToken).catch(
			(e) => console.warn('session-key registration skipped:', e),
		);
	} catch (e) {
		console.warn('key hierarchy establishment skipped:', e);
	}
}

/**
 * Add an additional passkey/authenticator to the CURRENT account on THIS device
 * (ADR-2606014000 multi-device). Requires the key hierarchy to be established
 * (this device holds the ARK). Registers a new passkey, evaluates its PRF at
 * create time, and re-wraps the SAME ARK under the new passkey's PRF so the new
 * authenticator independently recovers the account. Returns true on success.
 *
 * Scope: the SAME-DEVICE additional-authenticator case (ARK already in memory).
 * Adding a brand-new SECOND physical device needs an out-of-band ARK transfer
 * authorized from this device — a follow-up.
 */
export async function addDevicePasskey(accountDid: string, accessToken: string): Promise<boolean> {
	if (typeof window === 'undefined' || !navigator.credentials) return false;
	const h = getKeyHierarchy();
	if (!h) {
		console.warn('addDevicePasskey: no key hierarchy on this device');
		return false;
	}
	try {
		const userId = crypto.randomUUID();
		const beginResp = await authRpc('/xrpc/com.etzhayyim.auth.passkeyBeginRegister', {
			userId,
			userName: `device-${userId.slice(0, 8)}@etzhayyim.com`,
		});
		const credential = (await navigator.credentials.create({
			publicKey: {
				challenge: base64urlDecode(beginResp.challenge),
				rp: { id: beginResp.rp.id, name: beginResp.rp.name },
				user: {
					id: base64urlDecode(beginResp.user.id),
					name: beginResp.user.name,
					displayName: beginResp.user.displayName as string,
				},
				pubKeyCredParams: (beginResp.pubKeyCredParams as any[]).map((p: any) => ({
					type: p.type as 'public-key',
					alg: p.alg,
				})),
				timeout: beginResp.timeout as number,
				extensions: prfRegistrationEvalExtension(accountPrfSalt(beginResp.rp.id as string)),
			},
		})) as PublicKeyCredential | null;
		if (!credential) return false;
		const newPrf = extractPrfSecret(credential);
		if (!newPrf) {
			console.warn('addDevicePasskey: new authenticator has no PRF');
			return false;
		}
		const newCredId = base64urlEncode(credential.rawId);
		return await enrollDevice(accountDid, newCredId, newPrf, h.ark, makePutWrap(accessToken));
	} catch (e) {
		console.warn('addDevicePasskey failed:', e);
		return false;
	}
}

/**
 * Sign up with Passkey — same-origin, kotoba-based (ADR-2606061800). Creates the
 * passkey, derives the controller did:key on-device (PRF→Ed25519 primary, the
 * credential's P-256 key as fallback), establishes the session locally, and
 * best-effort publishes the handle to kotoba. No authn/mcp, no server key.
 */
export async function signUp(): Promise<void> {
	const result = await signUpSameOrigin();
	if (!result) return; // user cancelled the WebAuthn prompt
	applyAuthResult(result);
	onboardingCompleted.set(false);
}

export async function signUpWithUsername(input: UsernameSignUpInput): Promise<void> {
	// Passkey doesn't need username input — redirect to standard signUp
	await signUp();
}

export async function signOut(): Promise<void> {
	if (sessionRefreshTimer) {
		clearInterval(sessionRefreshTimer);
		sessionRefreshTimer = null;
	}
	clearStoredSession();
	clearSession();
	sessionToken.set(null);
	isSignedIn.set(false);
	clerkUser.set(null);
	onboardingCompleted.set(false);
	currentOrg.set(null);
	userOrganizations.set([]);
}

export async function refreshSessionToken(): Promise<string | null> {
	const stored = getStoredSession();
	if (!stored?.accessJwt) {
		sessionToken.set(null);
		return null;
	}
	sessionToken.set(stored.accessJwt);
	return stored.accessJwt;
}

export async function getSessionToken(): Promise<string | null> {
	const stored = getStoredSession();
	if (!stored?.accessJwt) return null;
	// Auto-refresh if near expiry
	if (stored.expiresAt && Date.now() > stored.expiresAt - 30_000 && stored.refreshJwt) {
		await refreshSessionFromStored(stored);
		const refreshed = getStoredSession();
		return refreshed?.accessJwt ?? null;
	}
	return stored.accessJwt;
}

export async function openUserProfile(): Promise<void> {
	// No-op for passkey — profile is managed via yoro settings
	if (typeof window !== 'undefined') {
		window.location.href = '/settings/account';
	}
}

export function getClerk(): any {
	// Compat — returns null (no Clerk instance)
	return null;
}

export async function loadOrganizations(): Promise<void> {
	// Organizations are DID-based in Passkey mode — no Clerk org model.
	// For now, create a default "personal" organization.
	const did = getStoredDid();
	if (!did) return;

	orgLoading.set(true);
	try {
		const orgs: Organization[] = [{
			id: did,
			name: 'Personal',
			slug: 'personal',
			category: 'individual',
			role: 'org:admin',
			imageUrl: undefined,
			memberCount: 1,
			requiredTrustScore: null,
			minimumAge: null,
			metadata: {},
		}];
		userOrganizations.set(orgs);
		currentOrg.set(orgs[0]);
	} finally {
		orgLoading.set(false);
	}
}

export async function switchOrganization(orgId: string): Promise<void> {
	// Single org in Passkey mode
	orgLoading.set(true);
	try {
		let orgs: Organization[] = [];
		userOrganizations.subscribe((o) => (orgs = o))();
		const matched = orgs.find((o) => o.id === orgId);
		if (matched) currentOrg.set(matched);
		onOrgSwitchCallback?.();
		await refreshSessionToken();
	} finally {
		orgLoading.set(false);
	}
}

export async function createOrganization(name: string, slug?: string): Promise<string | null> {
	// DID-based organizations — create via PDS
	console.warn('createOrganization: DID-based orgs not yet implemented in Passkey mode');
	return null;
}
