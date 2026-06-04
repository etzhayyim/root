import type { RequestHandler } from './$types';
import { proxyJsonRpcToMcpRouter, publicJson, envOf, mcpRouterUrl } from '$lib/server/bff';

export const GET: RequestHandler = async (event) => {
	const router = mcpRouterUrl(envOf(event));
	return publicJson({
		ok: true,
		bff: 'yoro-sveltekit',
		upstream: router,
		transport: 'mcp-json-rpc-over-http',
		methods: ['POST']
	});
};

export const POST: RequestHandler = async (event) => proxyJsonRpcToMcpRouter(event);

export const OPTIONS: RequestHandler = async () => new Response(null, {
	status: 204,
	headers: {
		'access-control-allow-origin': '*',
		'access-control-allow-methods': 'GET,POST,OPTIONS',
		'access-control-allow-headers': 'content-type,authorization',
		'access-control-max-age': '86400'
	}
});
