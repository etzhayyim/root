import type { RequestHandler } from './$types';
import { envOf, publicJson } from '$lib/server/bff';
import { apiCatalog } from '$lib/server/discovery';

export const GET: RequestHandler = async (event) => publicJson(apiCatalog(envOf(event)), {
	headers: { 'content-type': 'application/linkset+json; charset=utf-8' }
});
