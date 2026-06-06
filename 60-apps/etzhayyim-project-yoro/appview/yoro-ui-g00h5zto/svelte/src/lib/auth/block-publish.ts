/**
 * Member-signed content-addressed block publishing (ADR-2606061800 → 2606062600).
 *
 * The account record is NOT written to a central kotoba node (writes there are
 * operator-local, ADR-2606013200). It is published as a **member-signed,
 * content-addressed block** to the apex `com.etzhayyim.apps.kotoba.block.put`
 * (main's `kotoba-publish`: verifies the member sig, stores the block in KV,
 * advances the graph root via the KotobaRoot Durable Object, and the block is
 * IPFS-pinned via kotobase.net). This is the most domain-independent identity
 * form: the record is a CID (content-address) signed by the member's `did:key` —
 * it depends on neither the domain nor a central node. Proven live (`ok:true`).
 *
 * CID = `sha2-256` raw CIDv1 (`b`+base32), byte-identical to the apex
 * `cid.ts::computeCidV1`. The block.put author DID uses the `did:key:z`+hex(32B
 * pubkey) form (the node/kotoba-publish convention) — the SAME Ed25519 key as the
 * standard `did:key:z6Mk…` login identity, which is carried inside the record as
 * `account/did` (the canonical, login-linked identity).
 */

import type { SessionKey } from './session-key.js';

// RFC4648 base32 lower, no padding — multibase 'b' (matches apex cid.ts).
const B32 = 'abcdefghijklmnopqrstuvwxyz234567';
function base32(bytes: Uint8Array): string {
	let bits = 0;
	let val = 0;
	let out = '';
	for (const b of bytes) {
		val = (val << 8) | b;
		bits += 8;
		while (bits >= 5) {
			out += B32[(val >>> (bits - 5)) & 31];
			bits -= 5;
		}
	}
	if (bits > 0) out += B32[(val << (5 - bits)) & 31];
	return out;
}

function bytesToHex(b: Uint8Array): string {
	let o = '';
	for (const x of b) o += x.toString(16).padStart(2, '0');
	return o;
}

/** `sha2-256` raw CIDv1 of `bytes` → `{ str:'bafkrei…', bytes }` (the 36 CID bytes). */
export async function cidV1(bytes: Uint8Array): Promise<{ str: string; bytes: Uint8Array }> {
	const h = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes as BufferSource));
	const cid = new Uint8Array(36);
	cid.set([0x01, 0x55, 0x12, 0x20], 0); // cidv1 | raw | sha2-256 | 32
	cid.set(h, 4);
	return { str: 'b' + base32(cid), bytes: cid };
}

/** The `did:key:z`+hex(32B pubkey) form that `block.put` / the kotoba node use. */
export function didKeyHex(sessionKey: SessionKey): string {
	return 'did:key:z' + bytesToHex(sessionKey.publicKey);
}

/** Per-member account graph (no cross-member root contention on block.put CAS). */
export function accountGraph(sessionKey: SessionKey): string {
	return `acct-${bytesToHex(sessionKey.publicKey)}`;
}

const APEX_ORIGIN = 'https://etzhayyim.com';
const BLOCK_PUT_PATH = '/xrpc/com.etzhayyim.apps.kotoba.block.put';

export interface BlockPublishOutcome {
	ok: boolean;
	root?: string;
	reason?: string;
}

export interface BlockPublishDeps {
	fetch?: typeof fetch;
	origin?: string;
}

/**
 * Publish one member-signed content-addressed record block. The block bytes =
 * `utf8(JSON.stringify(record))`; the root = its CID; the member signs the raw
 * root CID bytes (Ed25519). `prevRoot` enables optimistic-concurrency on the
 * member's own account graph. Best-effort: any failure returns `{ok:false}` and
 * never throws into the auth flow.
 */
export async function publishSignedRecord(
	sessionKey: SessionKey,
	graph: string,
	record: Record<string, unknown>,
	prevRoot?: string,
	deps: BlockPublishDeps = {},
): Promise<BlockPublishOutcome> {
	try {
		const block = new TextEncoder().encode(JSON.stringify(record));
		const cid = await cidV1(block);
		const sig = new Uint8Array(
			await crypto.subtle.sign({ name: 'Ed25519' }, sessionKey.privateKey, cid.bytes as BufferSource),
		);
		const body: Record<string, unknown> = {
			graph,
			root: cid.str,
			did: didKeyHex(sessionKey),
			sig: bytesToHex(sig),
			blocks: [{ cid: cid.str, hex: bytesToHex(block) }],
		};
		if (prevRoot) body.prevRoot = prevRoot;
		const f = deps.fetch ?? fetch;
		const base = deps.origin ?? APEX_ORIGIN;
		const r = await f(`${base}${BLOCK_PUT_PATH}`, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify(body),
		});
		const j = (await r.json().catch(() => ({}))) as { ok?: boolean; root?: string; error?: string };
		if (!r.ok || j.ok === false) return { ok: false, reason: j.error ?? `HTTP ${r.status}` };
		return { ok: true, root: j.root ?? cid.str };
	} catch (e) {
		return { ok: false, reason: e instanceof Error ? e.message : String(e) };
	}
}
