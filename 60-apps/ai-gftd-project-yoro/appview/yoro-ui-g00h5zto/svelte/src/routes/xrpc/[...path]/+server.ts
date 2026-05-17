import type { RequestHandler } from './$types';
import { noStoreJson } from '$lib/server/bff';

export const GET: RequestHandler = async ({ url }) => gone(url.pathname);
export const POST: RequestHandler = async ({ url }) => gone(url.pathname);
export const PUT: RequestHandler = async ({ url }) => gone(url.pathname);
export const DELETE: RequestHandler = async ({ url }) => gone(url.pathname);

function gone(pathname: string): Response {
	return noStoreJson({
		error: 'Gone',
		message: 'yoro.gftd.ai no longer serves XRPC. Use /api/mcp for MCP BFF calls or atproto.gftd.ai/xrpc/* for AT Protocol.',
		mcpBff: 'https://yoro.gftd.ai/api/mcp',
		moved: `https://atproto.gftd.ai${pathname}`
	}, {
		status: 410,
		headers: { link: '<https://atproto.gftd.ai>; rel="canonical"' }
	});
}
