/**
 * Messaging XRPC client — all requests via atproto.etzhayyim.com (AT Protocol compliant).
 *
 * PDS is the sole XRPC endpoint. App-specific routing is handled by PDS
 * via atproto-proxy header (DID → App Worker).
 */
import { get } from 'svelte/store';
import { currentOrg, clerkUser, getSessionToken } from '../auth.js';
import { AtpAgent } from '@etzhayyim/sdk/atproto';

const _agent = new AtpAgent({ service: 'https://atproto.etzhayyim.com' });

// ─── XRPC messaging transport (via PDS) ──────────────────────────────────────

async function buildHeaders(nanoid: string): Promise<Record<string, string>> {
	const h: Record<string, string> = { 'content-type': 'application/json' };
	const token = await getSessionToken();
	if (token) h.authorization = `Bearer ${token}`;
	const user = get(clerkUser);
	if (user?.id) h['x-etzhayyim-user-id'] = user.id;
	const org = get(currentOrg);
	if (org?.id) h['x-etzhayyim-org-id'] = org.id;
	h['atproto-proxy'] = `did:web:${nanoid}.etzhayyim.com#atprotoLabeler`;
	return h;
}

async function messagingXrpc<T = Record<string, unknown>>(
	nanoid: string,
	nsid: string,
	body: Record<string, unknown> = {},
): Promise<T> {
	const headers = await buildHeaders(nanoid);
	const res = await _agent.api.call(nsid, body, undefined, { headers });
	return res.data as T;
}

// ─── Messaging client facade ─────────────────────────────────────────────────

export interface MessagingClient {
	command<T = Record<string, unknown>>(method: string, body?: Record<string, unknown>): Promise<T>;
	query<T = Record<string, unknown>>(method: string, body?: Record<string, unknown>): Promise<T>;
}

const clientCache = new Map<string, MessagingClient>();

/** Get or create an XRPC messaging client for an app. */
export function getMessagingCommandClient(nanoid: string): MessagingClient {
	return getMessagingClient(nanoid);
}

/** Get or create an XRPC messaging client for an app. */
export function getMessagingQueryClient(nanoid: string): MessagingClient {
	return getMessagingClient(nanoid);
}

/** Get or create an XRPC messaging client for an app. */
export function getMessagingClient(nanoid: string): MessagingClient {
	let client = clientCache.get(nanoid);
	if (client) return client;

	client = {
		async command<T = Record<string, unknown>>(method: string, body: Record<string, unknown> = {}): Promise<T> {
			const nsid = `com.etzhayyim.actor.messaging.${method.charAt(0).toLowerCase()}${method.slice(1)}`;
			return messagingXrpc<T>(nanoid, nsid, body);
		},
		async query<T = Record<string, unknown>>(method: string, body: Record<string, unknown> = {}): Promise<T> {
			const nsid = `com.etzhayyim.actor.messaging.${method.charAt(0).toLowerCase()}${method.slice(1)}`;
			return messagingXrpc<T>(nanoid, nsid, body);
		},
	};
	clientCache.set(nanoid, client);
	return client;
}

/** Clear cached clients (e.g. on auth change). */
export function clearMessagingClients(): void {
	clientCache.clear();
}
