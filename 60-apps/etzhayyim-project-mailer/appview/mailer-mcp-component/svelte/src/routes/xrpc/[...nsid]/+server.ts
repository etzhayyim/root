import type { RequestHandler } from './$types';
import { proxyXrpc } from '$lib/server/mailer-proxy';

export const GET: RequestHandler = ({ platform, request, params }) =>
  proxyXrpc(platform, request, params.nsid);

export const POST: RequestHandler = ({ platform, request, params }) =>
  proxyXrpc(platform, request, params.nsid);
