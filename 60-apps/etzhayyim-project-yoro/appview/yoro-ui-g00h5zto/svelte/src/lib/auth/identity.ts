/**
 * Domain-independent member identity — client side (ADR-2606061800).
 *
 * The canonical identity is the passkey-derived **`did:key`** (self-certifying).
 * `did:web:etzhayyim.com:<handle>` is a NON-authoritative readable alias only —
 * its trust would otherwise root in domain/TLS ownership, which breaks if the
 * domain changes hands. So the handle↔key binding is asserted by the `did:key`
 * ITSELF: a compact EdDSA JWS `{ iss, sub, handle, iat }` signed by the session
 * key, verifiable by anyone against the key embedded in the DID — no domain, no
 * registry. The apex (`identity.ts::verifyHandleAttestation`) and the kotoba log
 * carry it; a forged did:web document is detectable.
 */

import type { SessionKey } from './session-key.js';

function b64url(bytes: Uint8Array): string {
	let bin = '';
	for (const b of bytes) bin += String.fromCharCode(b);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
function jsonB64url(o: unknown): string {
	return b64url(new TextEncoder().encode(JSON.stringify(o)));
}

/**
 * Sign a self-certifying handle attestation with the controller `did:key`.
 * Returns a compact EdDSA JWS that binds the handle to the key WITHOUT any
 * domain trust. `iat` (and optional `exp`) are injected so this stays
 * deterministic + testable. Omit `exp` for a permanent binding (the kotoba
 * append-only record is the as-of history; rotation supersedes it).
 */
export async function signHandleAttestation(
	sessionKey: SessionKey,
	handle: string,
	iat: number,
	exp?: number,
): Promise<string> {
	const header = { alg: 'EdDSA', typ: 'handle-attest+jwt' };
	const payload: Record<string, unknown> = {
		iss: sessionKey.didKey,
		sub: sessionKey.didKey,
		handle,
		iat,
	};
	if (exp !== undefined) payload.exp = exp;
	const signingInput = `${jsonB64url(header)}.${jsonB64url(payload)}`;
	const sig = new Uint8Array(
		await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, new TextEncoder().encode(signingInput)),
	);
	return `${signingInput}.${b64url(sig)}`;
}

/**
 * The canonical, domain-independent DID Document for this member. `id` is the
 * `did:key`; `did:web:etzhayyim.com:<handle>` is only an `alsoKnownAs` alias.
 */
export function canonicalDidDoc(sessionKey: SessionKey, handle?: string): Record<string, unknown> {
	const didKey = sessionKey.didKey;
	const alsoKnownAs: string[] = [];
	if (handle) alsoKnownAs.push(`did:web:etzhayyim.com:${handle}`);
	return {
		'@context': ['https://www.w3.org/ns/did/v1'],
		id: didKey,
		alsoKnownAs,
		verificationMethod: [
			{
				id: `${didKey}#key-1`,
				type: 'Ed25519VerificationKey2020',
				controller: didKey,
				publicKeyMultibase: didKey.slice('did:key:'.length),
			},
		],
		authentication: [`${didKey}#key-1`],
		assertionMethod: [`${didKey}#key-1`],
	};
}
