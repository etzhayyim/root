import type { RequestHandler } from './$types';
import { markdown } from '$lib/server/bff';
import { llmText } from '$lib/server/discovery';

export const GET: RequestHandler = async () => markdown(llmText('/'));
