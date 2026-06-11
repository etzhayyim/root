import type { RequestHandler } from './$types';
import { actorSitemapIndexXml, sitemapResponse } from '$lib/server/sitemap';

export const GET: RequestHandler = async () => sitemapResponse(actorSitemapIndexXml(), 86400);
