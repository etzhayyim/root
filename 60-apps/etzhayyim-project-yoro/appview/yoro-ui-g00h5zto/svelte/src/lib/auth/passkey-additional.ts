/**
 * Multi-device passkey enrolment — ADR-0074 Phase 1.
 *
 * Adds another WebAuthn credential to the *currently signed-in* did:etzhayyim
 * account. After this completes, the new device can drive primary signin via
 * the existing `passkeyVerifyAuth` path (the credential is registered against
 * the same DID, so signin transparently resolves either device).
 *
 * Caller must already hold a yoro session.
 */

import { getSessionToken } from './passkey';

const AUTHZ_BASE = 'https://authz.etzhayyim.com';

export interface AdditionalPasskeyResult {
	ok: boolean;
	credentialId: string;
	linkedMethods: Array<Record<string, unknown>>;
	actorScore: Record<string, unknown>;
}

function base64urlEncode(buffer: ArrayBuffer): string {
	const bytes = new Uint8Array(buffer);
	let binary = '';
	for (const b of bytes) binary += String.fromCharCode(b);
	return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function base64urlDecode(s: string): ArrayBuffer {
	let str = s.replace(/-/g, '+').replace(/_/g, '/');
	while (str.length % 4) str += '=';
	const binary = atob(str);
	const result = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i += 1) result[i] = binary.charCodeAt(i);
	return result.buffer.slice(result.byteOffset, result.byteOffset + result.byteLength);
}

async function authzPost<T>(path: string, body: unknown): Promise<T> {
	const token = await getSessionToken();
	if (!token) throw new Error('Not signed in. Sign in with your passkey first.');
	const resp = await fetch(`${AUTHZ_BASE}${path}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`,
		},
		credentials: 'include',
		body: JSON.stringify(body),
	});
	if (!resp.ok) {
		const text = await resp.text().catch((_err) => '');
		throw new Error(`${path} failed: ${resp.status} ${text}`);
	}
	return resp.json() as Promise<T>;
}

interface BeginOptions {
	challenge: string;
	rp: { id: string; name: string };
	user: { id: string; name: string; displayName: string };
	pubKeyCredParams: Array<{ type: 'public-key'; alg: number }>;
	timeout: number;
	authenticatorSelection: {
		authenticatorAttachment: AuthenticatorAttachment;
		residentKey: ResidentKeyRequirement;
		userVerification: UserVerificationRequirement;
	};
	attestation: AttestationConveyancePreference;
}

/**
 * Prompt the platform authenticator for a new credential (Touch ID, Windows
 * Hello, security key, …) and bind it to the signed-in account on the server.
 * Re-running this on a device that already has a credential is a no-op
 * upsert.
 */
export async function linkAdditionalPasskey(label?: string): Promise<AdditionalPasskeyResult> {
	if (typeof window === 'undefined' || !navigator.credentials) {
		throw new Error('WebAuthn is not supported in this environment');
	}

	const beginResp = await authzPost<BeginOptions>(
		'/xrpc/com.etzhayyim.authz.linkPasskeyAdditionalBegin',
		{ label },
	);

	const credential = (await navigator.credentials.create({
		publicKey: {
			challenge: base64urlDecode(beginResp.challenge),
			rp: beginResp.rp,
			user: {
				id: base64urlDecode(beginResp.user.id),
				name: beginResp.user.name,
				displayName: beginResp.user.displayName,
			},
			pubKeyCredParams: beginResp.pubKeyCredParams,
			timeout: beginResp.timeout,
			authenticatorSelection: beginResp.authenticatorSelection,
			attestation: beginResp.attestation,
		},
	})) as PublicKeyCredential | null;

	if (!credential) throw new Error('Passkey registration was cancelled');

	const response = credential.response as AuthenticatorAttestationResponse;
	const verify = await authzPost<AdditionalPasskeyResult>(
		'/xrpc/com.etzhayyim.authz.linkPasskeyAdditionalVerify',
		{
			challenge: beginResp.challenge,
			clientDataJson: base64urlEncode(response.clientDataJSON),
			attestationObject: base64urlEncode(response.attestationObject),
			label,
		},
	);
	return verify;
}

/** Remove an additional passkey. Refuses to remove the last passkey (server-enforced). */
export async function unlinkAdditionalPasskey(credentialId: string): Promise<{ ok: boolean }> {
	return authzPost('/xrpc/com.etzhayyim.authz.unlinkMethod', {
		provider: 'webauthn-additional',
		providerSubject: credentialId,
	});
}
