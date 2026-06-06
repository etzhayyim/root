/**
 * Member-signed kotoba-write CACAO + account-record helpers (ADR-2606061800).
 *
 * The member's controller `did:key` signs a kotoba-scoped CACAO (aud = node
 * `operator_did`, `kotoba://op/datom:transact`) which the apex Worker re-encodes
 * to CBOR and relays to the node's `kg.ingest` (proven end-to-end). All account
 * writes — register, device-enroll (multi-device), key-rotation — are
 * `account.<did:key>` entities authorized by THIS CACAO; the record is keyed by
 * the self-certifying `did:key`, never the domain.
 *
 * Wire details that differ from the apex login CACAO (matched to the kotoba
 * node's verifier, verified live): timestamps are **second-precision**
 * (`…SSZ`, no millis — kotoba's delegation check rejects millis) and the
 * signature is **base64url** (kotoba decodes base64url first). Deterministic
 * (injected clock/nonce) for testability.
 */

import type { SessionKey } from './session-key.js';
import { siweMessage, type Cacao } from './cacao.js';

export interface KotobaClaim {
	pred: string;
	value: string;
}

export interface KotobaWriteDeps {
	/** millis since epoch (injected — no Date.now here). */
	now: () => number;
	/** opaque single-use nonce. */
	nonce: () => string;
	/** CACAO lifetime in seconds (default 5 min). */
	ttlSecs?: number;
	/** fetch impl (defaults to global). */
	fetch?: typeof fetch;
	/** apex origin (defaults to current origin → same-origin). */
	origin?: string;
}

/** second-precision strict-UTC ISO-8601 (kotoba delegation requires no millis). */
function isoZSeconds(ms: number): string {
	return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function b64url(bytes: Uint8Array): string {
	let bin = '';
	for (const b of bytes) bin += String.fromCharCode(b);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

const APEX_ORIGIN = 'https://etzhayyim.com';
const CONFIG_PATH = '/xrpc/com.etzhayyim.authz.kotobaWriteConfig';
const REGISTER_PATH = '/xrpc/com.etzhayyim.authz.registerAccount';

export interface KotobaWriteConfig {
	operatorDid: string | null;
	writeEnabled: boolean;
}

/** Fetch the node operator_did (the required CACAO aud) + whether writes are on. */
export async function fetchKotobaWriteConfig(deps?: Partial<KotobaWriteDeps>): Promise<KotobaWriteConfig> {
	const f = deps?.fetch ?? fetch;
	const base = deps?.origin ?? APEX_ORIGIN;
	try {
		const r = await f(`${base}${CONFIG_PATH}`, { method: 'GET' });
		if (!r.ok) return { operatorDid: null, writeEnabled: false };
		const j = (await r.json()) as KotobaWriteConfig;
		return { operatorDid: j.operatorDid ?? null, writeEnabled: !!j.writeEnabled };
	} catch {
		return { operatorDid: null, writeEnabled: false };
	}
}

/**
 * Build + sign a kotoba-scoped write CACAO with the controller `did:key`. The
 * issuer IS the controller key (the record is `account.<didKey>`), aud is the
 * node operator_did, capability is `datom:transact`.
 */
export async function signKotobaWriteCacao(
	sessionKey: SessionKey,
	operatorDid: string,
	deps: KotobaWriteDeps,
): Promise<Cacao> {
	const nowMs = deps.now();
	const ttl = (deps.ttlSecs ?? 300) * 1000;
	const unsigned: Cacao = {
		h: { t: 'eip4361' },
		p: {
			iss: sessionKey.didKey,
			aud: operatorDid,
			iat: isoZSeconds(nowMs),
			exp: isoZSeconds(nowMs + ttl),
			nonce: deps.nonce(),
			domain: 'etzhayyim.com',
			statement: 'etzhayyim account write',
			version: '1',
			resources: ['kotoba://op/datom:transact'],
		},
		s: { t: '', s: '' },
	};
	const sig = new Uint8Array(
		await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, new TextEncoder().encode(siweMessage(unsigned))),
	);
	return { ...unsigned, s: { t: 'EdDSA', s: b64url(sig) } };
}

export interface AccountWriteOutcome {
	ok: boolean;
	gated?: boolean;
	did?: string;
	reason?: string;
}

/**
 * POST a member-signed account write to the apex relay (which CBOR-encodes +
 * forwards to kotoba `kg.ingest`). `claims` is the exact record claim set:
 *   - register     → account/did, account/controller, account/handle, account/handle-attestation, …profile
 *   - device-enroll→ account/device/<credId> = wrapped-ARK b64
 *   - rotate       → account/controller = newDid, account/rotation/<n>
 * Best-effort: a `gated`/error response leaves the local session intact.
 */
export async function postAccountWrite(
	cacao: Cacao,
	id: string,
	claims: KotobaClaim[],
	deps: Partial<KotobaWriteDeps> = {},
	labelEn?: string,
): Promise<AccountWriteOutcome> {
	const f = deps.fetch ?? fetch;
	const base = deps.origin ?? APEX_ORIGIN;
	try {
		const r = await f(`${base}${REGISTER_PATH}`, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ cacao, id, claims, labelEn }),
		});
		const j = (await r.json().catch(() => ({}))) as AccountWriteOutcome;
		return { ok: j.ok === true, gated: j.gated, did: j.did, reason: j.reason };
	} catch (e) {
		return { ok: false, reason: e instanceof Error ? e.message : String(e) };
	}
}
