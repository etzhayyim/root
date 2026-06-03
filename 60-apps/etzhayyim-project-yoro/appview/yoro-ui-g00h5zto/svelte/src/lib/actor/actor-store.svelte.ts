/**
 * Actor profile store — fetches AT Protocol actor profiles with AT Protocol extensions.
 */

import { getAuthorProfile } from '$lib/atproto-agent';
import type { ActorProfileView } from './types.js';

/** Cached profiles by nanoid. */
const _cache = new Map<string, ActorProfileView>();

/** In-flight fetches by nanoid (dedup). */
const _inflight = new Map<string, Promise<ActorProfileView>>();

/**
 * Fetch actor profile view via app.bsky.actor.getProfile XRPC.
 * Falls back to /_app/meta if XRPC fails.
 */
export async function fetchActorProfileView(nanoid: string, appBaseUrl?: string): Promise<ActorProfileView> {
	const cached = _cache.get(nanoid);
	if (cached) return cached;

	const existing = _inflight.get(nanoid);
	if (existing) return existing;

	const p = _doFetch(nanoid, appBaseUrl ?? `https://${nanoid}.etzhayyim.com`);
	_inflight.set(nanoid, p);
	try {
		const profile = await p;
		_cache.set(nanoid, profile);
		return profile;
	} finally {
		_inflight.delete(nanoid);
	}
}

async function _doFetch(nanoid: string, _appBaseUrl: string): Promise<ActorProfileView> {
	const did = `did:web:${nanoid}.etzhayyim.com`;

	// Single path: PDS XRPC getAuthorProfile → graph SQL path → RisingWave
	const profile = await getAuthorProfile(did);
	const ext = profile as unknown as Record<string, unknown>;
	return {
		...profile,
		nanoid,
		performerType: (ext.performerType as ActorProfileView['performerType']) ?? 'service',
		contentMode: (ext.contentMode as ActorProfileView['contentMode']) ?? 'timeline',
		accent: ext.accent as string | undefined,
		icon: ext.icon as string | undefined,
		service: ext.service as ActorProfileView['service'],
		system: ext.system as ActorProfileView['system'],
		person: ext.person as ActorProfileView['person'],
		organization: ext.organization as ActorProfileView['organization'],
		embedUrl: ext.embedUrl as string | undefined,
		gameConfig: ext.gameConfig as ActorProfileView['gameConfig'],
	};
}

function _inferContentMode(meta: Record<string, unknown>): ActorProfileView['contentMode'] {
	if (meta.contentMode) return meta.contentMode as ActorProfileView['contentMode'];
	const ui = meta.ui as string | undefined;
	if (!ui) return 'timeline';
	if (ui === 'game') return 'game';
	if (ui === 'iframe' || ui === 'fullapp' || ui === 'full' || ui === 'esm') return 'interactive';
	return 'timeline';
}

/** Get cached actor profile view (sync). */
export function getCachedActorProfileView(nanoid: string): ActorProfileView | undefined {
	return _cache.get(nanoid);
}

/** Invalidate cached profile. */
export function invalidateActorProfile(nanoid: string): void {
	_cache.delete(nanoid);
}
