/**
 * `/profile` same-origin sign-in orchestrator (ADR-2606060000).
 *
 * Unifies the three sign-in methods into one flow that ends at the SAME-ORIGIN
 * apex verifier (`/xrpc/com.etzhayyim.authz.verifyCacao`) — no auth.etzhayyim.com
 * hop, no server-held key, no minted session. The result lets the profile page
 * flip into edit-mode; the real write is a CACAO-authorized datom:transact to the
 * kotoba node (whose NonceStore enforces single-use replay protection).
 *
 *   passkey → Ed25519 session key (did:key) → EdDSA CACAO  → verified on the apex
 *   wallet  → did:pkh:eip155 → personal_sign → eip191 CACAO → relayed to kotoba
 *
 * Dependencies (clock, fetch, randomness) are injected so this is unit-testable
 * without a browser or a live Worker.
 */

import type { SessionKey } from './session-key.js';
import {
	buildProfileCacao,
	signCacaoEd25519,
	signCacaoSiwe,
	didPkhEip155,
	graphResource,
	CAP_DATOM_TRANSACT,
	type Cacao,
	type Eip1193Provider,
} from './cacao.js';

export interface VerifyCacaoResult {
	valid: boolean;
	did?: string;
	sigType?: string;
	method?: string;
	scope?: { capabilities: string[]; graphs: string[] };
	gated?: boolean;
	reason?: string;
}

export interface SignInDeps {
	/** millis since epoch — injected (no Date.now in this module). */
	now: () => number;
	/** opaque single-use nonce. */
	nonce: () => string;
	/** fetch impl (defaults to global). */
	fetch?: typeof fetch;
	/** apex origin (defaults to current origin → truly same-origin). */
	origin?: string;
	/** session lifetime in seconds (default 15 min). */
	ttlSecs?: number;
}

const VERIFY_PATH = '/xrpc/com.etzhayyim.authz.verifyCacao';

function isoZ(ms: number): string {
	// toISOString() → `YYYY-MM-DDTHH:mm:ss.sssZ`, which is the strict-UTC `Z` form
	// the apex verifier (STRICT_UTC_ISO8601) and the Rust SSoT both accept.
	return new Date(ms).toISOString();
}

async function postVerify(
	cacao: Cacao,
	deps: SignInDeps,
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

function timestamps(deps: SignInDeps): { iat: string; exp: string } {
	const nowMs = deps.now();
	const ttl = (deps.ttlSecs ?? 900) * 1000;
	return { iat: isoZ(nowMs), exp: isoZ(nowMs + ttl) };
}

/**
 * Sign in with the passkey-derived Ed25519 session key (verified locally on the
 * apex — the primary, fully-working path). `graphCid` scopes the edit capability
 * to the actor-profile graph.
 */
export async function signInWithPasskey(
	sessionKey: SessionKey,
	graphCid: string,
	deps: SignInDeps,
): Promise<VerifyCacaoResult> {
	const { iat, exp } = timestamps(deps);
	const unsigned = buildProfileCacao({
		iss: sessionKey.didKey,
		iat,
		exp,
		nonce: deps.nonce(),
		capabilities: [CAP_DATOM_TRANSACT],
		graphs: [graphResource(graphCid)],
	});
	const signed = await signCacaoEd25519(unsigned, sessionKey);
	const { result } = await postVerify(signed, deps);
	return result;
}

/**
 * Sign in with a browser wallet (SIWE / `eip191`). Structurally verified on the
 * apex and relayed to the kotoba node for signature recovery; at R0 the apex
 * reports `gated: true` (honest — no false session) until the kotoba endpoint is
 * enabled. The signed CACAO is returned via `cacao` so the caller can present it
 * with the kotoba write.
 */
export async function signInWithWallet(
	provider: Eip1193Provider,
	address: string,
	graphCid: string,
	deps: SignInDeps & { chainId?: number },
): Promise<VerifyCacaoResult & { cacao: Cacao }> {
	const { iat, exp } = timestamps(deps);
	const iss = didPkhEip155(address, deps.chainId ?? 8453);
	const unsigned = buildProfileCacao({
		iss,
		iat,
		exp,
		nonce: deps.nonce(),
		capabilities: [CAP_DATOM_TRANSACT],
		graphs: [graphResource(graphCid)],
	});
	const signed = await signCacaoSiwe(unsigned, provider, address);
	const { result } = await postVerify(signed, deps);
	return { ...result, cacao: signed };
}
