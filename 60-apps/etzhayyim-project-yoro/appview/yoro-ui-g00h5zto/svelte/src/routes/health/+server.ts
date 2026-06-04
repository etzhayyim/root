import type { RequestHandler } from './$types';
import { noStoreJson, nowISO } from '$lib/server/bff';

export const GET: RequestHandler = async () => noStoreJson({ ok: true, app: 'yoro', runtime: 'sveltekit-bff', ts: nowISO() });
