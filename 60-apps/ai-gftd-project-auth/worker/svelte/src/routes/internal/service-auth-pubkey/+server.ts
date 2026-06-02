import { json, type RequestEvent } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { serviceAuthPubkeysMultibase, type KotobaAuthEnv } from '$lib/kotoba-service-auth';

function envOf(event: RequestEvent): KotobaAuthEnv {
	return ((event.platform as { env?: KotobaAuthEnv } | undefined)?.env ?? {}) as KotobaAuthEnv;
}

/**
 * Publishes the P-256 service-auth verification key(s) as did:key multibase so
 * the PDS can append them to atproto.gftd.ai's did.json. The PDS verifier
 * (verifyServiceAuthJWT) decodes the `0x80 0x24` (P-256) multicodec prefix; the
 * PDS otherwise only publishes secp256k1 repo keys, so without this the minted
 * ES256 JWTs would not verify. Public, read-only, no auth (it is public key
 * material). Includes the rotation `_NEXT` key when configured.
 */
export const GET: RequestHandler = async (event) => {
	const keys = serviceAuthPubkeysMultibase(envOf(event));
	const headers = new Headers({ 'cache-control': 'public, max-age=300' });
	return json({ keys, publicKeyMultibase: keys.find((k) => k.kind === 'current')?.multibase ?? null }, { headers });
};
