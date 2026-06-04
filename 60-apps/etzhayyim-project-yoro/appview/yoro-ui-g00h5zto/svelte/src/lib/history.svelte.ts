/**
 * Browsing history store — tracks profile/post/search views in SQL graph.
 * Write: ComAtprotoRepoCreateRecord (browsingHistory kind) → PDS → kagami.
 * Read: repo record scan on com.etzhayyim.apps.yoro.browsingHistory.
 */
import { browser } from '$app/environment';
import { atProcedure, getCurrentDID, listRecords } from '$lib/atproto-agent';
import { getSessionToken } from '$lib/auth';

/**
 * A single browsing history entry.
 * `ipDid` is injected server-side by the PDS Worker (CF-Connecting-IP → ipaddress.etzhayyim.com DID).
 */
export interface HistoryEntry {
	/** Unique path (e.g. /profile/did:web:abc.etzhayyim.com) */
	path: string;
	/** Display title */
	title: string;
	/** Entry type */
	type: 'profile' | 'post' | 'search';
	/** Avatar URL if available */
	avatar?: string;
	/** Handle or author handle */
	handle?: string;
	/** ISO timestamp of visit */
	visitedAt: string;
	/** Record key (for deletion) */
	rkey?: string;
}

const DEDUP_WINDOW_MS = 60 * 60 * 1000;

/** Reactive history entries, newest first. */
let _entries = $state<HistoryEntry[]>([]);
let _loaded = $state(false);
let _loading = $state(false);

/** Last recorded paths with timestamps for client-side dedup. */
const _recentPaths = new Map<string, number>();

/**
 * Record a page visit. Writes a browsingHistory record to PDS graph.
 * Deduplicates same path within 1 hour window (client-side gate).
 */
export function recordVisit(entry: Omit<HistoryEntry, 'visitedAt' | 'rkey'>) {
	if (!browser) return;
	const now = Date.now();
	const lastVisit = _recentPaths.get(entry.path);
	if (lastVisit && now - lastVisit < DEDUP_WINDOW_MS) return;
	_recentPaths.set(entry.path, now);

	const visitedAt = new Date(now).toISOString();

	// Optimistic UI update
	const newEntry: HistoryEntry = { ...entry, visitedAt };
	_entries = [newEntry, ..._entries.filter((e) => e.path !== entry.path)].slice(0, 200);

	// Fire-and-forget write to PDS (authenticated sessions only).
	void (async () => {
		const token = await getSessionToken().catch((_err: unknown) => null);
		if (!token) return;
		await atProcedure('com.atproto.repo.createRecord', {
			collection: 'com.etzhayyim.apps.yoro.browsingHistory',
			record: {
				$type: 'com.etzhayyim.apps.yoro.browsingHistory',
				path: entry.path,
				title: entry.title,
				historyType: entry.type,
				avatar: entry.avatar || '',
				handle: entry.handle || '',
				createdAt: visitedAt,
			},
		});
	})().catch((e) => console.warn('history: write failed', e));
}

/**
 * Record a search query to PDS graph.
 * Collection: `com.etzhayyim.apps.yoro.searchHistory`.
 * `ipDid` is injected server-side by the PDS Worker from CF-Connecting-IP.
 *
 * @param query - Raw search string entered by the user.
 * @param tab - Active search tab ('actors' | 'posts' | 'people').
 * @param resultCount - Number of results returned (optional).
 */
export function recordSearch(query: string, tab: string, resultCount: number = 0) {
	if (!browser || !query.trim()) return;
	const createdAt = new Date().toISOString();
	void (async () => {
		const token = await getSessionToken().catch((_err) => null);
		if (!token) return;
		await atProcedure('com.atproto.repo.createRecord', {
			collection: 'com.etzhayyim.apps.yoro.searchHistory',
			record: {
				$type: 'com.etzhayyim.apps.yoro.searchHistory',
				query: query.trim(),
				tab,
				resultCount,
				createdAt,
			},
		});
	})().catch((e) => console.warn('history: search record failed', e));
}

/**
 * Load history from SQL graph. Call once on page mount.
 */
export async function loadHistory(): Promise<HistoryEntry[]> {
	if (_loading) return _entries;
	_loading = true;
	try {
		const token = await getSessionToken().catch((_err: unknown) => null);
		if (!token) { _loaded = true; _entries = []; _loading = false; return []; }
		const did = getCurrentDID();
		if (!did) { _loading = false; return []; }
		const result = await listRecords(did, 'com.etzhayyim.apps.yoro.browsingHistory', { limit: 200 });
		const records = ((result as { records?: Array<Record<string, unknown>> })?.records ?? []);
		_entries = records.map((record) => {
			const value = (record.value ?? record) as Record<string, unknown>;
			const uri = typeof record.uri === 'string' ? record.uri : '';
			return {
				path: String(value.path ?? ''),
				title: String(value.title ?? ''),
				type: (String(value.historyType ?? 'post')) as HistoryEntry['type'],
				avatar: value.avatar ? String(value.avatar) : undefined,
				handle: value.handle ? String(value.handle) : undefined,
				visitedAt: String(value.createdAt ?? ''),
				rkey: uri ? uri.split('/').pop() : (record.rkey ? String(record.rkey) : undefined),
			};
		}).sort((a, b) => Date.parse(b.visitedAt || '') - Date.parse(a.visitedAt || ''));
		_loaded = true;
	} catch (e) {
		console.warn('history: load failed', e);
	} finally {
		_loading = false;
	}
	return _entries;
}

/** Get all history entries (reactive). */
export function getHistory(): HistoryEntry[] {
	return _entries;
}

/** Whether initial load is complete. */
export function isHistoryLoaded(): boolean {
	return _loaded;
}

/** Whether currently loading. */
export function isHistoryLoading(): boolean {
	return _loading;
}

/** Remove a single entry by rkey (delete record from PDS). */
export function removeEntry(path: string) {
	const entry = _entries.find((e) => e.path === path);
	_entries = _entries.filter((e) => e.path !== path);
	if (entry?.rkey) {
		void (async () => {
			const token = await getSessionToken().catch((_err) => null);
			if (!token) return;
			await atProcedure('com.atproto.repo.deleteRecord', {
				collection: 'com.etzhayyim.apps.yoro.browsingHistory',
				rkey: entry.rkey,
			});
		})().catch((e) => console.warn('history: delete failed', e));
	}
}

/** Clear all browsing history records. */
export function clearHistory() {
	const toDelete = _entries.filter((e) => e.rkey);
	_entries = [];
	_recentPaths.clear();
	// Delete each record
	void (async () => {
		const token = await getSessionToken().catch((_err) => null);
		if (!token) return;
		for (const entry of toDelete) {
			await atProcedure('com.atproto.repo.deleteRecord', {
				collection: 'com.etzhayyim.apps.yoro.browsingHistory',
				rkey: entry.rkey!,
			});
		}
	})().catch((e) => console.warn('history: delete failed', e));
}
