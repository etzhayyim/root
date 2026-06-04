/**
 * activity-feed.svelte.ts — Agent activity feed as chat-style timeline.
 *
 * Fetches recent evolution task results (shinka/koji/kyumei/hinshitsu/shinkaKnowledge)
 * from PDS and displays them as chat bubbles. Polls for new activity every 30s.
 *
 * @module
 */

const PDS = 'https://atproto.etzhayyim.com';

/** A single activity entry rendered as a chat bubble. */
export interface ActivityEntry {
	id: string;
	actorDid: string;
	actorName: string;
	actorAvatar: string;
	type: string;
	summary: string;
	detail: string;
	timestamp: string;
}

// ── Svelte 5 reactive state ──

let _entries = $state<ActivityEntry[]>([]);
let _loading = $state(false);
let _error = $state<string | null>(null);
let _pollTimer: ReturnType<typeof setTimeout> | null = null;

/** Load recent activity from PDS evolution records. */
async function loadActivity(): Promise<void> {
	_loading = true;
	_error = null;

	try {
		const collections = [
			'com.etzhayyim.apps.yoro.shinkaKnowledge',
			'com.etzhayyim.apps.yoro.shinkaEvolution',
			'com.etzhayyim.apps.yoro.kojiDiscovery',
			'com.etzhayyim.apps.yoro.kyumeiValidation',
			'com.etzhayyim.apps.yoro.hinshitsuAssessment',
		];

		const entries: ActivityEntry[] = [];

		for (const collection of collections) {
			try {
				const res = await fetch(`${PDS}/xrpc/com.atproto.repo.listRecords`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({ collection, limit: 10 }),
				});
				if (!res.ok) continue;
				const data = await res.json();
				for (const rec of data?.records ?? []) {
					const val = rec.value ?? rec.record ?? {};
					const type = collection.split('.').pop() ?? 'unknown';
					const actorName = String(val.actorName || val.actorDid || 'Actor');
					const actorDid = String(val.actorDid || rec.uri?.split('/')[2] || '');

					let summary = '';
					let detail = '';
					if (type === 'shinkaKnowledge') {
						summary = `Generated domain knowledge: ${(val.subDids?.length ?? 0)} sub-DIDs, ${(val.knowledgeEdges?.length ?? 0)} edges`;
						detail = String(val.domainSummary || '');
					} else if (type === 'shinkaEvolution') {
						summary = `Joucho: ${val.mood || 'neutral'} (joy:${val.joucho?.joy ?? 0} calm:${val.joucho?.calm ?? 0})`;
						detail = String(val.suggestion || '');
					} else if (type === 'kojiDiscovery') {
						summary = `Discovered ${(val.capabilities?.length ?? 0)} capabilities, grade ${val.readinessGrade || '?'}`;
						detail = String(val.summary || '');
					} else if (type === 'kyumeiValidation') {
						summary = `Validation score: ${val.validationScore ?? 0}/100, ${(val.inconsistencies?.length ?? 0)} issues`;
						detail = val.repairs?.join(', ') || '';
					} else if (type === 'hinshitsuAssessment') {
						summary = `Quality: ${val.grade || '?'} (${val.qualityScore ?? 0}/100)`;
						detail = val.improvements?.join(', ') || '';
					}

					entries.push({
						id: rec.uri || `${type}-${Date.now()}-${Math.random()}`,
						actorDid,
						actorName,
						actorAvatar: `https://api.dicebear.com/9.x/identicon/svg?seed=${encodeURIComponent(actorName)}`,
						type,
						summary,
						detail,
						timestamp: String(val.createdAt || new Date().toISOString()),
					});
				}
			} catch {
				// skip failed collection
			}
		}

		// Sort by timestamp descending
		entries.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
		_entries = entries.slice(0, 50);
	} catch (err) {
		_error = (err as Error).message;
	} finally {
		_loading = false;
	}
}

/** Start polling for activity. */
function startPolling(): void {
	stopPolling();
	void loadActivity();
	_pollTimer = setInterval(() => void loadActivity(), 30_000);
}

/** Stop polling. */
function stopPolling(): void {
	if (_pollTimer) {
		clearInterval(_pollTimer);
		_pollTimer = null;
	}
}

/** Svelte 5 reactive store. */
export function useActivityFeed() {
	return {
		get entries() { return _entries; },
		get loading() { return _loading; },
		get error() { return _error; },
		startPolling,
		stopPolling,
		refresh: loadActivity,
	};
}
