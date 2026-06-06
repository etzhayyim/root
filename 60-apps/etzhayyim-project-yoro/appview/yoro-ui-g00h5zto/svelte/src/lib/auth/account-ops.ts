/**
 * Account operations over the domain-independent identity (ADR-2606061800 →
 * 2606062600). Canonical identity = the controller `did:key`; the account record
 * is `account.<did:key>` in kotoba (self-certifying — authorized by the key's own
 * CACAO). did:web is only a readable alias. These orchestrate the kotoba-write
 * relay for the three account writes; all are best-effort (the local session is
 * already established, so a `gated`/offline response never breaks login).
 */

import type { SessionKey } from './session-key.js';
import { signHandleAttestation } from './identity.js';
import {
	fetchKotobaWriteConfig,
	signKotobaWriteCacao,
	postAccountWrite,
	type KotobaClaim,
	type KotobaWriteDeps,
	type AccountWriteOutcome,
} from './kotoba-write.js';

function defaultDeps(over: Partial<KotobaWriteDeps> = {}): KotobaWriteDeps {
	return {
		now: over.now ?? (() => Date.now()),
		nonce:
			over.nonce ??
			(() => {
				const b = crypto.getRandomValues(new Uint8Array(16));
				let s = '';
				for (const x of b) s += x.toString(16).padStart(2, '0');
				return s;
			}),
		ttlSecs: over.ttlSecs,
		fetch: over.fetch,
		origin: over.origin,
	};
}

const GATED: AccountWriteOutcome = { ok: false, gated: true, reason: 'kotoba write not configured' };

/**
 * Publish (or update) the account record: the canonical `did:key` + a
 * **self-certifying handle attestation** (the did:key signs `{iss, handle}`) +
 * optional profile. The binding is the key's own assertion — domain-independent.
 */
export async function publishAccount(
	sessionKey: SessionKey,
	handle: string,
	profile: Record<string, string> = {},
	over: Partial<KotobaWriteDeps> = {},
): Promise<AccountWriteOutcome> {
	const deps = defaultDeps(over);
	const cfg = await fetchKotobaWriteConfig(deps);
	if (!cfg.operatorDid) return GATED;
	const nowMs = deps.now();
	const attestation = await signHandleAttestation(sessionKey, handle, Math.floor(nowMs / 1000));
	const claims: KotobaClaim[] = [
		{ pred: 'account/did', value: sessionKey.didKey },
		{ pred: 'account/controller', value: sessionKey.didKey },
		{ pred: 'account/handle', value: handle },
		{ pred: 'account/handle-attestation', value: attestation },
	];
	for (const [k, v] of Object.entries(profile)) if (typeof v === 'string') claims.push({ pred: `account/${k}`, value: v });
	const cacao = await signKotobaWriteCacao(sessionKey, cfg.operatorDid, deps);
	return postAccountWrite(cacao, `account.${sessionKey.didKey}`, claims, deps, handle);
}

/**
 * Multi-device add: record a wrapped-ARK for a NEW device's passkey credential,
 * authorized by THIS (already-enrolled) device. The new device later reads
 * `account/device/<credId>` and unwraps with its own PRF to recover the SAME ARK
 * → the SAME did:key. The wrap is opaque (useless without the new passkey's PRF).
 */
export async function enrollDevice(
	sessionKey: SessionKey,
	newCredentialId: string,
	wrappedArkB64: string,
	over: Partial<KotobaWriteDeps> = {},
): Promise<AccountWriteOutcome> {
	const deps = defaultDeps(over);
	const cfg = await fetchKotobaWriteConfig(deps);
	if (!cfg.operatorDid) return GATED;
	const claims: KotobaClaim[] = [{ pred: `account/device/${newCredentialId}`, value: wrappedArkB64 }];
	const cacao = await signKotobaWriteCacao(sessionKey, cfg.operatorDid, deps);
	return postAccountWrite(cacao, `account.${sessionKey.didKey}`, claims, deps);
}

/**
 * Key rotation: record a new controller `did:key` + an append-only rotation
 * entry, SIGNED BY THE CURRENT key (so the rotation is authorized by the holder
 * of the key being retired). did:web is unaffected — it only ever aliased the
 * controller, which now points at the new key. kotoba's append-only log keeps
 * the full rotation history (非終末論; the old key's prior records stay auditable).
 */
export async function rotateKey(
	currentSessionKey: SessionKey,
	newDidKey: string,
	rotationIndex: number,
	over: Partial<KotobaWriteDeps> = {},
): Promise<AccountWriteOutcome> {
	const deps = defaultDeps(over);
	const cfg = await fetchKotobaWriteConfig(deps);
	if (!cfg.operatorDid) return GATED;
	const at = new Date(deps.now()).toISOString().replace(/\.\d{3}Z$/, 'Z');
	const claims: KotobaClaim[] = [
		{ pred: 'account/controller', value: newDidKey },
		{ pred: `account/rotation/${rotationIndex}`, value: `${currentSessionKey.didKey}->${newDidKey}@${at}` },
	];
	const cacao = await signKotobaWriteCacao(currentSessionKey, cfg.operatorDid, deps);
	return postAccountWrite(cacao, `account.${currentSessionKey.didKey}`, claims, deps);
}
