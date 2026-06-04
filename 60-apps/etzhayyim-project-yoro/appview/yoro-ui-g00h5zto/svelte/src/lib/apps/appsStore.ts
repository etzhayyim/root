import { writable } from 'svelte/store';
import { apps as staticApps, normalizeAppId, findAppById, resolveAppHref } from './apps.js';
import type { GfAppLink } from './types.js';

// Starts with static apps for instant first-paint; replaced by DB data on load.
export const appsStore = writable<GfAppLink[]>(staticApps);

let _loaded = false;

export async function loadAppsFromRegistry(): Promise<void> {
	if (_loaded) return;
	_loaded = true;
	try {
		const { atProcedure } = await import('$lib/atproto-agent');
		const result = await atProcedure<{ items?: GfAppLink[]; total?: number }>(
			'com.etzhayyim.apps.yoro.listApps',
			{}
		);
		if (result?.items && result.items.length > 0) {
			appsStore.set(result.items);
		}
	} catch {
		// static fallback stays in place
	}
}

export { normalizeAppId, findAppById, resolveAppHref };
