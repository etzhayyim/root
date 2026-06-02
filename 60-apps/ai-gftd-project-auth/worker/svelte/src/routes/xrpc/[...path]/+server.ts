import { json, type RequestEvent } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { mintServiceAuth, MintError, type KotobaAuthEnv, type MintRequest } from '$lib/kotoba-service-auth';

const DEFAULT_MCP_ROUTER_URL = 'https://mcp.etzhayyim.com/xrpc/ai.gftd.mcp.message';
type Env = Record<string, unknown> & { AGENTGATEWAY_MCP_ROUTER_URL?: string; MCP_ROUTER_URL?: string };
function envOf(event: RequestEvent): Env { return ((event.platform as { env?: Env } | undefined)?.env ?? {}) as Env; }
function mcpRouterUrl(env: Env): string { const configured = typeof env.AGENTGATEWAY_MCP_ROUTER_URL === 'string' && env.AGENTGATEWAY_MCP_ROUTER_URL.trim() ? env.AGENTGATEWAY_MCP_ROUTER_URL : typeof env.MCP_ROUTER_URL === 'string' && env.MCP_ROUTER_URL.trim() ? env.MCP_ROUTER_URL : DEFAULT_MCP_ROUTER_URL; return configured.replace(/\/+$/, ''); }
function noStore(body: unknown, init: ResponseInit = {}): Response { const headers = new Headers(init.headers); headers.set('cache-control', 'no-store'); return json(body, { ...init, headers }); }
export const POST: RequestHandler = async (event) => { const nsid = event.params.path; if (!nsid) return noStore({ error: 'Missing XRPC method' }, { status: 400 }); const input = await event.request.json().catch(() => ({}));
	// kotoba: mint service-auth bearers LOCALLY (DID-rooted self-signing). No
	// central MCP hop — this is the method whose remote proxy hung and took
	// platform-wide bearer minting down. Only this NSID is intercepted; all
	// other XRPC methods still fall through to the MCP router below.
	if (nsid === 'com.atproto.server.getServiceAuth') {
		try {
			const { token } = await mintServiceAuth(envOf(event) as KotobaAuthEnv, (input ?? {}) as MintRequest);
			return noStore({ token });
		} catch (e) {
			const code = e instanceof MintError ? e.code : 'mintError';
			const status = code === 'lxmNotMintable' || code === 'badIss' || code === 'badAud' ? 403 : 500;
			return noStore({ error: code, message: e instanceof Error ? e.message : String(e) }, { status });
		}
	}
	const headers = new Headers(event.request.headers); headers.delete('host'); headers.set('content-type', 'application/json'); headers.set('x-gftd-bff', 'sveltekit-edge-bff'); headers.set('x-gftd-xrpc-method', nsid); const upstream = await fetch(mcpRouterUrl(envOf(event)), { method: 'POST', headers, body: JSON.stringify({ jsonrpc: '2.0', id: crypto.randomUUID(), method: 'tools/call', params: { name: nsid, arguments: input } }) }); const upstreamText = await upstream.text(); let payload: unknown = upstreamText; try { payload = upstreamText ? JSON.parse(upstreamText) : null; } catch { /* Preserve text payload. */ } if (!upstream.ok) return noStore({ error: 'MCP router request failed', upstream: payload }, { status: upstream.status }); if (payload && typeof payload === 'object' && 'error' in payload) { const error = (payload as { error?: { message?: string } }).error; return noStore({ error: error?.message ?? 'MCP router returned an error', upstream: payload }, { status: 502 }); } const result = payload && typeof payload === 'object' && 'result' in payload ? (payload as { result?: unknown }).result : payload; const structured = result && typeof result === 'object' && 'structuredContent' in result ? (result as { structuredContent?: unknown }).structuredContent : result; return noStore(structured ?? {}); };
export const OPTIONS: RequestHandler = async () => new Response(null, { status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST,OPTIONS', 'access-control-allow-headers': 'content-type,authorization', 'access-control-max-age': '86400' } });
