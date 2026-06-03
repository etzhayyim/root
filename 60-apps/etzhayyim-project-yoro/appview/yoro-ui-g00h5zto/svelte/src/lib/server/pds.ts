/**
 * Server-side PDS fetch helpers for SSR OG tags.
 *
 * Resolution order (fastest first):
 *   1. Workers RPC (env.PDS_SERVICE) — <1ms if same-account
 *   2. HTTP fetch (atproto.etzhayyim.com) — 50-5000ms
 *
 * Calls atproto.etzhayyim.com XRPC endpoints (AT Protocol native, no auth required for public data).
 */

// Direct XRPC fetch over Worker binding (fast path) or HTTPS (fallback).
// No @etzhayyim/xrpc dependency: public reads only, no session auth required.

export interface Profile {
	did: string;
	handle: string;
	displayName: string;
	description: string;
	avatar: string;
	banner: string;
	followersCount: number;
	followsCount: number;
	postsCount: number;
	indexedAt: string;
}

export interface PdsPost {
	uri: string;
	cid: string;
	author: {
		did: string;
		handle: string;
		displayName: string;
		avatar: string;
	};
	record: {
		text: string;
		createdAt: string;
		reply?: { parent: { uri: string }; root: { uri: string } };
		embed?: {
			$type: string;
			images?: Array<{ alt: string; image: { ref: { $link: string }; mimeType: string } }>;
			external?: { uri: string; title: string; description: string };
		};
	};
	embed?: {
		$type: string;
		images?: Array<{ thumb: string; fullsize: string; alt: string }>;
		external?: { uri: string; title: string; description: string; thumb: string };
	};
	replyCount: number;
	repostCount: number;
	likeCount: number;
	quoteCount: number;
	indexedAt: string;
}

export interface PdsThreadResponse {
	thread: {
		$type: string;
		post: PdsPost;
		replies?: Array<{ post: PdsPost }>;
	};
}

// --- Direct XRPC fetch (Worker binding fast path + HTTP fallback) ---

const PDS_BASE = 'https://atproto.etzhayyim.com';
// Apex substrate front door. Registered etzhayyim actors
// (did:web:etzhayyim.com:actor:*) — including kotoba-native actors like tsumugi
// that have NO atproto repo — resolve their profile from the actor registry
// (KV → kotoba → compiled) served by the apex Worker, not from the PDS. Per
// ADR-2606013800. The PDS path stays the resolver for human members / agents.
const APEX_BASE = 'https://etzhayyim.com';
const PDS_TIMEOUT_MS = 3000;

function withHardTimeout<T>(promise: Promise<T>, timeoutMs = PDS_TIMEOUT_MS): Promise<T> {
	return new Promise<T>((resolve, reject) => {
		const timer = setTimeout(() => reject(new Error(`pds timeout (${timeoutMs}ms)`)), timeoutMs);
		promise.then(
			(value) => {
				clearTimeout(timer);
				resolve(value);
			},
			(error) => {
				clearTimeout(timer);
				reject(error);
			},
		);
	});
}

interface PdsServiceBinding {
	fetch(input: Request | string, init?: RequestInit): Promise<Response>;
}

async function xrpcGet<T>(base: string, path: string, params: Record<string, string>, doFetch: typeof fetch): Promise<T | null> {
	const qs = new URLSearchParams(params).toString();
	const url = `${base}/xrpc/${path}${qs ? `?${qs}` : ''}`;
	const init: RequestInit = {
		method: 'GET',
		headers: { accept: 'application/json' },
		signal: AbortSignal.timeout(PDS_TIMEOUT_MS),
	};
	try {
		const res = await withHardTimeout(doFetch(url, init), PDS_TIMEOUT_MS);
		if (!res.ok) return null;
		return (await res.json()) as T;
	} catch {
		return null;
	}
}

async function pdsGet<T>(path: string, params: Record<string, string>, platform?: any): Promise<T | null> {
	const binding = platform?.env?.PDS_SERVICE as PdsServiceBinding | undefined;
	const doFetch = binding ? (binding.fetch.bind(binding) as typeof fetch) : fetch;
	return xrpcGet<T>(PDS_BASE, path, params, doFetch);
}

/** Apex actor-registry resolution (plain cross-origin fetch; no PDS binding). */
async function apexGetProfile(actor: string): Promise<Profile | null> {
	return xrpcGet<Profile>(APEX_BASE, 'app.bsky.actor.getProfile', { actor }, fetch);
}

// --- Public API: tiered resolution ---

export async function resolveHandle(handle: string, platform?: any): Promise<string | null> {
	const res = await pdsGet<{ did: string }>('com.atproto.identity.resolveHandle', { handle }, platform);
	return res?.did ?? null;
}

export async function getProfile(actor: string, platform?: any): Promise<Profile | null> {
	// Registered etzhayyim actor DIDs resolve from the apex actor registry first
	// (covers kotoba-native actors with no PDS repo, e.g. tsumugi). Additive +
	// fallback-preserving: anything the registry doesn't know falls through to
	// the PDS exactly as before. Per ADR-2606013800.
	const isActorDid = actor.startsWith('did:web:etzhayyim.com:actor:');
	if (isActorDid) {
		const viaApex = await apexGetProfile(actor);
		if (viaApex) return viaApex;
	}
	const viaPds = await pdsGet<Profile>('app.bsky.actor.getProfile', { actor }, platform);
	if (viaPds) return viaPds;
	// Bare-handle actor fallback (e.g. /profile/tsumugi): try the apex registry
	// only after the PDS misses, so human-member resolution is never affected.
	if (!actor.startsWith('did:')) {
		return apexGetProfile(actor);
	}
	return null;
}

export async function getPostThread(uri: string, platform?: any): Promise<PdsThreadResponse | null> {
	return pdsGet<PdsThreadResponse>('app.bsky.feed.getPostThread', { uri, depth: '0' }, platform);
}

/** Build AT URI from handle/did + rkey */
export function makePostUri(did: string, rkey: string): string {
	return `at://${did}/app.bsky.feed.post/${rkey}`;
}

/** Extract first image thumb from post embed */
export function postImageUrl(post: PdsPost): string | null {
	if (post.embed?.images?.[0]?.thumb) return post.embed.images[0].thumb;
	if (post.embed?.external?.thumb) return post.embed.external.thumb;
	return null;
}

/** Fetch /_app/meta from an app Worker (server-side, no CORS). Returns tools array or null. */
export async function getAppMetaTools(appHost: string): Promise<string[] | null> {
	try {
		const res = await fetch(`https://${appHost}/_app/meta`, {
			headers: { Accept: 'application/json' },
			signal: AbortSignal.timeout(1000),
		});
		if (!res.ok) return null;
		const meta = await res.json() as Record<string, unknown>;
		const tools = (meta.tools ?? meta.capabilities ?? []) as unknown[];
		return Array.isArray(tools) && tools.length > 0 ? tools.map(t => typeof t === 'string' ? t : (t as any).name ?? String(t)) : null;
	} catch {
		return null;
	}
}

/** Truncate text for OG description */
export function truncate(text: string, max = 200): string {
	if (text.length <= max) return text;
	return text.slice(0, max - 1) + '\u2026';
}
