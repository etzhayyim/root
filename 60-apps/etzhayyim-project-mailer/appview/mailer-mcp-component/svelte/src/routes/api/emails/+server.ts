import type { RequestHandler } from './$types';
import { proxyApi } from '$lib/server/mailer-proxy';

export const GET: RequestHandler = ({ platform, url }) =>
  proxyApi(platform, 'com.etzhayyim.apps.mailer.listEmails', url);
