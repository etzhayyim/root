import type { RequestHandler } from './$types';
import { envOf, publicJson } from '$lib/server/bff';
import { a2aAgentCard } from '$lib/server/discovery';

export const GET: RequestHandler = async (event) => publicJson(a2aAgentCard(envOf(event)));
