/**
 * Ed25519 session signing key derived from the account hierarchy (ADR-2606014500
 * C-2, client side). The key is generated **on the device** from `k_session`
 * (= HKDF(ARK, "kotoba/session/sign/v1")) and only its PUBLIC half is registered
 * with the auth Worker via `com.etzhayyim.auth.registerSigningKey`. The private
 * key never leaves the browser — zero-access custody.
 *
 * Deterministic: the same ARK always yields the same key, so it is recoverable on
 * any device that can recover the ARK (via passkey PRF or guardian shares).
 * Zero-dependency: Ed25519 is derived from the 32-byte seed by wrapping it in the
 * fixed PKCS#8 prefix and importing via WebCrypto (verified in Node + modern
 * browsers).
 */

import { deriveSessionSeed } from './key-tree.js';

/** PKCS#8 DER prefix for an Ed25519 private key followed by the 32-byte seed. */
const PKCS8_ED25519_PREFIX = Uint8Array.from([
	0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20,
]);
/** Multicodec prefix for an Ed25519 public key (`ed25519-pub` = 0xed varint). */
const ED25519_MULTICODEC = Uint8Array.from([0xed, 0x01]);
const B58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

/** Standard base58btc (Bitcoin alphabet) encode — matches the Rust `multibase` crate. */
export function base58btcEncode(bytes: Uint8Array): string {
	let zeros = 0;
	while (zeros < bytes.length && bytes[zeros] === 0) zeros++;
	const digits: number[] = [];
	for (let i = zeros; i < bytes.length; i++) {
		let carry = bytes[i];
		for (let j = 0; j < digits.length; j++) {
			carry += digits[j] << 8;
			digits[j] = carry % 58;
			carry = (carry / 58) | 0;
		}
		while (carry > 0) {
			digits.push(carry % 58);
			carry = (carry / 58) | 0;
		}
	}
	let out = '1'.repeat(zeros);
	for (let i = digits.length - 1; i >= 0; i--) out += B58_ALPHABET[digits[i]];
	return out;
}

/** Decode base58btc — companion to the encoder (used in tests / verification). */
export function base58btcDecode(s: string): Uint8Array {
	let zeros = 0;
	while (zeros < s.length && s[zeros] === '1') zeros++;
	const bytes: number[] = [];
	for (let i = zeros; i < s.length; i++) {
		let carry = B58_ALPHABET.indexOf(s[i]);
		if (carry < 0) throw new Error(`invalid base58 char: ${s[i]}`);
		for (let j = 0; j < bytes.length; j++) {
			carry += bytes[j] * 58;
			bytes[j] = carry & 0xff;
			carry >>= 8;
		}
		while (carry > 0) {
			bytes.push(carry & 0xff);
			carry >>= 8;
		}
	}
	const out = new Uint8Array(zeros + bytes.length);
	for (let i = 0; i < bytes.length; i++) out[zeros + bytes.length - 1 - i] = bytes[i];
	return out;
}

/** `publicKeyMultibase` form (`z…`) of an Ed25519 public key, per did:key. */
export function ed25519PublicKeyMultibase(pub: Uint8Array): string {
	const prefixed = new Uint8Array(ED25519_MULTICODEC.length + pub.length);
	prefixed.set(ED25519_MULTICODEC);
	prefixed.set(pub, ED25519_MULTICODEC.length);
	return 'z' + base58btcEncode(prefixed);
}

export interface SessionKey {
	/** Non-exported-by-design signer (the private key material is the ARK-derived seed). */
	privateKey: CryptoKey;
	publicKey: Uint8Array;
	/** `z…` multibase, ready for `registerSigningKey` / did:key. */
	publicKeyMultibase: string;
	/** Full `did:key:z…` identifier (trustless — key is in the DID itself). */
	didKey: string;
}

/** Derive the Ed25519 session keypair deterministically from the ARK. */
export async function deriveSessionKeyPair(ark: Uint8Array): Promise<SessionKey> {
	const seed = await deriveSessionSeed(ark);
	const pkcs8 = new Uint8Array(PKCS8_ED25519_PREFIX.length + 32);
	pkcs8.set(PKCS8_ED25519_PREFIX);
	pkcs8.set(seed, PKCS8_ED25519_PREFIX.length);
	const privateKey = await crypto.subtle.importKey('pkcs8', pkcs8, { name: 'Ed25519' }, true, [
		'sign',
	]);
	const jwk = (await crypto.subtle.exportKey('jwk', privateKey)) as JsonWebKey;
	const publicKey = b64urlToBytes(jwk.x as string);
	const publicKeyMultibase = ed25519PublicKeyMultibase(publicKey);
	return { privateKey, publicKey, publicKeyMultibase, didKey: `did:key:${publicKeyMultibase}` };
}

function b64urlToBytes(s: string): Uint8Array {
	const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
	const b64 = s.replace(/-/g, '+').replace(/_/g, '/') + pad;
	const bin = atob(b64);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}

function bytesToB64url(b: Uint8Array): string {
	let bin = '';
	for (const x of b) bin += String.fromCharCode(x);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
function jsonToB64url(o: unknown): string {
	return bytesToB64url(new TextEncoder().encode(JSON.stringify(o)));
}

/**
 * Sign a session Proof-of-Possession token with the session key (ADR-2606014500
 * C-3, client side). Produces a compact EdDSA JWS — `b64url(header).b64url(payload).b64url(sig)` —
 * that the server VERIFIES (read-only) against the registered public key, instead
 * of a server-minted HS256 session JWT. The private key never leaves the device.
 *
 * `iat`/`exp` are supplied by the caller (no `Date.now()` here) so the token is
 * deterministic and testable.
 */
export async function signSessionPoP(
	sessionKey: SessionKey,
	did: string,
	iat: number,
	exp: number,
	extraClaims: Record<string, unknown> = {},
): Promise<string> {
	const header = { alg: 'EdDSA', typ: 'pop+jwt', kid: `${did}#session-key` };
	const payload = { iss: did, sub: did, iat, exp, ...extraClaims };
	const signingInput = `${jsonToB64url(header)}.${jsonToB64url(payload)}`;
	const sig = new Uint8Array(
		await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, new TextEncoder().encode(signingInput)),
	);
	return `${signingInput}.${bytesToB64url(sig)}`;
}

/**
 * Register the public half of the session key with the auth Worker (Stage C-2).
 * The server stores public-key-only — it never receives the private key.
 */
export async function registerSessionKey(
	did: string,
	publicKeyMultibase: string,
	accessToken: string,
	authBase = 'https://authn.etzhayyim.com',
): Promise<boolean> {
	const resp = await fetch(`${authBase}/xrpc/com.etzhayyim.auth.registerSigningKey`, {
		method: 'POST',
		headers: { 'content-type': 'application/json', authorization: `Bearer ${accessToken}` },
		body: JSON.stringify({ did, publicKeyMultibase, performerType: 'person' }),
	});
	return resp.ok;
}
