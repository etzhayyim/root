/**
 * Svelte stores for yatabase Studio session state.
 *
 * - `apiKey` persists to localStorage (`yatabase-studio:apiKey`) so the
 *   user pastes their `sk_live_yata_*` key once.
 * - `identity` / `plan` are derived: refreshed on apiKey change.
 * - `theme` follows the `[data-theme]` attribute on <html>.
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { auth, plan as planApi, type WhoamiResp, type PlanResp } from './api';

const STORAGE_KEY = 'yatabase-studio:apiKey';
const ADMIN_STORAGE_KEY = 'yatabase-studio:adminKey';

const _initial = browser ? localStorage.getItem(STORAGE_KEY) || '' : '';
const _initialAdmin = browser ? localStorage.getItem(ADMIN_STORAGE_KEY) || '' : '';

export const apiKey = writable<string>(_initial);

/** Operator-only `x-yata-admin-key` (separate from sk_live_yata_*).
 * Required for /api/outbox/* + /api/leads/* admin routes. Stays in
 * localStorage to survive reloads but is never sent to a non-admin
 * surface. */
export const adminKey = writable<string>(_initialAdmin);

if (browser) {
	apiKey.subscribe((v) => {
		if (v) localStorage.setItem(STORAGE_KEY, v);
		else localStorage.removeItem(STORAGE_KEY);
	});
	adminKey.subscribe((v) => {
		if (v) localStorage.setItem(ADMIN_STORAGE_KEY, v);
		else localStorage.removeItem(ADMIN_STORAGE_KEY);
	});
}

// Validate-on-set: when a new key is pasted, refresh whoami + plan.
export const identity = writable<WhoamiResp | null>(null);
export const plan = writable<PlanResp | null>(null);
export const sessionError = writable<string>('');
export const sessionLoading = writable<boolean>(false);

export function isAuthed(): boolean {
	return Boolean(get(apiKey)) && Boolean(get(identity));
}

let _lastValidatedKey = '';

export async function refreshSession(): Promise<void> {
	if (!browser) return;
	const k = get(apiKey);
	if (!k) {
		identity.set(null);
		plan.set(null);
		sessionError.set('');
		return;
	}
	if (k === _lastValidatedKey && get(identity)) return; // already valid

	sessionLoading.set(true);
	sessionError.set('');
	try {
		const who = await auth.whoami(k);
		identity.set(who);
		try {
			const p = await planApi.get(k);
			plan.set(p);
		} catch {
			// /api/plan may 404 on brand-new tenants — keep identity but
			// surface the gap to the page.
			plan.set(null);
		}
		_lastValidatedKey = k;
	} catch (e: any) {
		identity.set(null);
		plan.set(null);
		sessionError.set(
			e?.message?.includes('401')
				? 'Invalid API key — paste the sk_live_yata_* you got at signup.'
				: e?.message || 'Unable to validate API key.',
		);
		_lastValidatedKey = '';
	} finally {
		sessionLoading.set(false);
	}
}

export function signOut(): void {
	apiKey.set('');
	identity.set(null);
	plan.set(null);
	sessionError.set('');
	_lastValidatedKey = '';
}

// Convenience derived: ready-to-use display name (tenant or did-tail).
export const tenantLabel = derived(identity, ($i) => {
	if (!$i) return '';
	if ($i.tenantName) return $i.tenantName;
	if ($i.orgDid) {
		const tail = $i.orgDid.split(':').pop() ?? $i.orgDid;
		return tail.length > 12 ? `${tail.slice(0, 12)}…` : tail;
	}
	return '(unknown tenant)';
});

// ─── Theme toggle (data-theme on <html>) ──────────────────────────────────

export const theme = writable<'dark' | 'light'>(
	browser
		? (((document.documentElement.getAttribute('data-theme') as 'dark' | 'light') ||
				'dark') as 'dark' | 'light')
		: 'dark',
);

if (browser) {
	theme.subscribe((t) => {
		document.documentElement.setAttribute('data-theme', t);
	});
}
