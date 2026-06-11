/**
 * AT Protocol convo reactive store — Svelte 5 runes.
 * Uses XRPC for data + w-stream (SSE) for real-time events.
 */

import {
	listConvos,
	getConvoMessages,
	getConvo,
	getUnread,
	listPresence,
	decodeMessageBody,
	subscribeAtprotoStream,
} from '$lib/atproto-agent';
import type {
	StreamEvent,
	StreamConnection,
	StreamState,
	SyncSnapshot,
	ConvoSnapshot,
	ConvoEnvelope,
	Convo,
	ConvoEntry,
	ConvoGroup,
	ConvoSection,
	ConvoId,
	UnreadCounts,
	PresenceState,
} from '$lib/atproto-agent';

/** Race a promise against a timeout. Rejects on timeout instead of returning fallback. */
function withTimeout<T>(p: Promise<T>, ms: number, _label = ''): Promise<T> {
	let timer: ReturnType<typeof setTimeout>;
	return Promise.race([
		p,
		new Promise<T>((_, reject) => { timer = setTimeout(() => reject(new Error(`convo timeout (${ms}ms) ${_label}`)), ms); }),
	]).finally(() => clearTimeout(timer!));
}

// ─── Convo list builder ─────────────────────────────────────────────────────

function lastEnvelopePreview(envelopes: ConvoEnvelope[]): string {
	for (let i = envelopes.length - 1; i >= 0; i--) {
		const e = envelopes[i];
		if (e.kind !== 'message') continue;
		const body = decodeMessageBody(e).trim();
		if (body) return body.length > 60 ? body.slice(0, 60) + '...' : body;
	}
	return '';
}

function lastEnvelopeTimestamp(envelopes: ConvoEnvelope[]): string {
	for (let i = envelopes.length - 1; i >= 0; i--) {
		if (envelopes[i].createdAt) return envelopes[i].createdAt;
	}
	return '';
}

function buildConvoEntry(
	convo: Convo,
	snap: ConvoSnapshot,
	directConvoIds: Set<ConvoId>,
): ConvoEntry {
	return {
		convoId: convo.convoId,
		name: convo.name || convo.convoId,
		description: convo.description || '',
		isDirect: directConvoIds.has(convo.convoId) || convo.kind === 'direct' || convo.kind === 'group-dm' || convo.kind === 'email',
		isSpace: false,
		isFavorite: false,
		isMuted: false,
		isEncrypted: convo.encryptionMode !== 'plaintext',
		unreadCount: snap.unread.notificationCount,
		highlightCount: snap.unread.highlightCount,
		lastRecordTimestamp: lastEnvelopeTimestamp(snap.envelopes),
		lastRecordPreview: lastEnvelopePreview(snap.envelopes),
		avatarUrl: undefined,
		kind: convo.kind,
	};
}

function buildConvoList(
	snapshot: SyncSnapshot | null,
	collapsedSections: Set<ConvoSection>,
): ConvoGroup[] {
	if (!snapshot) return [];

	const directSet = new Set(snapshot.directConvoIds);
	const directs: ConvoEntry[] = [];
	const convos: ConvoEntry[] = [];

	for (const [convoId, snap] of Object.entries(snapshot.convos)) {
		const ch = snap.convo;
		const convo: Convo = {
			convoId: convoId,
			orgId: '',
			name: ch.name ?? convoId,
			description: ch.description ?? '',
			kind: directSet.has(convoId) ? 'direct' : 'public',
			encryptionMode: ch.encryptionEnabled ? 'signal-group' : 'plaintext',
			creatorDid: '',
			memberCount: ch.joinedMemberCount ?? 0,
			atUri: '',
			createdAt: '',
		};
		const entry = buildConvoEntry(convo, snap, directSet);

		if (entry.isDirect) {
			directs.push(entry);
		} else {
			convos.push(entry);
		}
	}

	directs.sort((a, b) => {
		if (!a.lastRecordTimestamp && !b.lastRecordTimestamp) return 0;
		if (!a.lastRecordTimestamp) return 1;
		if (!b.lastRecordTimestamp) return -1;
		return b.lastRecordTimestamp.localeCompare(a.lastRecordTimestamp);
	});
	convos.sort((a, b) => a.name.localeCompare(b.name));

	// System convo: Agent Activity (pinned at top)
	const agentActivityEntry: ConvoEntry = {
		convoId: 'agent-activity' as ConvoId,
		name: 'Agent Activity',
		description: 'Actor evolution, shinka, knowledge graph',
		isDirect: false,
		isSpace: false,
		isFavorite: false,
		isMuted: false,
		isEncrypted: false,
		unreadCount: 0,
		highlightCount: 0,
		lastRecordTimestamp: new Date().toISOString(),
		lastRecordPreview: 'Actor evolution, shinka, knowledge graph',
	};

	const groups: ConvoGroup[] = [];
	groups.push({ section: 'convos', label: 'System', convos: [agentActivityEntry], collapsed: false });
	if (directs.length > 0)
		groups.push({ section: 'directs', label: 'Direct Messages', convos: directs, collapsed: collapsedSections.has('directs') });
	if (convos.length > 0)
		groups.push({ section: 'convos', label: 'Conversations', convos: convos, collapsed: collapsedSections.has('convos') });

	return groups;
}

// ─── Module-level reactive state (Svelte 5 runes) ────────────────────────────

let _snapshot = $state<SyncSnapshot | null>(null);
let _activeConvoId = $state<ConvoId>('');
let _collapsedSections = $state<Set<ConvoSection>>(new Set());
let _presenceMap = $state<Map<string, PresenceState>>(new Map());
let _streamState = $state<StreamState>('closed');
let _unsubscribe: (() => void) | null = null;
let _reload: (() => Promise<void>) | null = null;

const _activeConvo = $derived(
	_snapshot && _activeConvoId ? _snapshot.convos[_activeConvoId] : undefined,
);
const _activeConvoEnvelopes = $derived(
	(_activeConvo?.envelopes ?? [])
		.filter((e) => e.kind === 'message')
		.sort((a, b) => (a.createdAt || '').localeCompare(b.createdAt || '')),
);
const _activeConvoUnread = $derived<UnreadCounts>(
	_activeConvo?.unread ?? { 'notificationCount': 0, 'highlightCount': 0 },
);
const _syncStatus = $derived(_snapshot?.status ?? 'idle');
const _syncError = $derived(_snapshot?.error ?? '');
const _hasSynced = $derived(
	Boolean(_snapshot?.syncedAt) || _syncStatus === 'live' || _syncStatus === 'error',
);
const _isSyncing = $derived(
	(_syncStatus === 'idle' || _syncStatus === 'syncing') && !_syncError,
);
const _typingUsers = $derived<string[]>([]);
const _convoList = $derived(buildConvoList(_snapshot, _collapsedSections));

// ─── Stream event handler ─────────────────────────────────────────────────────

function handleStreamEvent(event: StreamEvent) {
	if (!_snapshot) return;

	const convoId = (event as any).convoId;
	const { action, envelope } = event;

	if (action === 'create' && convoId && envelope) {
		const convoSnap = _snapshot.convos[convoId];
		if (!convoSnap) return;

		if (convoId === _activeConvoId) {
			_snapshot = {
				..._snapshot,
				convos: {
					..._snapshot.convos,
					[convoId]: {
						...convoSnap,
						envelopes: [...convoSnap.envelopes, envelope],
					},
				},
			};
		}

		if (convoId !== _activeConvoId) {
			_snapshot = {
				..._snapshot,
				convos: {
					..._snapshot.convos,
					[convoId]: {
						...convoSnap,
						unread: {
							'notificationCount': convoSnap.unread.notificationCount + 1,
							'highlightCount': convoSnap.unread.highlightCount,
						},
					},
				},
			};
		}
	}

	if (action === 'edit' && convoId && envelope) {
		const convoSnap = _snapshot.convos[convoId];
		if (!convoSnap) return;
		_snapshot = {
			..._snapshot,
			convos: {
				..._snapshot.convos,
				[convoId]: {
					...convoSnap,
					envelopes: convoSnap.envelopes.map(e =>
						e.rkey === envelope.rkey ? envelope : e,
					),
				},
			},
		};
	}

	if (action === 'redact' && convoId && event.targetRkey) {
		const convoSnap = _snapshot.convos[convoId];
		if (!convoSnap) return;
		_snapshot = {
			..._snapshot,
			convos: {
				..._snapshot.convos,
				[convoId]: {
					...convoSnap,
					envelopes: convoSnap.envelopes.filter(e => e.rkey !== event.targetRkey),
				},
			},
		};
	}
}

// ─── Public store object ──────────────────────────────────────────────────────

export const convos = {
	get activeConvoId(): ConvoId { return _activeConvoId; },
	setActiveConvo(convoId: ConvoId): void {
		_activeConvoId = convoId;
		if (_reload) void _reload();
	},

	get snapshot(): SyncSnapshot | null { return _snapshot; },
	get activeConvo(): ConvoSnapshot | undefined { return _activeConvo; },
	get convoList(): ConvoGroup[] { return _convoList; },
	get typingUsers(): string[] { return _typingUsers; },
	get activeConvoEnvelopes(): ConvoEnvelope[] { return _activeConvoEnvelopes; },
	get activeConvoUnread(): UnreadCounts { return _activeConvoUnread; },
	get syncStatus(): SyncSnapshot['status'] { return _syncStatus; },
	get syncError(): string { return _syncError; },
	get hasSynced(): boolean { return _hasSynced; },
	get isSyncing(): boolean { return _isSyncing; },
	get streamState(): StreamState { return _streamState; },
	get presenceMap(): Map<string, PresenceState> { return _presenceMap; },

	getPresence(did: string): PresenceState | undefined {
		return _presenceMap.get(did);
	},

	toggleSection(section: ConvoSection): void {
		const next = new Set(_collapsedSections);
		if (next.has(section)) { next.delete(section); } else { next.add(section); }
		_collapsedSections = next;
	},

	subscribe(): void {
		if (_unsubscribe) return;

		_snapshot = { convos: {}, directConvoIds: [], status: 'syncing' };
		let cancelled = false;
		let stream: StreamConnection | null = null;
		let pollTimer: ReturnType<typeof setInterval> | null = null;

		const reload = async () => {
			if (cancelled) return;
			try {
				// Parallel fetch with timeouts (Bluesky pattern: never block on a single call)
				const [convosResult, unreadResult] = await Promise.allSettled([
					withTimeout(listConvos(), 8000, 'listConvos'),
					withTimeout(getUnread(), 8000, 'getUnread'),
				]);

				const userConvos = convosResult.status === 'fulfilled' ? convosResult.value : [];
				const unreadPairs = unreadResult.status === 'fulfilled' ? unreadResult.value : [];
				if (convosResult.status === 'rejected') console.warn('listConvos failed', convosResult.reason);
				if (unreadResult.status === 'rejected') console.warn('getUnread failed', unreadResult.reason);

				const unreadMap = new Map(unreadPairs);

				const prev = _snapshot?.convos ?? {};
				const convoMap: Record<ConvoId, ConvoSnapshot> = {};
				const directIds: ConvoId[] = [];

				for (const ch of userConvos) {
					const unread = unreadMap.get(ch.convoId) ?? 0;
					if (ch.kind === 'direct' || ch.kind === 'group-dm') {
						directIds.push(ch.convoId);
					}
					convoMap[ch.convoId] = {
						convo: {
							id: ch.convoId,
							name: ch.name,
							description: ch.description,
							encryptionEnabled: ch.encryptionMode !== 'plaintext',
							joinedMemberCount: ch.memberCount,
						},
						envelopes: prev[ch.convoId]?.envelopes ?? [],
						unread: {
							'notificationCount': unread,
							'highlightCount': 0,
						},
					};
				}

				// Fetch envelopes for active convo
				if (_activeConvoId) {
					// If active convo not in listConvos result, create a stub via getConvo
					if (!convoMap[_activeConvoId]) {
						try {
							const meta = await withTimeout(getConvo(_activeConvoId), 5000, 'getConvo');
							if (meta) {
								convoMap[_activeConvoId] = {
									convo: {
										id: _activeConvoId,
										name: meta.name ?? _activeConvoId,
										description: meta.description ?? '',
										encryptionEnabled: meta.encryptionMode !== 'plaintext',
										joinedMemberCount: meta.memberCount ?? 0,
									},
									envelopes: prev[_activeConvoId]?.envelopes ?? [],
									unread: { 'notificationCount': 0, 'highlightCount': 0 },
								};
								if (meta.kind === 'direct' || meta.kind === 'group-dm') {
									directIds.push(_activeConvoId);
								}
							}
						} catch (e) {
							console.warn('getConvo fallback failed', e);
						}
					}

					if (convoMap[_activeConvoId]) {
						try {
							const envelopes = await withTimeout(getConvoMessages(_activeConvoId, { limit: 50 }), 8000, 'getConvoMessages');
							if (envelopes) {
								convoMap[_activeConvoId] = {
									...convoMap[_activeConvoId],
									envelopes,
								};
							}
						} catch (e) {
							console.warn('getConvoMessages failed', e);
						}
					}
				}

				if (!cancelled) {
					_snapshot = {
						convos: convoMap,
						directConvoIds: directIds,
						status: 'live',
						syncedAt: new Date().toISOString(),
					};

					// Fetch presence for DM peers (non-blocking)
					const dmPeers = userConvos
						.filter((c) => c.kind === 'direct' && c.creatorDid)
						.map((c) => c.creatorDid)
						.filter(Boolean);
					if (dmPeers.length > 0) {
						withTimeout(listPresence(dmPeers), 5000, 'listPresence').then((presences) => {
							if (cancelled || !presences.length) return;
							const newMap = new Map(_presenceMap);
							for (const p of presences) {
								newMap.set(p.did, p);
							}
							_presenceMap = newMap;
						}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/w/convo-store.svelte.ts: suppressed async error", error); });
					}
				}
			} catch (err) {
				if (!cancelled) {
					_snapshot = { ..._snapshot!, status: 'error', error: String(err) };
				}
			}
		};

		_reload = reload;

		void reload().then(() => {
			if (cancelled) return;

			try {
				stream = subscribeAtprotoStream(handleStreamEvent, {
					onStateChange(state) {
						if (state === 'streaming') {
							_streamState = 'streaming';
							if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
						} else if (state === 'polling' || state === 'closed') {
							_streamState = state === 'closed' ? 'closed' : 'polling';
							if (!pollTimer && !cancelled) {
								pollTimer = setInterval(() => void reload(), 5000);
							}
						}
					},
				});
			} catch {
				_streamState = 'polling';
			}

			if (!pollTimer) {
				_streamState = 'polling';
				pollTimer = setInterval(() => void reload(), 5000);
			}
		});

		_unsubscribe = () => {
			cancelled = true;
			if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
			if (stream) { stream.close(); stream = null; }
			_streamState = 'closed';
			_unsubscribe = null;
			_reload = null;
		};
	},

	/** Directly load messages for a convo (Bluesky pattern: independent of reload cycle). */
	async loadConvoMessages(convoId: ConvoId): Promise<ConvoEnvelope[]> {
		try {
			const envelopes = await withTimeout(getConvoMessages(convoId, { limit: 50 }), 8000, 'getConvoMessages');
			// Inject into snapshot if present
			if (_snapshot && envelopes.length > 0) {
				const existing = _snapshot.convos[convoId];
				if (existing) {
					_snapshot = {
						..._snapshot,
						convos: {
							..._snapshot.convos,
							[convoId]: { ...existing, envelopes },
						},
					};
				} else {
					// Create a minimal stub entry
					_snapshot = {
						..._snapshot,
						convos: {
							..._snapshot.convos,
							[convoId]: {
								convo: { id: convoId, name: convoId, description: '', encryptionEnabled: false, joinedMemberCount: 0 },
								envelopes,
								unread: { 'notificationCount': 0, 'highlightCount': 0 },
							},
						},
					};
				}
			}
			return envelopes;
		} catch (e) {
			console.warn('loadConvoMessages failed', e);
			return [];
		}
	},

	async refresh(): Promise<void> {
		if (_reload) await _reload();
	},

	unsubscribe(): void {
		if (_unsubscribe) _unsubscribe();
	},
};

// ─── Backward-compatible alias ───────────────────────────────────────────────
