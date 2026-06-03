import type { Handle } from '@sveltejs/kit';

const BASE_SECURITY_HEADERS: Record<string, string> = {
	'referrer-policy': 'strict-origin-when-cross-origin',
	'x-content-type-options': 'nosniff',
	'x-frame-options': 'DENY',
	'permissions-policy': 'camera=(), microphone=(), geolocation=()',
	'strict-transport-security': 'max-age=31536000'
};

const HTML_SECURITY_HEADERS: Record<string, string> = {
	'content-security-policy': "base-uri 'self'; frame-ancestors 'none'; object-src 'none'"
};

const DISCOVERY_LINK_HEADER = [
	'<https://yoro.etzhayyim.com/sitemap.xml>; rel="sitemap"; type="application/xml"',
	'<https://yoro.etzhayyim.com/llms.txt>; rel="alternate"; type="text/markdown"',
	'<https://yoro.etzhayyim.com/llms-full.txt>; rel="alternate"; type="text/markdown"',
	'<https://yoro.etzhayyim.com/.well-known/mcp/server-card.json>; rel="service-desc"; type="application/json"',
	'<https://yoro.etzhayyim.com/.well-known/api-catalog>; rel="service-desc"; type="application/linkset+json"'
].join(', ');

export const handle: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);
	const headers = new Headers(response.headers);
	for (const [key, value] of Object.entries(BASE_SECURITY_HEADERS)) headers.set(key, value);

	const contentType = headers.get('content-type') ?? '';
	if (contentType.includes('text/html') || contentType.includes('text/markdown') || contentType.includes('text/plain')) {
		headers.set('link', DISCOVERY_LINK_HEADER);
	}
	if (contentType.includes('text/html')) {
		for (const [key, value] of Object.entries(HTML_SECURITY_HEADERS)) headers.set(key, value);
	}

	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers
	});
};
