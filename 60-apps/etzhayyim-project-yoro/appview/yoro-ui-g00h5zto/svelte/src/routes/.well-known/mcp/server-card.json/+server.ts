import type { RequestHandler } from './$types';
import { envOf, publicJson } from '$lib/server/bff';
import { mcpServerCard } from '$lib/server/discovery';

export const GET: RequestHandler = async (event) => publicJson(mcpServerCard(envOf(event)));
