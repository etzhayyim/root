/**
 * Client-side CACAO (CAIP-74) builder + signer for same-origin `/profile` auth.
 * ADR-2606060000.
 *
 * Three sign-in methods produce ONE artifact — a member-signed CACAO — which the
 * apex Worker (`com.etzhayyim.authz.verifyCacao`, same origin, no auth subdomain,
 * no server key) verifies and turns into "DID control proven + capability scope".
 *
 *   - passkey  → Ed25519 session key (did:key) signs an `EdDSA` CACAO.
 *   - wallet   → EIP-1193 `personal_sign` over the SIWE plaintext → `eip191` CACAO.
 *
 * The SIWE plaintext reconstruction here is BYTE-IDENTICAL to the apex verifier
 * (`50-infra/etzhayyim-did-web/src/cacao.ts`) and the Rust SSoT
 * (`kotoba-auth/src/cacao.rs siwe_message`), so the same token verifies on the
 * Worker AND on the kotoba node. Timestamps are injected (no `Date.now()` in this
 * library) so it stays deterministic + testable.
 */

import type { SessionKey } from './session-key.js';

export interface CacaoPayload {
	iss: string;
	aud: string;
	iat: string;
	exp?: string;
	nonce: string;
	domain?: string;
	statement?: string;
	version?: string;
	resources?: string[];
}

export interface Cacao {
	h: { t: string };
	p: CacaoPayload;
	s: { t: string; s: string };
}

const APEX_AUD = 'did:web:etzhayyim.com';
const APEX_DOMAIN = 'etzhayyim.com';

/** kotoba capability for editing one's own profile record (a datom transact). */
export const CAP_DATOM_TRANSACT = 'kotoba://op/datom:transact';
export const CAP_DATOM_READ = 'kotoba://op/datom:read';
/**
 * Pure proof-of-control capability used by the same-origin login/signup gate
 * (no write intent — the apex Worker only confirms DID control + freshness).
 */
export const CAP_ACCOUNT_LOGIN = 'kotoba://op/account:login';
/** Register/publish one's own account record (handle alias + profile) to kotoba. */
export const CAP_ACCOUNT_REGISTER = 'kotoba://op/account:register';
/** Public actor-profile graph (ADR-2606013800 `actors-v1`). */
export function graphResource(graphCid: string): string {
	return `kotoba://graph/${graphCid}`;
}

export interface BuildCacaoParams {
	iss: string;
	/** ISO-8601 UTC `Z` issued-at. */
	iat: string;
	/** ISO-8601 UTC `Z` expiry. */
	exp: string;
	/** single-use nonce (hex/opaque). */
	nonce: string;
	capabilities: string[];
	graphs: string[];
	statement?: string;
}

/** Build an unsigned profile-edit CACAO bound to the apex origin. */
export function buildProfileCacao(params: BuildCacaoParams): Cacao {
	return {
		h: { t: 'eip4361' },
		p: {
			iss: params.iss,
			aud: APEX_AUD,
			iat: params.iat,
			exp: params.exp,
			nonce: params.nonce,
			domain: APEX_DOMAIN,
			statement: params.statement ?? 'Edit your etzhayyim profile',
			version: '1',
			resources: [...params.capabilities, ...params.graphs],
		},
		s: { t: '', s: '' },
	};
}

/** Reconstruct the SIWE plaintext — byte-identical to the apex + Rust verifier. */
export function siweMessage(cacao: Cacao): string {
	const p = cacao.p;
	const segments = p.iss.split(':');
	const address = segments[segments.length - 1] || p.iss;
	const chainId = p.iss.startsWith('did:key:')
		? '1'
		: segments.length >= 2
			? segments[segments.length - 2]
			: '1';

	const lines: string[] = [];
	lines.push(`${p.domain ?? ''} wants you to sign in with your Ethereum account:`);
	lines.push(address);
	lines.push('');
	if (p.statement) {
		lines.push(p.statement);
		lines.push('');
	}
	lines.push(`URI: ${p.aud}`);
	lines.push(`Version: ${p.version ?? '1'}`);
	lines.push(`Chain ID: ${chainId}`);
	lines.push(`Nonce: ${p.nonce}`);
	lines.push(`Issued At: ${p.iat}`);
	if (p.exp) lines.push(`Expiration Time: ${p.exp}`);
	if (p.resources && p.resources.length > 0) {
		lines.push('Resources:');
		for (const r of p.resources) lines.push(`- ${r}`);
	}
	return lines.join('\n');
}

function bytesToHex(bytes: Uint8Array): string {
	let out = '';
	for (const b of bytes) out += b.toString(16).padStart(2, '0');
	return out;
}

/**
 * Sign a CACAO with the passkey-derived Ed25519 session key (`EdDSA`). The
 * issuer MUST be the session key's `did:key` — the apex verifies the signature
 * against the key embedded in that DID (trustless).
 */
export async function signCacaoEd25519(cacao: Cacao, sessionKey: SessionKey): Promise<Cacao> {
	if (cacao.p.iss !== sessionKey.didKey) {
		throw new Error('CACAO iss must equal the session key did:key for EdDSA signing');
	}
	const msg = new TextEncoder().encode(siweMessage(cacao));
	const sig = new Uint8Array(
		await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, msg),
	);
	return { ...cacao, s: { t: 'EdDSA', s: bytesToHex(sig) } };
}

/** Minimal EIP-1193 provider shape (window.ethereum). */
export interface Eip1193Provider {
	request<T = unknown>(args: { method: string; params?: unknown[] }): Promise<T>;
}

/**
 * Sign a CACAO with a browser wallet via `personal_sign` (`eip191`). The issuer
 * MUST be `did:pkh:eip155:<chainId>:<address>` for the signing account. The apex
 * relays this CACAO to the kotoba node for secp256k1/ERC-1271 recovery.
 */
export async function signCacaoSiwe(
	cacao: Cacao,
	provider: Eip1193Provider,
	address: string,
): Promise<Cacao> {
	if (!cacao.p.iss.includes(address.toLowerCase()) && !cacao.p.iss.includes(address)) {
		throw new Error('CACAO iss must reference the signing address for eip191');
	}
	const message = siweMessage(cacao);
	const sig = await provider.request<string>({
		method: 'personal_sign',
		params: [message, address],
	});
	return { ...cacao, s: { t: 'eip191', s: sig } };
}

/** did:pkh for an EIP-155 account (Base mainnet default chainId 8453). */
export function didPkhEip155(address: string, chainId = 8453): string {
	return `did:pkh:eip155:${chainId}:${address.toLowerCase()}`;
}
