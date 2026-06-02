/**
 * Fetch transport for the opaque wrapped-ARK store (ADR-2606014000 L1),
 * kotoba-server `com.etzhayyim.account.{put,get}.wrapped.ark`. The server stores the
 * `wrapArk` ciphertext but cannot read it — the wrapping key is the device's
 * WebAuthn PRF output. Build `PutWrap` / `GetWrap` closures for `key-hierarchy.ts`.
 */

import type { PutWrap, GetWrap } from './key-hierarchy.js';

/** Default kotoba substrate host. Override per deployment / PDS-proxy routing. */
const DEFAULT_KOTOBA_BASE = 'https://kotoba.etzhayyim.com';

export function makePutWrap(accessToken: string, kotobaBase = DEFAULT_KOTOBA_BASE): PutWrap {
	return async (did, credentialId, wrappedArkB64) => {
		const resp = await fetch(`${kotobaBase}/xrpc/com.etzhayyim.account.put.wrapped.ark`, {
			method: 'POST',
			headers: { 'content-type': 'application/json', authorization: `Bearer ${accessToken}` },
			body: JSON.stringify({ did, credentialId, wrappedArk: wrappedArkB64 }),
		});
		return resp.ok;
	};
}

export function makeGetWrap(accessToken: string, kotobaBase = DEFAULT_KOTOBA_BASE): GetWrap {
	return async (did, credentialId) => {
		const url = new URL(`${kotobaBase}/xrpc/com.etzhayyim.account.get.wrapped.ark`);
		url.searchParams.set('did', did);
		url.searchParams.set('credentialId', credentialId);
		const resp = await fetch(url, { headers: { authorization: `Bearer ${accessToken}` } });
		if (resp.status === 404) return null;
		if (!resp.ok) throw new Error(`getWrappedArk failed: ${resp.status}`);
		const body = (await resp.json()) as { wrappedArk?: string };
		return body.wrappedArk ?? null;
	};
}
