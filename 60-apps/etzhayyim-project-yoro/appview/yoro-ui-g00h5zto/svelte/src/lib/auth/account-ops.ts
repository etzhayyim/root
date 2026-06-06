/**
 * Account operations over the domain-independent identity (ADR-2606061800 →
 * 2606062600). Canonical identity = the controller `did:key` (self-certifying).
 * The account record is a **member-signed, content-addressed block** published
 * to the apex `block.put` (main's `kotoba-publish`: verify sig → KV → KotobaRoot
 * DO root advance → IPFS pin via kotobase.net) — NOT a central-node write (those
 * are operator-local, ADR-2606013200). This is the most domain-independent form:
 * a CID signed by the member's key, dependent on neither domain nor a central
 * node. Proven live (`block.put` → `{ok:true}`). Best-effort: the local session
 * is already established, so a failed publish never breaks login.
 */

import type { SessionKey } from './session-key.js';
import { signHandleAttestation } from './identity.js';
import {
	publishSignedRecord,
	accountGraph,
	type BlockPublishDeps,
	type BlockPublishOutcome,
} from './block-publish.js';

export type { BlockPublishOutcome as AccountWriteOutcome } from './block-publish.js';

function nowMsOf(over?: { now?: () => number }): number {
	return over?.now ? over.now() : Date.now();
}

/**
 * Publish (or update) the account record block: the canonical `did:key`, a
 * **self-certifying handle attestation** (the did:key signs `{iss,handle}`), and
 * optional profile. The block is content-addressed + member-signed —
 * domain-independent.
 */
export async function publishAccount(
	sessionKey: SessionKey,
	handle: string,
	profile: Record<string, string> = {},
	over: { now?: () => number } & BlockPublishDeps = {},
	prevRoot?: string,
): Promise<BlockPublishOutcome> {
	const nowMs = nowMsOf(over);
	const attestation = await signHandleAttestation(sessionKey, handle, Math.floor(nowMs / 1000));
	const record: Record<string, unknown> = {
		type: 'account/register',
		'account/did': sessionKey.didKey,
		'account/controller': sessionKey.didKey,
		'account/handle': handle,
		'account/handle-attestation': attestation,
		iat: Math.floor(nowMs / 1000),
	};
	for (const [k, v] of Object.entries(profile)) if (typeof v === 'string') record[`account/${k}`] = v;
	return publishSignedRecord(sessionKey, accountGraph(sessionKey), record, prevRoot, over);
}

/**
 * Multi-device add: publish a wrapped-ARK record for a NEW device's passkey
 * credential, signed by THIS (already-enrolled) device. The new device later
 * reads it and unwraps with its own PRF to recover the SAME ARK → SAME did:key.
 * The wrap is opaque (useless without the new passkey's PRF).
 */
export async function enrollDevice(
	sessionKey: SessionKey,
	newCredentialId: string,
	wrappedArkB64: string,
	over: { now?: () => number } & BlockPublishDeps = {},
	prevRoot?: string,
): Promise<BlockPublishOutcome> {
	const record = {
		type: 'account/device',
		'account/did': sessionKey.didKey,
		'account/device-credential': newCredentialId,
		'account/wrapped-ark': wrappedArkB64,
		iat: Math.floor(nowMsOf(over) / 1000),
	};
	return publishSignedRecord(sessionKey, accountGraph(sessionKey), record, prevRoot, over);
}

/**
 * Key rotation: publish a record naming a new controller `did:key` + an
 * append-only rotation entry, SIGNED BY THE CURRENT key (so the rotation is
 * authorized by the holder of the key being retired). The content-addressed log
 * keeps the full rotation history (非終末論; the old key's prior records stay
 * auditable). did:web is unaffected — it only ever aliased the controller.
 */
export async function rotateKey(
	currentSessionKey: SessionKey,
	newDidKey: string,
	rotationIndex: number,
	over: { now?: () => number } & BlockPublishDeps = {},
	prevRoot?: string,
): Promise<BlockPublishOutcome> {
	const at = new Date(nowMsOf(over)).toISOString().replace(/\.\d{3}Z$/, 'Z');
	const record = {
		type: 'account/rotation',
		'account/did': currentSessionKey.didKey,
		'account/controller': newDidKey,
		[`account/rotation/${rotationIndex}`]: `${currentSessionKey.didKey}->${newDidKey}@${at}`,
		iat: Math.floor(nowMsOf(over) / 1000),
	};
	return publishSignedRecord(currentSessionKey, accountGraph(currentSessionKey), record, prevRoot, over);
}
