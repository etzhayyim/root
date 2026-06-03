import type { RequestHandler } from './$types';
import { publicJson } from '$lib/server/bff';
import { agentSkillsIndex } from '$lib/server/discovery';

export const GET: RequestHandler = async () => publicJson(agentSkillsIndex());
