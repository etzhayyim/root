/**
 * Client side of the passkey-rooted key hierarchy (ADR-2606014000).
 *
 * Mirrors the Rust `kotoba_crypto::key_tree` byte-for-byte so a key wrapped here
 * unwraps there and vice-versa (verified against Rust known-answer vectors in
 * `key-tree.test.ts`):
 *
 *   L0  WebAuthn PRF / hmac-secret  ──▶ S_prf  (32 B, never leaves the device)
 *   L1  ARK (random 32 B)           ──▶ wrapped per-passkey under KDF(S_prf), AAD = account DID
 *   L2  k_storage / k_signal / k_session = HKDF(ARK, <label>)
 *
 * Everything here runs in the browser via WebCrypto. The server only ever sees
 * the opaque `wrapArk` blob — there is no server-held wrapping key
 * (ADR-2605231525 no-server-key invariant).
 */

const enc = new TextEncoder();

/** Normalize bytes to a fresh ArrayBuffer-backed view — satisfies WebCrypto's
 *  `BufferSource` param under TS's strict typed-array (`ArrayBufferLike`) typing. */
function bs(u: Uint8Array): Uint8Array<ArrayBuffer> {
	const out = new Uint8Array(u.byteLength);
	out.set(u);
	return out as Uint8Array<ArrayBuffer>;
}

/** HKDF salt — 32 zero bytes, matching RustCrypto `Hkdf::new(None, ikm)`. */
const HKDF_ZERO_SALT = new Uint8Array(32);

/** L1 wrap-key label (HKDF info) — must equal the Rust `LABEL_ARK_WRAP`. */
const LABEL_ARK_WRAP = 'kotoba/passkey/ark-wrap/v1';
/** L2 purpose labels — must equal the Rust `LABEL_*` constants. */
export const LABEL_STORAGE = 'kotoba/storage/dek-wrap/v1';
export const LABEL_SIGNAL = 'kotoba/signal/identity/v1';
export const LABEL_SESSION = 'kotoba/session/sign/v1';

/** HKDF-SHA256(ikm, salt=32 zeros, info=label) → 32 bytes. */
async function hkdf32(ikm: Uint8Array, label: string): Promise<Uint8Array> {
	const key = await crypto.subtle.importKey('raw', bs(ikm), 'HKDF', false, ['deriveBits']);
	const bits = await crypto.subtle.deriveBits(
		{ name: 'HKDF', hash: 'SHA-256', salt: bs(HKDF_ZERO_SALT), info: bs(enc.encode(label)) },
		key,
		256,
	);
	return new Uint8Array(bits);
}

/** Per-passkey ARK-wrapping key derived from a WebAuthn PRF output. */
async function passkeyWrapKey(prfOutput: Uint8Array): Promise<CryptoKey> {
	const raw = await hkdf32(prfOutput, LABEL_ARK_WRAP);
	return crypto.subtle.importKey('raw', bs(raw), 'AES-GCM', false, ['encrypt', 'decrypt']);
}

/** Generate a fresh random Account Root Key. Call once, at account enrollment. */
export function generateArk(): Uint8Array {
	return crypto.getRandomValues(new Uint8Array(32));
}

/**
 * Wrap the ARK under a passkey's PRF output, bound to the account DID.
 * Output = `iv(12) || ciphertext || tag(16)` — identical layout to the Rust
 * `wrap_ark` (`nonce || ciphertext_with_tag`), so the Rust side can unwrap it.
 * Safe to persist publicly: useless without the device-resident PRF output.
 */
export async function wrapArk(
	prfOutput: Uint8Array,
	ark: Uint8Array,
	accountDid: string,
): Promise<Uint8Array> {
	const key = await passkeyWrapKey(prfOutput);
	const iv = crypto.getRandomValues(new Uint8Array(12));
	const ct = new Uint8Array(
		await crypto.subtle.encrypt(
			{ name: 'AES-GCM', iv: bs(iv), additionalData: bs(enc.encode(accountDid)) },
			key,
			bs(ark),
		),
	);
	const out = new Uint8Array(12 + ct.length);
	out.set(iv);
	out.set(ct, 12);
	return out;
}

/** Recover the ARK from a wrapped blob using this device's passkey PRF output. */
export async function unwrapArk(
	prfOutput: Uint8Array,
	wrapped: Uint8Array,
	accountDid: string,
): Promise<Uint8Array> {
	const key = await passkeyWrapKey(prfOutput);
	const iv = wrapped.slice(0, 12);
	const body = wrapped.slice(12);
	const pt = await crypto.subtle.decrypt(
		{ name: 'AES-GCM', iv: bs(iv), additionalData: bs(enc.encode(accountDid)) },
		key,
		bs(body),
	);
	return new Uint8Array(pt);
}

/** L2: storage DEK-wrapping key (wraps per-graph/per-record data keys). */
export function deriveStorageKey(ark: Uint8Array): Promise<Uint8Array> {
	return hkdf32(ark, LABEL_STORAGE);
}
/** L2: Signal identity seed (deterministic libsignal IdentityKey seed). */
export function deriveSignalSeed(ark: Uint8Array): Promise<Uint8Array> {
	return hkdf32(ark, LABEL_SIGNAL);
}
/** L2: session signing seed (seeds the CACAO / session keypair). */
export function deriveSessionSeed(ark: Uint8Array): Promise<Uint8Array> {
	return hkdf32(ark, LABEL_SESSION);
}
