import type { RequestHandler } from './$types';
import { proxyApi } from '$lib/server/mailer-proxy';

export const GET: RequestHandler = ({ platform, url }) =>
  proxyApi(platform, 'ai.etzhayyim.apps.mailer.listBindings', url);
