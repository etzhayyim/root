import type { RequestHandler } from './$types';
import { proxyApi } from '$lib/server/mailer-proxy';

export const GET: RequestHandler = ({ platform, url }) =>
  proxyApi(platform, 'app.etzhayyim.apps.mailer.listBindings', url);
