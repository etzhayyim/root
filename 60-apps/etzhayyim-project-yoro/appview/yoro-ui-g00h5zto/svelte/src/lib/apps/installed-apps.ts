import { writable, get } from 'svelte/store';
import { clerkUser, currentOrg } from '../auth/stores.js';
import { getSessionToken } from '../auth/passkey.js';
import type { GfAppLink } from './types.js';
import { findAppById, resolveAppHref } from './apps.js';

const APPSTORE_ENDPOINT = 'https://apps.etzhayyim.com/xrpc';

/** OAuth scope that apps can request. */
export interface AppScope {
	id: string;
	label: string;
	description: string;
}

/** Well-known scopes apps can request. */
export const KNOWN_SCOPES: AppScope[] = [
	{ id: 'profile:read', label: 'Profile', description: 'View your name, email, and avatar' },
	{ id: 'threads:read', label: 'Read Matrix', description: 'Access your Matrix rooms and conversation history' },
	{ id: 'threads:write', label: 'Write Matrix', description: 'Send Matrix messages on your behalf' },
	{ id: 'cases:read', label: 'Read Cases', description: 'View your case data' },
	{ id: 'cases:write', label: 'Write Cases', description: 'Create and modify cases' },
	{ id: 'documents:read', label: 'Read Documents', description: 'Access your documents' },
	{ id: 'documents:write', label: 'Write Documents', description: 'Create and modify documents' },
	{ id: 'calendar:read', label: 'Read Calendar', description: 'View your schedule' },
	{ id: 'calendar:write', label: 'Write Calendar', description: 'Create and modify events' },
	{ id: 'contacts:read', label: 'Read Contacts', description: 'View your contacts' },
	{ id: 'billing:read', label: 'View Billing', description: 'View your credits and usage' },
];

export function scopeLabel(scopeId: string): string {
	return KNOWN_SCOPES.find((s) => s.id === scopeId)?.label ?? scopeId;
}

export function scopeDescription(scopeId: string): string {
	return KNOWN_SCOPES.find((s) => s.id === scopeId)?.description ?? scopeId;
}

/** Installation record from appstore backend. */
export interface InstalledApp {
	'installationId': string;
	'appId': string;
	'appName': string;
	'appIcon': string;
	'appHref': string;
	version: string;
	'grantedScopes': string[];
	'installedAt': number;
}

/** Store of user's installed apps. */
export const installedApps = writable<InstalledApp[]>([]);

/** Loading state. */
export const installedAppsLoading = writable(false);

async function authHeaders(): Promise<Record<string, string>> {
	const h: Record<string, string> = {
		'Content-Type': 'application/json',
		'Connect-Protocol-Version': '1'
	};
	const token = await getSessionToken();
	if (token) h.Authorization = `Bearer ${token}`;
	const user = get(clerkUser);
	if (user?.id) h['X-etzhayyim-USER-ID'] = user.id;
	const org = get(currentOrg);
	if (org?.id) h['X-etzhayyim-ORG-ID'] = org.id;
	return h;
}

/** Fetch installed apps from appstore backend. */
export async function fetchInstalledApps(): Promise<InstalledApp[]> {
	installedAppsLoading.set(true);
	try {
		const headers = await authHeaders();
		const res = await fetch(`${APPSTORE_ENDPOINT}/etzhayyim.appstore.v1.DistributionService/ListInstalled`, {
			method: 'POST',
			headers,
			body: JSON.stringify({ limit: 100 })
		});
		if (!res.ok) return [];
		const data = await res.json();
		const items: InstalledApp[] = (data.installations ?? [])
			.filter((i: Record<string, unknown>) => i && !i.uninstalledAt)
			.map((i: Record<string, unknown>) => ({
				'installationId': String(i.installationId ?? ''),
				'appId': String(i.appId ?? ''),
				'appName': String(i.appName ?? i.appId ?? ''),
				'appIcon': String(i.appIcon ?? ''),
				'appHref': String(i.appHref ?? ''),
				version: String(i.version ?? ''),
				'grantedScopes': parseScopes(i.grantedScopes),
				'installedAt': Number(i.installedAt ?? 0)
			}));
		installedApps.set(items);
		return items;
	} catch {
		return [];
	} finally {
		installedAppsLoading.set(false);
	}
}

/** Install an app with granted scopes. */
export async function installApp(
	appId: string,
	appName: string,
	appIcon: string,
	appHref: string,
	grantedScopes: string[]
): Promise<{ ok: boolean; installationId?: string }> {
	try {
		const headers = await authHeaders();
		const res = await fetch(`${APPSTORE_ENDPOINT}/etzhayyim.appstore.v1.DistributionService/Install`, {
			method: 'POST',
			headers,
			body: JSON.stringify({
				'appId': appId,
				'appName': appName,
				'appIcon': appIcon,
				'appHref': appHref,
				'grantedScopes': JSON.stringify(grantedScopes)
			})
		});
		if (!res.ok) return { ok: false };
		const data = await res.json();
		// Refresh installed list
		await fetchInstalledApps();
		return { ok: true, 'installationId': data.installationId };
	} catch {
		return { ok: false };
	}
}

/** Uninstall an app. */
export async function uninstallApp(installationId: string): Promise<boolean> {
	try {
		const headers = await authHeaders();
		const res = await fetch(`${APPSTORE_ENDPOINT}/etzhayyim.appstore.v1.DistributionService/Uninstall`, {
			method: 'POST',
			headers,
			body: JSON.stringify({ 'installationId': installationId })
		});
		if (!res.ok) return false;
		await fetchInstalledApps();
		return true;
	} catch {
		return false;
	}
}

/** Convert installed apps to GfAppLink format for AppLauncher. */
export function installedToAppLinks(installed: InstalledApp[]): GfAppLink[] {
	return installed.map((i) => {
		const knownApp = findAppById(i.appId);
		return {
			id: i.installationId,
			name: i.appName,
			shortName: i.appName,
			href: resolveAppHref(i.appId, i.appHref || undefined),
			icon: i.appIcon || knownApp?.icon || i.appName[0] || '?',
			category: (knownApp?.category ?? 'Services'),
			description: `v${i.version}`
		};
	});
}

function parseScopes(v: unknown): string[] {
	if (Array.isArray(v)) return v.map(String);
	if (typeof v === 'string') {
		try {
			const parsed = JSON.parse(v);
			if (Array.isArray(parsed)) return parsed.map(String);
		} catch { /* ignore */ }
	}
	return [];
}
