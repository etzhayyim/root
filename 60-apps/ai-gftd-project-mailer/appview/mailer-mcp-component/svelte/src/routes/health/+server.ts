import type { RequestHandler } from './$types';
import { metaResponse } from '$lib/server/mailer-proxy';

export const GET: RequestHandler = ({ platform }) => metaResponse(platform);
