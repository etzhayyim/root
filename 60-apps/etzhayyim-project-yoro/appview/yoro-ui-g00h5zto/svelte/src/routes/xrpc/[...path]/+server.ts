import type { RequestHandler } from './$types';
import { noStoreJson } from '$lib/server/bff';

export const GET: RequestHandler = async ({ url }) => gone(url.pathname);
export const POST: RequestHandler = async ({ url }) => gone(url.pathname);
export const PUT: RequestHandler = async ({ url }) => gone(url.pathname);
export const DELETE: RequestHandler = async ({ url }) => gone(url.pathname);

function gone(pathname: string): Response {
	return noStoreJson({
		error: 'Gone',
		message: 'yoro.etzhayyim.com no longer serves XRPC. Use /api/mcp for MCP BFF calls or atproto.etzhayyim.com/xrpc/* for AT Protocol.',
		mcpBff: 'https://yoro.etzhayyim.com/api/mcp',
		moved: `https://atproto.etzhayyim.com${pathname}`
	}, {
		status: 410,
		headers: { link: '<https://atproto.etzhayyim.com>; rel="canonical"' }
	});
}
