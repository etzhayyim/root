import { json, text, type RequestEvent } from '@sveltejs/kit';

export const YORO_SITE_ORIGIN = 'https://yoro.etzhayyim.com';
export const DEFAULT_MCP_ROUTER_URL = 'https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message';

export type YoroEnv = Record<string, unknown> & {
	AGENTGATEWAY_MCP_ROUTER_URL?: string;
	MCP_ROUTER_URL?: string;
	HITL_API_KEY?: string;
	TERMINAL_AGENT_URL?: string;
	TERMINAL_AGENT_API_KEY?: string;
	LG_PREGEL_URL?: string;
	LG_PREGEL_API_KEY?: string;
	CACHE_PURGE_API_KEY?: string;
	CACHE_PURGE_CF_API_TOKEN?: string;
	CACHE_PURGE_CF_ZONE_ID?: string;
};

export function envOf(event: RequestEvent): YoroEnv {
	return ((event.platform as { env?: YoroEnv } | undefined)?.env ?? {}) as YoroEnv;
}

export function mcpRouterUrl(env: YoroEnv): string {
	return (
		typeof env.AGENTGATEWAY_MCP_ROUTER_URL === 'string' && env.AGENTGATEWAY_MCP_ROUTER_URL.trim()
			? env.AGENTGATEWAY_MCP_ROUTER_URL
			: typeof env.MCP_ROUTER_URL === 'string' && env.MCP_ROUTER_URL.trim()
				? env.MCP_ROUTER_URL
				: DEFAULT_MCP_ROUTER_URL
	).replace(/\/+$/, '');
}

export function nowISO(): string {
	return new Date().toISOString();
}

export function publicJson(body: unknown, init: ResponseInit = {}): Response {
	const headers = new Headers(init.headers);
	headers.set('content-type', 'application/json; charset=utf-8');
	if (!headers.has('cache-control')) headers.set('cache-control', 'public, max-age=300');
	return new Response(JSON.stringify(body, null, 2), { ...init, headers });
}

export function noStoreJson(body: unknown, init: ResponseInit = {}): Response {
	const headers = new Headers(init.headers);
	headers.set('cache-control', 'no-store');
	return json(body, { ...init, headers });
}

export function markdown(body: string, init: ResponseInit = {}): Response {
	return text(body, {
		...init,
		headers: {
			'content-type': 'text/markdown; charset=utf-8',
			'cache-control': 'public, max-age=300',
			...(init.headers as Record<string, string> | undefined)
		}
	});
}

export function corsHeaders(origin: string | null): HeadersInit {
	return {
		'access-control-allow-origin': origin ?? '*',
		'access-control-allow-methods': 'GET,POST,OPTIONS',
		'access-control-allow-headers': 'content-type,authorization',
		'access-control-max-age': '86400'
	};
}

export async function proxyJsonRpcToMcpRouter(event: RequestEvent): Promise<Response> {
	const env = envOf(event);
	const targetUrl = mcpRouterUrl(env);
	const headers = new Headers(event.request.headers);
	headers.delete('host');
	headers.set('content-type', headers.get('content-type') ?? 'application/json');
	headers.set('x-etzhayyim-bff', 'yoro-sveltekit');

	const resp = await fetch(targetUrl, {
		method: event.request.method,
		headers,
		body: event.request.method === 'GET' || event.request.method === 'HEAD' ? undefined : event.request.body,
		// @ts-expect-error Cloudflare/undici streaming request bodies need duplex.
		duplex: 'half'
	});
	const outHeaders = new Headers(resp.headers);
	outHeaders.set('cache-control', 'no-store');
	outHeaders.set('x-etzhayyim-upstream', targetUrl);
	return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: outHeaders });
}

export async function proxyPrefix(event: RequestEvent, prefix: string, baseUrl: string, apiKey?: string): Promise<Response> {
	const url = new URL(event.request.url);
	const upstream = baseUrl.replace(/\/+$/, '') + url.pathname.replace(prefix, '') + url.search;
	const headers = new Headers(event.request.headers);
	headers.delete('host');
	if (apiKey?.trim()) headers.set('x-api-key', apiKey.trim());

	const resp = await fetch(upstream, {
		method: event.request.method,
		headers,
		body: ['GET', 'HEAD'].includes(event.request.method) ? undefined : event.request.body,
		// @ts-expect-error Cloudflare/undici streaming request bodies need duplex.
		duplex: 'half'
	});
	const outHeaders = new Headers(resp.headers);
	outHeaders.set('access-control-allow-origin', event.request.headers.get('origin') ?? '*');
	outHeaders.set('cache-control', 'no-store');
	return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: outHeaders });
}

export function authorizeBearer(event: RequestEvent, token?: string): Response | null {
	const expected = token?.trim();
	if (!expected) return null;
	const authz = event.request.headers.get('authorization') ?? '';
	const actual = authz.startsWith('Bearer ') ? authz.slice(7).trim() : '';
	return actual === expected ? null : noStoreJson({ error: 'Unauthorized' }, { status: 401 });
}
