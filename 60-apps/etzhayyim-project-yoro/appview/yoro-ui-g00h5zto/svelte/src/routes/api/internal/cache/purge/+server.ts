import type { RequestHandler } from './$types';
import { authorizeBearer, envOf, noStoreJson } from '$lib/server/bff';

const DEFAULT_FILES = ['https://yoro.etzhayyim.com/', 'https://yoro.etzhayyim.com/vibes', 'https://yoro.etzhayyim.com/search'];

export const POST: RequestHandler = async (event) => {
	const env = envOf(event);
	const unauthorized = authorizeBearer(event, env.CACHE_PURGE_API_KEY);
	if (unauthorized) return unauthorized;

	const cfToken = env.CACHE_PURGE_CF_API_TOKEN?.trim();
	const zoneId = env.CACHE_PURGE_CF_ZONE_ID?.trim();
	if (!cfToken || !zoneId) {
		return noStoreJson({ ok: false, error: 'CachePurgeSecretMissing' }, { status: 500 });
	}

	const payload = await event.request.json().catch(() => ({})) as { files?: unknown };
	const files = Array.isArray(payload.files)
		? payload.files.map((v) => String(v ?? '').trim()).filter(Boolean).slice(0, 50)
		: DEFAULT_FILES;
	if (files.length === 0) return noStoreJson({ ok: false, error: 'NoFiles' }, { status: 400 });

	const cfResp = await fetch(`https://api.cloudflare.com/client/v4/zones/${zoneId}/purge_cache`, {
		method: 'POST',
		headers: {
			authorization: `Bearer ${cfToken}`,
			'content-type': 'application/json'
		},
		body: JSON.stringify({ files })
	});
	const body = await cfResp.json().catch(() => null);
	if (!cfResp.ok || (body as { success?: boolean } | null)?.success !== true) {
		return noStoreJson({ ok: false, error: 'CloudflarePurgeFailed', details: body }, { status: 502 });
	}
	return noStoreJson({ ok: true, files, result: body });
};
