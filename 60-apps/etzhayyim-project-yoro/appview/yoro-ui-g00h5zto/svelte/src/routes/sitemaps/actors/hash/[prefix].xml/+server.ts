import type { RequestHandler } from './$types';
import { actorSitemapIndexXml, renderUrlSetXml, sitemapResponse } from '$lib/server/sitemap';

const ACTOR_HASH_PREFIX_RE = /^[0-9a-f]{2}(?:[0-9a-f]{2})?$/;

export const GET: RequestHandler = async ({ params }) => {
	const prefix = params.prefix.toLowerCase();
	if (!ACTOR_HASH_PREFIX_RE.test(prefix)) {
		return new Response('Not Found', { status: 404 });
	}
	if (prefix.length === 2) return sitemapResponse(actorSitemapIndexXml(prefix), 86400);
	return sitemapResponse(renderUrlSetXml([]), 21600);
};
