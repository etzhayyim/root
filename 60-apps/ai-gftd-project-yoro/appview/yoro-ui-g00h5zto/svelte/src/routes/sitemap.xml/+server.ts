import type { RequestHandler } from './$types';
import { sitemapIndexXml, sitemapResponse } from '$lib/server/sitemap';

export const GET: RequestHandler = async () => sitemapResponse(sitemapIndexXml(), 3600);
