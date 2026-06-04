import type { RequestHandler } from './$types';
import { sitemapResponse, staticSitemapXml } from '$lib/server/sitemap';

export const GET: RequestHandler = async () => sitemapResponse(staticSitemapXml(), 86400);
