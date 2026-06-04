import type { RequestHandler } from './$types';
import { markdown } from '$lib/server/bff';
import { yoroAgentSkillMarkdown } from '$lib/server/discovery';

export const GET: RequestHandler = async () => markdown(yoroAgentSkillMarkdown());
