import type { RequestHandler } from './$types';
import { authorizeBearer, corsHeaders, envOf, noStoreJson, proxyPrefix } from '$lib/server/bff';

export const OPTIONS: RequestHandler = async ({ request }) => new Response(null, { status: 204, headers: corsHeaders(request.headers.get('origin')) });

export const GET: RequestHandler = async (event) => handle(event);
export const POST: RequestHandler = async (event) => handle(event);

async function handle(event: Parameters<RequestHandler>[0]): Promise<Response> {
	const env = envOf(event);
	const unauthorized = authorizeBearer(event, env.HITL_API_KEY);
	if (unauthorized) return unauthorized;
	const baseUrl = env.TERMINAL_AGENT_URL?.trim();
	if (!baseUrl) return noStoreJson({ error: 'TERMINAL_AGENT_URL not configured' }, { status: 503 });
	return proxyPrefix(event, '/api/hitl', baseUrl, env.TERMINAL_AGENT_API_KEY);
}
