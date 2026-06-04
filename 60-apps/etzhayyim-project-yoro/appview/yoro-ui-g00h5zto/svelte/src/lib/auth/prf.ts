/**
 * WebAuthn PRF (`hmac-secret`) ceremony helpers — L0 of the passkey-rooted key
 * hierarchy (ADR-2606014000). The PRF lets a passkey deterministically produce a
 * 32-byte secret (`S_prf`) that never leaves the authenticator/device, which is
 * then fed into `key-tree.ts` to unwrap the Account Root Key.
 *
 * PRF is an optional WebAuthn extension (CTAP 2.1 `hmac-secret`). Not every
 * authenticator supports it, so callers MUST treat a missing PRF result as
 * "this device can't do zero-access self-custody" and fall back (the legacy
 * server-assisted path), rather than failing the sign-in.
 */

/** Stable per-account PRF salt. Bound to the RP so PRF outputs don't collide
 *  across relying parties. Stored/derived per account; constant for a given account. */
export function accountPrfSalt(accountId: string): Uint8Array {
	// Domain-separated, fixed-length salt = SHA-256(label || accountId) is computed
	// by the caller when available; here we provide a synchronous deterministic
	// fallback salt derived from the UTF-8 bytes, zero-padded/truncated to 32.
	const enc = new TextEncoder();
	const raw = enc.encode(`kotoba/prf-salt/v1:${accountId}`);
	const salt = new Uint8Array(32);
	salt.set(raw.subarray(0, 32));
	return salt;
}

/** WebAuthn `extensions` to request at registration so the credential is
 *  PRF-capable. Spread into `navigator.credentials.create({ publicKey })`. */
export function prfRegistrationExtension(): AuthenticationExtensionsClientInputs {
	return { prf: {} } as AuthenticationExtensionsClientInputs;
}

/** WebAuthn `extensions` to evaluate the PRF for `salt` during an assertion.
 *  Spread into `navigator.credentials.get({ publicKey })`. */
export function prfEvalExtension(salt: Uint8Array): AuthenticationExtensionsClientInputs {
	return { prf: { eval: { first: salt } } } as unknown as AuthenticationExtensionsClientInputs;
}

/** WebAuthn `extensions` to BOTH enable PRF and evaluate it for `salt` at
 *  REGISTRATION (`navigator.credentials.create`). Modern authenticators return
 *  `prf.results.first` directly from create, so a newly-added device can derive
 *  its PRF secret in one ceremony (used by the add-device flow). */
export function prfRegistrationEvalExtension(salt: Uint8Array): AuthenticationExtensionsClientInputs {
	return { prf: { eval: { first: salt } } } as unknown as AuthenticationExtensionsClientInputs;
}

/** True if the authenticator reported PRF support at registration. */
export function credentialSupportsPrf(credential: PublicKeyCredential): boolean {
	const ext = credential.getClientExtensionResults() as Record<string, unknown>;
	const prf = ext?.prf as { enabled?: boolean } | undefined;
	return prf?.enabled === true;
}

/**
 * Extract the 32-byte PRF secret (`prf.results.first`) from a completed WebAuthn
 * assertion. Returns `null` if the authenticator did not produce one (no PRF
 * support, or the eval extension was not requested) — the caller must then fall
 * back to server-assisted custody rather than proceed.
 */
export function extractPrfSecret(credential: PublicKeyCredential): Uint8Array | null {
	const ext = credential.getClientExtensionResults() as Record<string, unknown>;
	const prf = ext?.prf as { results?: { first?: BufferSource } } | undefined;
	const first = prf?.results?.first;
	if (!first) return null;
	const bytes =
		first instanceof ArrayBuffer ? new Uint8Array(first) : new Uint8Array(ArrayBuffer.isView(first) ? first.buffer : first);
	// PRF output is 32 bytes per the hmac-secret spec; reject anything else.
	return bytes.length === 32 ? bytes : null;
}
