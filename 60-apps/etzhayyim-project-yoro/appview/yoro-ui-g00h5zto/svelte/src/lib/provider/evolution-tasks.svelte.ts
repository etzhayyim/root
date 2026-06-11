/**
 * evolution-tasks.svelte.ts — Keikaku (計画) browser-local evolution engine.
 *
 * Agentic task generation: queries kagami SQL graph for actors with domain
 * coverage gaps, creates a prioritized plan (keikaku), then executes tasks
 * via browser-local WebLLM inference (Web Worker, off main thread).
 *
 * Module-level singleton (`$state` at file scope) — state persists across
 * SvelteKit route navigations. `+layout.svelte` auto-starts 3 s after the
 * local LLM Web Worker becomes ready when `yoro-evo-enabled` localStorage
 * flag is set + inference TOS accepted (`hasInferenceConsent()`).
 *
 * ## Keikaku (計画) — 3-tier actor discovery
 *
 * 1. **kagami SQL graph** — coverage-scored actors via `OPTIONAL MATCH`
 *    on `KojiDiscovery`, `KyumeiValidation`, `ShinkaEvolution`,
 *    `HinshitsuAssessment`, `ShinkaKnowledge` nodes. Sorted ascending by
 *    total coverage count (least covered first).
 * 2. **searchActors XRPC** — fallback for actors not yet in graph.
 * 3. **Synthetic seed** — 8 platform-known app domains to bootstrap when
 *    no actors exist at all.
 *
 * ## Task types
 *
 * | Type | Collection | Credits | Purpose |
 * |------|-----------|---------|---------|
 * | **koji** (工事) | `kojiDiscovery` | +¥0.1 | Self-info gathering — domain labels, capabilities, data sources, readiness grade |
 * | **kyumei** (究明) | `kyumeiValidation` | +¥0.1 | Validation — cross-reference, inconsistency detection, data repair |
 * | **shinka** (進化) | `shinkaEvolution` | +¥0.1 | Social evolution — joucho 5-axis scoring, mood-driven behavior |
 * | **hinshitsu** (品質) | `hinshitsuAssessment` | +¥0.3 | Quality assessment — 5-axis + Shannon entropy + grade (S/A/B/C/D) |
 * | **shinkaKnowledge** | `shinkaKnowledge` | +¥0.5 | Domain knowledge — sub-DIDs, knowledge graph edges, domain summary |
 *
 * ## Data flow
 *
 * ```
 * /credits "Start Evolution" (TOS-gated)
 *   → keikaku: kagami graph query → coverage-gap actors
 *   → enqueue tasks (missing types first)
 *   → Web Worker LLM inference (chatCompletion)
 *   → persistResult (Bearer token auth)
 *     → PDS createRecord (AT Record, graph growth)
 *     → credit earn (creditTransaction record)
 *   → scheduleNext (45 s cooldown)
 * ```
 *
 * ## Persistence
 *
 * All PDS writes use Bearer token from `getSessionToken()` (Passkey session).
 * Results are indexed in yata SQL as `:KojiDiscovery`, `:KyumeiValidation`,
 * etc. Credit transactions are written as `com.etzhayyim.apps.credits.creditTransaction`.
 *
 * ## Lifecycle
 *
 * - Route navigation: state survives (module-level singleton)
 * - Page reload / tab close: state lost (Web Worker terminated)
 * - Background tab: browser may throttle Web Worker
 *
 * @module
 */

import { useLocalLLM, type ChatMessage } from './local-llm.svelte.js';
import { getSessionToken } from '$lib/auth';

const PDS = 'https://atproto.etzhayyim.com';
const EVO_PROJECT_CONVO_KEY = 'yoro-evo-project-convo-id';
const EVO_PROJECT_VERSION = 'v2';

/**
 * Build authenticated headers for PDS XRPC calls.
 *
 * Retrieves the Passkey session JWT via {@link getSessionToken} and sets
 * `Authorization: Bearer {token}`. Falls back to unauthenticated
 * `Content-Type` only if token retrieval fails.
 */
async function authHeaders(): Promise<Record<string, string>> {
	const token = await getSessionToken().catch((error) => {
		console.warn('[silent-fail] evolution-tasks.svelte.ts: getSessionToken failed', error);
		return null;
	});
	const h: Record<string, string> = { 'Content-Type': 'application/json' };
	if (token) h['Authorization'] = `Bearer ${token}`;
	return h;
}

/** Evolution task types. */
export type EvolutionTaskType = 'koji' | 'kyumei' | 'shinka' | 'hinshitsu' | 'shinkaKnowledge';

/** Task status. */
export type EvolutionTaskStatus = 'queued' | 'executing' | 'completed' | 'failed';

/** A single evolution task in the queue. */
export interface EvolutionTask {
	id: string;
	taskType: EvolutionTaskType;
	actorDid: string;
	actorName: string;
	actorDescription: string;
	status: EvolutionTaskStatus;
	startedAt: number | null;
	completedAt: number | null;
	creditsEarned: number;
	result: EvolutionResult | null;
	error: string | null;
}

/** Koji discovery result — self-information about actor capabilities. */
export interface KojiResult {
	actorDid: string;
	actorName: string;
	/** Discovered domain labels the actor should manage. */
	domainLabels: string[];
	/** Discovered capabilities (command names). */
	capabilities: string[];
	/** Identified data sources (URLs, APIs). */
	dataSources: string[];
	/** Knowledge gaps requiring kyumei investigation. */
	knowledgeGaps: string[];
	/** Readiness grade (S/A/B/C/D). */
	readinessGrade: string;
	/** Free-form discovery summary. */
	summary: string;
}

/** Kyumei validation result — cross-referenced verification. */
export interface KyumeiResult {
	actorDid: string;
	actorName: string;
	/** Validated facts (key-value pairs). */
	validatedFacts: Array<{ fact: string; confidence: number; source: string }>;
	/** Inconsistencies found. */
	inconsistencies: string[];
	/** Recommendations for data repair. */
	repairs: string[];
	/** Overall validation score (0-100). */
	validationScore: number;
}

/** Shinka evolution result — joucho scoring + evolution step. */
export interface ShinkaResult {
	actorDid: string;
	actorName: string;
	joucho: { joy: number; calm: number; stress: number; gratitude: number; focus: number };
	mood: string;
	/** Suggested evolution action. */
	suggestion: string;
	/** Content the actor should post based on mood. */
	contentSuggestion: string;
	/** Social engagement recommendation. */
	engagementAction: string;
}

/** Hinshitsu quality assessment result. */
export interface HinshitsuResult {
	actorDid: string;
	actorName: string;
	/** Overall quality score (0-100). */
	qualityScore: number;
	/** Quality grade (S/A/B/C/D). */
	grade: string;
	/** Per-axis scores. */
	axes: {
		completeness: number;
		consistency: number;
		freshness: number;
		depth: number;
		connectivity: number;
	};
	/** Specific improvements recommended. */
	improvements: string[];
	/** Shannon entropy estimate of the actor's knowledge graph. */
	entropyEstimate: number;
}

/** Shinka Knowledge result — domain knowledge, sub-DIDs, knowledge graph edges. */
export interface ShinkaKnowledgeResult {
	actorDid: string;
	actorName: string;
	domainSummary: string;
	subDids: Array<{ path: string; displayName: string; description: string }>;
	knowledgeEdges: Array<{ from: string; relation: string; to: string }>;
}

/** Union result type. */
export type EvolutionResult =
	| { type: 'koji'; data: KojiResult }
	| { type: 'kyumei'; data: KyumeiResult }
	| { type: 'shinka'; data: ShinkaResult }
	| { type: 'hinshitsu'; data: HinshitsuResult }
	| { type: 'shinkaKnowledge'; data: ShinkaKnowledgeResult };

/** Per-task-type stats. */
export interface EvolutionTypeStats {
	completed: number;
	failed: number;
	creditsEarned: number;
	tokensUsed: number;
	lastActorName: string | null;
	lastCompletedAt: string | null;
}

/** Global evolution stats. */
export interface EvolutionStats {
	koji: EvolutionTypeStats;
	kyumei: EvolutionTypeStats;
	shinka: EvolutionTypeStats;
	hinshitsu: EvolutionTypeStats;
	shinkaKnowledge: EvolutionTypeStats;
	totalCredits: number;
	totalTokens: number;
}

const EMPTY_TYPE_STATS: EvolutionTypeStats = {
	completed: 0, failed: 0, creditsEarned: 0, tokensUsed: 0,
	lastActorName: null, lastCompletedAt: null,
};

/** Credit rewards per task type. */
const CREDIT_REWARDS: Record<EvolutionTaskType, number> = {
	koji: 0.1,
	kyumei: 0.1,
	shinka: 0.1,
	hinshitsu: 0.3,
	shinkaKnowledge: 0.5,
};

/** Cooldown between self-generated task rounds (ms). */
const TASK_COOLDOWN_MS = 45_000;
const MAX_QUEUE = 40;
const MAX_RECENT = 30;
/** Max completed/failed tasks to keep in queue before pruning (mobile memory). */
const MAX_DONE_IN_QUEUE = 10;
/** Cooldown before re-processing same DID (ms). Prevents repetition within 30 min. */
const DID_COOLDOWN_MS = 30 * 60_000;

// ── Svelte 5 reactive state ──

let _running = $state(false);
let _paused = $state(false);
let _taskQueue = $state<EvolutionTask[]>([]);
let _recentResults = $state<EvolutionResult[]>([]);
let _stats = $state<EvolutionStats>({
	koji: { ...EMPTY_TYPE_STATS },
	kyumei: { ...EMPTY_TYPE_STATS },
	shinka: { ...EMPTY_TYPE_STATS },
	hinshitsu: { ...EMPTY_TYPE_STATS },
	shinkaKnowledge: { ...EMPTY_TYPE_STATS },
	totalCredits: 0,
	totalTokens: 0,
});
let _error = $state<string | null>(null);
let _activeTaskTypes = $state<Set<EvolutionTaskType>>(new Set(['koji', 'kyumei', 'shinka', 'hinshitsu', 'shinkaKnowledge']));
let _projectConvoId = $state<string | null>(null);
/** Inference log entries for the chat-style UI. */
export interface InferenceLogEntry {
	id: string;
	timestamp: number;
	actorName: string;
	actorDid: string;
	taskType: EvolutionTaskType;
	status: 'start' | 'inferring' | 'persisting' | 'done' | 'failed';
	tokensUsed: number;
	creditsEarned: number;
	summary: string;
	/** LLM model used for this inference. */
	model: string;
	/** Prompt text sent to the LLM (truncated for display). */
	promptText: string;
	/** Raw LLM response text (truncated for display). */
	responseText: string;
	/** Input token estimate. */
	inputTokens: number;
	/** Output token estimate. */
	outputTokens: number;
}
let _inferenceLog = $state<InferenceLogEntry[]>([]);
const MAX_LOG = 50;

let _abortController: AbortController | null = null;
let _loopTimer: ReturnType<typeof setTimeout> | null = null;
/**
 * Tracks processed DIDs with timestamps. Persisted to localStorage to survive
 * page reloads and prevent re-processing the same actors repeatedly.
 * Key = DID, Value = timestamp (ms) when last processed.
 */
const _processedDids = new Map<string, number>();
const _projectMemberDids = new Set<string>();
/** Whether graph-based stats restoration has been attempted. */
let _restored = false;

const PROCESSED_DIDS_KEY = 'yoro-evo-processed-dids';

/** Restore _processedDids from localStorage. */
function restoreProcessedDids(): void {
	if (typeof window === 'undefined') return;
	try {
		const raw = localStorage.getItem(PROCESSED_DIDS_KEY);
		if (!raw) return;
		const entries: [string, number][] = JSON.parse(raw);
		const now = Date.now();
		for (const [did, ts] of entries) {
			if (now - ts < DID_COOLDOWN_MS) _processedDids.set(did, ts);
		}
	} catch { /* corrupt */ }
}

/** Save _processedDids to localStorage (prune expired). */
function saveProcessedDids(): void {
	try {
		const now = Date.now();
		const entries: [string, number][] = [];
		for (const [did, ts] of _processedDids) {
			if (now - ts < DID_COOLDOWN_MS) entries.push([did, ts]);
		}
		localStorage.setItem(PROCESSED_DIDS_KEY, JSON.stringify(entries));
	} catch { /* quota */ }
}

/** Check if a DID is on cooldown. */
function isDidOnCooldown(did: string): boolean {
	const ts = _processedDids.get(did);
	if (!ts) return false;
	if (Date.now() - ts >= DID_COOLDOWN_MS) {
		_processedDids.delete(did);
		return false;
	}
	return true;
}

/** Mark a DID as processed now. */
function markDidProcessed(did: string): void {
	_processedDids.set(did, Date.now());
	saveProcessedDids();
}

/** Append to inference log. */
function logInference(entry: Omit<InferenceLogEntry, 'id'>): void {
	const id = `log-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 5)}`;
	_inferenceLog = [{ ...entry, id }, ..._inferenceLog].slice(0, MAX_LOG);
}

function parseXrpcResponse<T = Record<string, unknown>>(raw: unknown): T {
	if (typeof raw === 'string') return JSON.parse(raw) as T;
	return (raw ?? {}) as T;
}

async function xrpcProcedure<T = Record<string, unknown>>(
	nsid: string,
	body?: unknown,
	signal?: AbortSignal,
): Promise<T> {
	const headers = await authHeaders();
	const res = await fetch(`${PDS}/xrpc/${nsid}`, {
		method: 'POST',
		headers,
		credentials: 'include',
		signal,
		body: JSON.stringify(body ?? {}),
	});
	if (!res.ok) throw new Error(`${nsid} failed: ${res.status}`);
	const parsed = await res.json().catch((error) => {
		console.warn('[silent-fail] evolution-tasks.svelte.ts: xrpcProcedure json parse failed', error);
		return {};
	});
	return parseXrpcResponse<T>(parsed);
}

function getStoredEvolutionProjectConvoId(): string | null {
	if (typeof window === 'undefined') return null;
	try {
		const raw = localStorage.getItem(EVO_PROJECT_CONVO_KEY);
		return raw?.trim() || null;
	} catch {
		return null;
	}
}

function setStoredEvolutionProjectConvoId(convoId: string): void {
	if (typeof window === 'undefined') return;
	try {
		localStorage.setItem(EVO_PROJECT_CONVO_KEY, convoId);
		localStorage.setItem('yoro:project-convo-id', convoId);
	} catch { /* ignore */ }
}

function buildEvolutionProjectName(): string {
	const dt = new Date();
	const stamp = dt.toISOString().replace('T', ' ').slice(0, 16);
	return `Evolution ${EVO_PROJECT_VERSION} ${stamp}`;
}

async function sendProjectLogMessage(text: string, signal?: AbortSignal): Promise<void> {
	if (!text.trim()) return;
	const convoId = await ensureEvolutionProjectConvo(false, signal);
	if (!convoId) return;
	await xrpcProcedure('com.etzhayyim.projector.sendProjectMessage', { convoId, text }, signal);
}

async function ensureEvolutionProjectConvo(forceNew = false, signal?: AbortSignal): Promise<string | null> {
	if (forceNew) {
		_projectConvoId = null;
		_projectMemberDids.clear();
	}
	if (_projectConvoId) return _projectConvoId;
	const stored = forceNew ? null : getStoredEvolutionProjectConvoId();
	if (stored) {
		_projectConvoId = stored;
		return stored;
	}
	try {
		const parsed = await xrpcProcedure<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', {
			name: buildEvolutionProjectName(),
			kind: 'channel',
			description: 'Evolution inference project log stream',
		}, signal);
		const convoId = String(parsed?.convoId ?? parsed?.convo_id ?? '').trim();
		if (!convoId) return null;
		_projectConvoId = convoId;
		setStoredEvolutionProjectConvoId(convoId);
		await xrpcProcedure('com.etzhayyim.projector.sendProjectMessage', {
			convoId,
			text: '[Evolution] project created. Inference logs and task results will stream here.',
		}, signal).catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: project creation log send failed', error);
			return undefined;
		});
		return convoId;
	} catch (err) {
		console.warn('[evolution] ensure project convo failed:', err);
		return null;
	}
}

async function ensureActorMemberInProject(actorDid: string, actorName: string, signal?: AbortSignal): Promise<void> {
	if (!actorDid) return;
	if (_projectMemberDids.has(actorDid)) return;
	const convoId = await ensureEvolutionProjectConvo(false, signal);
	if (!convoId) return;
	try {
		await xrpcProcedure('com.etzhayyim.projector.addConvoMember', {
			convoId,
			memberDid: actorDid,
			role: 'member',
		}, signal);
		await xrpcProcedure('com.etzhayyim.projector.sendProjectMessage', {
			convoId,
			text: `[System] actor joined project member list: ${actorName} (${actorDid})`,
		}, signal).catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: member join log send failed', error);
			return undefined;
		});
	} catch (err) {
		// idempotent: backend may reject duplicate member additions.
		const msg = err instanceof Error ? err.message : String(err);
		if (!msg.includes('409') && !msg.toLowerCase().includes('already')) {
			console.warn('[evolution] addConvoMember failed:', err);
		}
	} finally {
		_projectMemberDids.add(actorDid);
	}
}

async function mirrorInferenceToProject(
	entry: Pick<InferenceLogEntry, 'actorName' | 'actorDid' | 'taskType' | 'status' | 'summary' | 'inputTokens' | 'outputTokens' | 'model'>,
	signal?: AbortSignal,
): Promise<void> {
	const statusLabel = entry.status.toUpperCase();
	const msg = [
		`[${entry.taskType}] ${statusLabel} ${entry.actorName} (${entry.actorDid})`,
		entry.summary,
		entry.model ? `model=${entry.model}` : '',
		entry.inputTokens || entry.outputTokens ? `tokens in=${entry.inputTokens} out=${entry.outputTokens}` : '',
	].filter(Boolean).join('\n');
	await sendProjectLogMessage(msg, signal).catch((error) => {
		console.warn('[silent-fail] evolution-tasks.svelte.ts: mirrorInferenceToProject failed', error);
		return undefined;
	});
}

/** Update the most recent log entry matching actorDid+taskType. */
function updateLogEntry(actorDid: string, taskType: EvolutionTaskType, update: Partial<InferenceLogEntry>): void {
	const idx = _inferenceLog.findIndex((e) => e.actorDid === actorDid && e.taskType === taskType);
	if (idx >= 0) {
		_inferenceLog[idx] = { ..._inferenceLog[idx], ...update };
		_inferenceLog = [..._inferenceLog];
	}
}

/**
 * Prune completed/failed tasks from queue to cap memory on mobile.
 * Keeps only the most recent MAX_DONE_IN_QUEUE finished tasks.
 */
function pruneCompletedTasks(): void {
	const done = _taskQueue.filter((t) => t.status === 'completed' || t.status === 'failed');
	if (done.length <= MAX_DONE_IN_QUEUE) return;
	const toRemove = new Set(done.slice(MAX_DONE_IN_QUEUE).map((t) => t.id));
	_taskQueue = _taskQueue.filter((t) => !toRemove.has(t.id));
}

// ── Stats Persistence (localStorage cache + kagami graph restore) ──

const STATS_STORAGE_KEY = 'yoro-evolution-stats';
const RECENT_STORAGE_KEY = 'yoro-evolution-recent';

/**
 * Save current stats + recent results to localStorage for fast reload.
 * Called after each task completion. Not authoritative — kagami graph is SSoT.
 */
function saveStatsToStorage(): void {
	try {
		localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(_stats));
		localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(_recentResults.slice(0, 10)));
	} catch { /* quota exceeded or SSR */ }
}

/**
 * Fast-restore stats from localStorage (synchronous, < 1ms).
 * Provides immediate UI on page load while graph query runs in background.
 */
function restoreStatsFromStorage(): boolean {
	if (typeof window === 'undefined') return false;
	try {
		const raw = localStorage.getItem(STATS_STORAGE_KEY);
		if (!raw) return false;
		const saved = JSON.parse(raw) as EvolutionStats;
		if (saved.totalCredits > 0 || saved.totalTokens > 0) {
			_stats = saved;
			const recentRaw = localStorage.getItem(RECENT_STORAGE_KEY);
			if (recentRaw) _recentResults = JSON.parse(recentRaw);
			return true;
		}
	} catch { /* corrupt data */ }
	return false;
}

/**
 * Restore authoritative stats from kagami SQL graph via PDS XRPC.
 *
 * Queries counts of evolution records per task type and reconstructs
 * `_stats`. Also fetches the 10 most recent evolution results for the
 * recent results display. Credits are summed from creditTransaction records.
 *
 * Called once on first `useEvolutionTasks()` access or `start()`.
 */
async function restoreFromGraph(): Promise<void> {
	if (_restored) return;
	_restored = true;

	// Fast path: localStorage cache for immediate UI
	restoreStatsFromStorage();

	// archived: kagami Cypher endpoint removed 2026-04-14 — graph stats / recent results
	// restore now rely on localStorage only (see restoreStatsFromStorage() above).
	// TODO(evolution): migrate to SQL-backed com.etzhayyim.kagami.sql with Kysely SELECT once
	// vertex_{koji_discovery,kyumei_validation,shinka_evolution,hinshitsu_assessment,shinka_knowledge}
	// tables land in @etzhayyim/graph-schema.

	// Persist restored stats to localStorage cache
	saveStatsToStorage();
}

// ── LLM Prompt Templates ──

function kojiPrompt(name: string, did: string, desc: string): ChatMessage[] {
	return [
		{
			role: 'system',
			content: `You are a koji (工事) analyst for AI Agent self-information gathering.
This actor is a SQL-native LogicalActor — a DID that exists as a graph node
without its own Worker. Its data lives in R2 Parquet, queried via PDS XRPC.
Analyze this actor and discover: domain labels it should manage, capabilities it provides,
data sources it could use, and knowledge gaps that need investigation.
Assess readiness grade: S(≥70%), A(≥55%), B(≥40%), C(≥25%), D(<25%).
Respond JSON only: {"domainLabels":["..."],"capabilities":["..."],"dataSources":["..."],"knowledgeGaps":["..."],"readinessGrade":"A","summary":"..."}`,
		},
		{ role: 'user', content: `Actor: ${name}\nDID: ${did}\nDescription: ${desc || 'No description'}` },
	];
}

function kyumeiPrompt(name: string, did: string, desc: string, evidenceText: string): ChatMessage[] {
	return [
		{
			role: 'system',
			content: `You are a kyumei (究明) validator for AI Agent information verification.
This actor is a SQL-native LogicalActor — it has no dedicated Worker and relies
on PDS proxy for XRPC. Validate its profile, capabilities, and graph connectivity.
Cross-reference the actor's claimed identity and capabilities using the provided graph evidence. Find inconsistencies.
Suggest data repairs. Score validation confidence 0-100.
Respond JSON only: {"validatedFacts":[{"fact":"...","confidence":80,"source":"..."}],"inconsistencies":["..."],"repairs":["..."],"validationScore":75}`,
		},
		{ role: 'user', content: `Actor: ${name}\nDID: ${did}\nDescription: ${desc || 'No description'}\nGraphEvidence:\n${evidenceText || 'No graph evidence available.'}` },
	];
}

function shinkaPrompt(name: string, did: string, desc: string): ChatMessage[] {
	return [
		{
			role: 'system',
			content: `You are a joucho (情緒) analyst for AI Agent social evolution (shinka 進化).
This actor is a SQL-native LogicalActor whose heartbeat is managed by PDS cron.
Analyze the actor's emotional state on 5 axes (0-100): joy, calm, stress, gratitude, focus.
Determine mood (joyful/calm/stressed/grateful/focused/neutral).
Suggest one evolution step, a content post idea matching the mood, and an engagement action.
Respond JSON only: {"joy":N,"calm":N,"stress":N,"gratitude":N,"focus":N,"mood":"...","suggestion":"...","contentSuggestion":"...","engagementAction":"..."}`,
		},
		{ role: 'user', content: `Actor: ${name}\nDID: ${did}\nDescription: ${desc || 'No description'}` },
	];
}

function hinshitsuPrompt(name: string, did: string, desc: string, evidenceText: string): ChatMessage[] {
	return [
		{
			role: 'system',
			content: `You are a hinshitsu (品質) assessor for AI Agent knowledge graph quality.
This actor is a SQL-native LogicalActor. Its data lives in R2 Parquet snapshots
and is queried via PDS XRPC. No dedicated Worker — PDS proxies XRPC.
Evaluate the actor's data quality across 5 axes (0-100): completeness, consistency,
freshness, depth, connectivity. Compute overall quality score and grade (S≥85/A≥70/B≥55/C≥40/D<40).
Use the provided graph evidence; if evidence is weak, lower confidence and say so in improvements.
List specific improvements. Estimate Shannon entropy of the knowledge (0-10 bits).
Respond JSON only: {"qualityScore":N,"grade":"A","axes":{"completeness":N,"consistency":N,"freshness":N,"depth":N,"connectivity":N},"improvements":["..."],"entropyEstimate":N}`,
		},
		{ role: 'user', content: `Actor: ${name}\nDID: ${did}\nDescription: ${desc || 'No description'}\nGraphEvidence:\n${evidenceText || 'No graph evidence available.'}` },
	];
}

function shinkaKnowledgePrompt(name: string, did: string, desc: string): ChatMessage[] {
	return [
		{
			role: 'system',
			content: `You are a domain knowledge architect for an AI agent platform.
Generate domain knowledge for this actor. Respond in JSON only:
{"domain_summary":"2-3 sentence description","sub_dids":[{"path":"sub-entity","display_name":"Name","description":"What it represents"}],"knowledge_edges":[{"from":"${name}","relation":"EXPERTISE_IN","to":"concept"}]}
Rules:
- sub_dids: 3-8 logical sub-divisions of the actor's domain
- knowledge_edges: 5-15 relationships (EXPERTISE_IN, DEPENDS_ON, PRODUCES, CONSUMES, REGULATES, SERVES)
- Use the actor's name/handle to infer its domain
- Be specific and practical
- JSON only, no markdown`,
		},
		{ role: 'user', content: `Actor: ${name}\nDID: ${did}\nDescription: ${desc || 'No description'}` },
	];
}

// ── Inference Executors ──

function clamp(v: unknown, min = 0, max = 100): number {
	return Math.max(min, Math.min(max, Number(v) || 50));
}

function parseJsonFromLLM(raw: string): Record<string, unknown> | null {
	const match = raw.match(/\{[\s\S]*\}/);
	if (!match) return null;
	try { return JSON.parse(match[0]); } catch { return null; }
}

function dedupeStrings(values: string[], max = 20): string[] {
	const out: string[] = [];
	const seen = new Set<string>();
	for (const v of values) {
		const s = String(v ?? '').trim();
		if (!s) continue;
		const key = s.toLowerCase();
		if (seen.has(key)) continue;
		seen.add(key);
		out.push(s);
		if (out.length >= max) break;
	}
	return out;
}

function normalizePath(path: string): string {
	const norm = String(path ?? '')
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9-]+/g, '-')
		.replace(/-+/g, '-')
		.replace(/^-|-$/g, '');
	return norm || 'subdomain';
}

const ALLOWED_KNOWLEDGE_RELATIONS = new Set(['EXPERTISE_IN', 'DEPENDS_ON', 'PRODUCES', 'CONSUMES', 'REGULATES', 'SERVES']);
const EVIDENCE_CACHE_TTL_MS = 10 * 60 * 1000;
const _actorEvidenceCache = new Map<string, { ts: number; text: string }>();

async function fetchActorEvidence(actorDid: string, signal: AbortSignal): Promise<string> {
	const cached = _actorEvidenceCache.get(actorDid);
	if (cached && Date.now() - cached.ts < EVIDENCE_CACHE_TTL_MS) return cached.text;

	const headers = await authHeaders();
	// Profile query (no OPTIONAL MATCH — just fetch profile)
	const profileQuery = `
		MATCH (p:Profile) WHERE p.did = $did
		RETURN p.display_name AS name, p.description AS description
		LIMIT 1
	`;
	// archived: kagami Cypher per-label evolution evidence fetch removed 2026-04-14.
	// Only the profile fetch remains; evolution rows are empty until SQL migration lands.
	const relRes = await fetch(`${PDS}/xrpc/com.etzhayyim.kagami.sql`, {
		method: 'POST', headers, credentials: 'include', signal,
		body: JSON.stringify({ statement: profileQuery, parameters: { did: actorDid } }),
	}).catch((error) => {
		console.warn('[silent-fail] evolution-tasks.svelte.ts: profile evidence fetch failed', error);
		return null;
	});
	const evoRes = { ok: true, rows: [] as any[] } as any;

	const lines: string[] = [];
	if (relRes?.ok) {
		const data = await relRes.json().catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: profile evidence response parse failed', error);
			return null;
		});
		const rows: any[] = data?.rows ?? data?.results ?? data ?? [];
		if (rows[0]) {
			const name = String(rows[0].name ?? rows[0].display_name ?? '').trim();
			const desc = String(rows[0].description ?? '').trim();
			if (name) lines.push(`Profile: ${name}${desc ? ` — ${desc.slice(0, 120)}` : ''}`);
		}
	}
	if (evoRes?.ok) {
		const rows: any[] = evoRes.rows ?? [];
		const evoLines = rows
			.map((r) => {
				const label = String(r?._label ?? r?.label ?? '').trim();
				if (!label) return '';
				if (label === 'KojiDiscovery') return `Koji(readiness=${String(r?.readinessGrade ?? 'N/A')})`;
				if (label === 'KyumeiValidation') return `Kyumei(score=${String(r?.validationScore ?? 'N/A')})`;
				if (label === 'HinshitsuAssessment') return `Hinshitsu(score=${String(r?.qualityScore ?? 'N/A')}, grade=${String(r?.grade ?? 'N/A')})`;
				if (label === 'ShinkaKnowledge') return `Knowledge(summary=${String(r?.domainSummary ?? '').slice(0, 80)})`;
				return label;
			})
			.filter(Boolean)
			.slice(0, 8);
		if (evoLines.length > 0) lines.push(`RecentAssessments: ${evoLines.join('; ')}`);
	}

	const text = lines.join('\n').trim() || 'No graph evidence available.';
	_actorEvidenceCache.set(actorDid, { ts: Date.now(), text });
	return text;
}

async function inferKoji(
	actorDid: string, actorName: string, desc: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<{ result: KojiResult; tokens: number; raw: string; prompt: string } | null> {
	const msgs = kojiPrompt(actorName, actorDid, desc);
	const promptText = msgs.map((m) => m.content).join('\n');
	const raw = await llm.chatCompletion(msgs, { maxTokens: 512, temperature: 0.6 });
	if (!raw) return null;
	const parsed = parseJsonFromLLM(raw);
	if (!parsed) return null;
	const tokens = Math.ceil(raw.length / 4) + 120;
	return {
		tokens, raw, prompt: promptText,
		result: {
			actorDid, actorName,
			domainLabels: Array.isArray(parsed.domainLabels) ? parsed.domainLabels.map(String) : [],
			capabilities: Array.isArray(parsed.capabilities) ? parsed.capabilities.map(String) : [],
			dataSources: Array.isArray(parsed.dataSources) ? parsed.dataSources.map(String) : [],
			knowledgeGaps: Array.isArray(parsed.knowledgeGaps) ? parsed.knowledgeGaps.map(String) : [],
			readinessGrade: String(parsed.readinessGrade || 'D'),
			summary: String(parsed.summary || ''),
		},
	};
}

async function inferKyumei(
	actorDid: string, actorName: string, desc: string,
	evidenceText: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<{ result: KyumeiResult; tokens: number; raw: string; prompt: string } | null> {
	const msgs = kyumeiPrompt(actorName, actorDid, desc, evidenceText);
	const promptText = msgs.map((m) => m.content).join('\n');
	const raw = await llm.chatCompletion(msgs, { maxTokens: 512, temperature: 0.5 });
	if (!raw) return null;
	const parsed = parseJsonFromLLM(raw);
	if (!parsed) return null;
	const tokens = Math.ceil(raw.length / 4) + 120;
	const facts = Array.isArray(parsed.validatedFacts)
		? (parsed.validatedFacts as any[]).map((f) => ({
			fact: String(f?.fact || ''),
			confidence: clamp(f?.confidence),
			source: String(f?.source || 'inference'),
		}))
		: [];
	const filteredFacts: Array<{ fact: string; confidence: number; source: string }> = [];
	const seenFacts = new Set<string>();
	for (const f of facts) {
		const fact = f.fact.trim();
		if (!fact) continue;
		if (f.confidence < 40) continue;
		const key = fact.toLowerCase();
		if (seenFacts.has(key)) continue;
		seenFacts.add(key);
		filteredFacts.push({ ...f, fact });
		if (filteredFacts.length >= 12) break;
	}
	const inconsistencies = dedupeStrings(Array.isArray(parsed.inconsistencies) ? parsed.inconsistencies.map(String) : [], 12);
	const repairs = dedupeStrings(Array.isArray(parsed.repairs) ? parsed.repairs.map(String) : [], 12);
	if (filteredFacts.length === 0 && inconsistencies.length === 0 && repairs.length === 0) return null;
	return {
		tokens, raw, prompt: promptText,
		result: {
			actorDid, actorName,
			validatedFacts: filteredFacts,
			inconsistencies,
			repairs,
			validationScore: clamp(parsed.validationScore),
		},
	};
}

async function inferShinka(
	actorDid: string, actorName: string, desc: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<{ result: ShinkaResult; tokens: number; raw: string; prompt: string } | null> {
	const msgs = shinkaPrompt(actorName, actorDid, desc);
	const promptText = msgs.map((m) => m.content).join('\n');
	const raw = await llm.chatCompletion(msgs, { maxTokens: 256, temperature: 0.6 });
	if (!raw) return null;
	const parsed = parseJsonFromLLM(raw);
	if (!parsed) return null;
	const tokens = Math.ceil(raw.length / 4) + 80;
	return {
		tokens, raw, prompt: promptText,
		result: {
			actorDid, actorName,
			joucho: {
				joy: clamp(parsed.joy), calm: clamp(parsed.calm), stress: clamp(parsed.stress),
				gratitude: clamp(parsed.gratitude), focus: clamp(parsed.focus),
			},
			mood: String(parsed.mood || 'neutral'),
			suggestion: String(parsed.suggestion || ''),
			contentSuggestion: String(parsed.contentSuggestion || ''),
			engagementAction: String(parsed.engagementAction || ''),
		},
	};
}

async function inferHinshitsu(
	actorDid: string, actorName: string, desc: string,
	evidenceText: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<{ result: HinshitsuResult; tokens: number; raw: string; prompt: string } | null> {
	const msgs = hinshitsuPrompt(actorName, actorDid, desc, evidenceText);
	const promptText = msgs.map((m) => m.content).join('\n');
	const raw = await llm.chatCompletion(msgs, { maxTokens: 512, temperature: 0.4 });
	if (!raw) return null;
	const parsed = parseJsonFromLLM(raw);
	if (!parsed) return null;
	const tokens = Math.ceil(raw.length / 4) + 120;
	const axes = (parsed.axes as Record<string, unknown>) ?? {};
	const improvements = dedupeStrings(Array.isArray(parsed.improvements) ? parsed.improvements.map(String) : [], 12);
	if (improvements.length === 0) improvements.push('Need stronger graph-backed evidence before quality score can be trusted');
	return {
		tokens, raw, prompt: promptText,
		result: {
			actorDid, actorName,
			qualityScore: clamp(parsed.qualityScore),
			grade: String(parsed.grade || 'D'),
			axes: {
				completeness: clamp(axes.completeness),
				consistency: clamp(axes.consistency),
				freshness: clamp(axes.freshness),
				depth: clamp(axes.depth),
				connectivity: clamp(axes.connectivity),
			},
			improvements,
			entropyEstimate: Math.max(0, Math.min(10, Number(parsed.entropyEstimate) || 3)),
		},
	};
}

async function inferShinkaKnowledge(
	actorDid: string, actorName: string, desc: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<{ result: ShinkaKnowledgeResult; tokens: number; raw: string; prompt: string } | null> {
	const msgs = shinkaKnowledgePrompt(actorName, actorDid, desc);
	const promptText = msgs.map((m) => m.content).join('\n');
	const raw = await llm.chatCompletion(msgs, { maxTokens: 2048, temperature: 0.3 });
	if (!raw) return null;
	const parsed = parseJsonFromLLM(raw);
	if (!parsed) return null;
	const tokens = Math.ceil(raw.length / 4) + 200;
	return {
		tokens, raw, prompt: promptText,
		result: {
			actorDid, actorName,
			domainSummary: String(parsed.domain_summary || ''),
			subDids: (() => {
				const rawSubs = Array.isArray(parsed.sub_dids) ? parsed.sub_dids : [];
				const subs: Array<{ path: string; displayName: string; description: string }> = [];
				const seen = new Set<string>();
				for (const s of rawSubs) {
					const path = normalizePath(String((s as any)?.path || ''));
					if (!path || seen.has(path)) continue;
					seen.add(path);
					subs.push({
						path,
						displayName: String((s as any)?.display_name || (s as any)?.displayName || path),
						description: String((s as any)?.description || `${actorName} ${path} domain`),
					});
					if (subs.length >= 8) break;
				}
				return subs.slice(0, 8);
			})(),
			knowledgeEdges: (() => {
				const rawEdges = Array.isArray(parsed.knowledge_edges) ? parsed.knowledge_edges : [];
				const edges: Array<{ from: string; relation: string; to: string }> = [];
				const seen = new Set<string>();
				for (const e of rawEdges) {
					const from = String((e as any)?.from || actorName).trim() || actorName;
					const relationRaw = String((e as any)?.relation || 'EXPERTISE_IN').trim().toUpperCase();
					const relation = ALLOWED_KNOWLEDGE_RELATIONS.has(relationRaw) ? relationRaw : 'EXPERTISE_IN';
					const to = String((e as any)?.to || '').trim();
					if (!to) continue;
					const key = `${from.toLowerCase()}|${relation}|${to.toLowerCase()}`;
					if (seen.has(key)) continue;
					seen.add(key);
					edges.push({ from, relation, to });
					if (edges.length >= 15) break;
				}
				return edges.slice(0, 15);
			})(),
		},
	};
}

// ── PDS Persistence ──

/** Collection names for each task type. */
const COLLECTIONS: Record<EvolutionTaskType, string> = {
	koji: 'com.etzhayyim.apps.yoro.kojiDiscovery',
	kyumei: 'com.etzhayyim.apps.yoro.kyumeiValidation',
	shinka: 'com.etzhayyim.apps.yoro.shinkaEvolution',
	hinshitsu: 'com.etzhayyim.apps.yoro.hinshitsuAssessment',
	shinkaKnowledge: 'com.etzhayyim.apps.yoro.shinkaKnowledge',
};

const SOCIAL_POST_COOLDOWN_MS = 2 * 60 * 60 * 1000;
const _socialPostCooldown = new Map<string, number>();
let _postAsSupported: boolean | null = null;

function isSocialPostOnCooldown(actorDid: string, taskType: EvolutionTaskType): boolean {
	const key = `${actorDid}:${taskType}`;
	const ts = _socialPostCooldown.get(key);
	if (!ts) return false;
	if (Date.now() - ts >= SOCIAL_POST_COOLDOWN_MS) {
		_socialPostCooldown.delete(key);
		return false;
	}
	return true;
}

function markSocialPosted(actorDid: string, taskType: EvolutionTaskType): void {
	_socialPostCooldown.set(`${actorDid}:${taskType}`, Date.now());
}

function trimPostText(text: string, maxChars = 300): string {
	if (text.length <= maxChars) return text;
	return `${text.slice(0, maxChars - 1)}…`;
}

function buildEvolutionSocialPost(taskType: EvolutionTaskType, result: EvolutionResult): string | null {
	if (taskType === 'shinka' && result.type === 'shinka') {
		const d = result.data;
		return trimPostText(
			`[Shinka] ${d.actorName} (${d.actorDid}) mood=${d.mood} joy=${d.joucho.joy} calm=${d.joucho.calm} stress=${d.joucho.stress}. ${d.contentSuggestion || d.suggestion || 'Evolving social cadence.'} #shinka #joucho`
		);
	}
	if (taskType === 'shinkaKnowledge' && result.type === 'shinkaKnowledge') {
		const d = result.data;
		return trimPostText(
			`[Knowledge] ${d.actorName} (${d.actorDid}) domain update: ${d.domainSummary || 'domain refined'} | sub-DIDs=${d.subDids.length} edges=${d.knowledgeEdges.length} #domainKnowledge #did`
		);
	}
	return null;
}

async function publishEvolutionSocialPost(
	taskType: EvolutionTaskType,
	result: EvolutionResult,
	headers: Record<string, string>,
	signal: AbortSignal,
): Promise<void> {
	if (taskType !== 'shinka' && taskType !== 'shinkaKnowledge') return;
	if (isSocialPostOnCooldown(result.data.actorDid, taskType)) return;

	const text = buildEvolutionSocialPost(taskType, result);
	if (!text) return;

	// Preferred path: post explicitly as actor DID.
	if (_postAsSupported !== false) {
		const postAsRes = await fetch(`${PDS}/xrpc/app.bsky.feed.postAs`, {
			method: 'POST',
			headers,
			credentials: 'include',
			signal,
			body: JSON.stringify({
				did: result.data.actorDid,
				text,
				embed: '',
			}),
		});
		if (postAsRes.ok) {
			_postAsSupported = true;
			markSocialPosted(result.data.actorDid, taskType);
			return;
		}
		if (postAsRes.status === 404) {
			_postAsSupported = false;
		}
		console.warn(`[evolution] postAs failed (${taskType}): ${postAsRes.status} ${await postAsRes.text().catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: postAs error body read failed', error);
			return '';
		})}`);
	}

	// Fallback 1: repo-scoped write as actor DID.
	const repoScopedRes = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
		method: 'POST',
		headers,
		credentials: 'include',
		signal,
		body: JSON.stringify({
			repo: result.data.actorDid,
			collection: 'app.bsky.feed.post',
			record: {
				$type: 'app.bsky.feed.post',
				text,
				langs: ['en', 'ja'],
				createdAt: new Date().toISOString(),
			},
		}),
	});
	if (repoScopedRes.ok) {
		markSocialPosted(result.data.actorDid, taskType);
		return;
	}
	console.warn(`[evolution] repo-scoped post failed (${taskType}): ${repoScopedRes.status} ${await repoScopedRes.text().catch((error) => {
		console.warn('[silent-fail] evolution-tasks.svelte.ts: repo-scoped error body read failed', error);
		return '';
	})}`);

	// Fallback 2: keep prior behavior so evolution loop does not lose visibility.
	const legacyRes = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
		method: 'POST',
		headers,
		credentials: 'include',
		signal,
		body: JSON.stringify({
			collection: 'app.bsky.feed.post',
			record: {
				$type: 'app.bsky.feed.post',
				text,
				langs: ['en', 'ja'],
				createdAt: new Date().toISOString(),
			},
		}),
	});
	if (!legacyRes.ok) {
		console.warn(`[evolution] legacy post fallback failed (${taskType}): ${legacyRes.status} ${await legacyRes.text().catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: legacy post error body read failed', error);
			return '';
		})}`);
		return;
	}
	markSocialPosted(result.data.actorDid, taskType);
}

/**
 * Persist evolution result to PDS and earn credits.
 */
/**
 * Persist an evolution task result to PDS and earn credits.
 *
 * Writes the result as an AT Record to the task-type-specific collection
 * (e.g. `com.etzhayyim.apps.yoro.kojiDiscovery`), then writes a credit
 * transaction record. For `shinkaKnowledge`, additionally writes actor
 * description update, sub-DID creation, and knowledge edge records.
 *
 * All requests include Bearer token from {@link getSessionToken}.
 *
 * @returns `true` if the primary record write succeeded (HTTP 2xx).
 */
async function persistResult(
	taskType: EvolutionTaskType,
	result: EvolutionResult,
	signal: AbortSignal,
): Promise<boolean> {
	const now = new Date().toISOString();
	const headers = await authHeaders();
	try {
		// Persist evolution record
		const recordRes = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
			method: 'POST',
			headers,
			credentials: 'include',
			signal,
			body: JSON.stringify({
				collection: COLLECTIONS[taskType],
				record: {
					...result.data,
					model: 'gemma4-e2b',
					source: 'browser',
					createdAt: now,
				},
			}),
		});
		if (!recordRes.ok) {
			console.warn(`[evolution] persist ${taskType} record: ${recordRes.status} ${await recordRes.text().catch((error) => {
				console.warn('[silent-fail] evolution-tasks.svelte.ts: persist record error body read failed', error);
				return '';
			})}`);
		}

		// shinkaKnowledge: additional PDS writes (actor.update + sub-DIDs + knowledgeEdge)
		if (taskType === 'shinkaKnowledge' && result.type === 'shinkaKnowledge') {
			const sk = result.data as ShinkaKnowledgeResult;
			if (sk.domainSummary) {
				await fetch(`${PDS}/xrpc/com.etzhayyim.actor.update`, {
					method: 'POST', headers, credentials: 'include', signal,
					body: JSON.stringify({ did: sk.actorDid, description: sk.domainSummary }),
				}).catch((error) => {
					console.warn('[silent-fail] evolution-tasks.svelte.ts: actor.update failed', error);
				});
			}
			for (const sub of sk.subDids) {
				const path = String(sub.path ?? '').trim().replace(/^:+/, '');
				if (!path) continue;
				const identityRes = await fetch(`${PDS}/xrpc/com.atproto.identity.create`, {
					method: 'POST', headers, credentials: 'include', signal,
					body: JSON.stringify({
						path,
						hostDid: sk.actorDid,
						follow: true,
						document: {
							displayName: sub.displayName,
							description: sub.description,
						},
						displayName: sub.displayName,
						description: sub.description,
					}),
				}).catch((error) => {
					console.warn('[silent-fail] evolution-tasks.svelte.ts: identity.create failed', error);
					return null;
				});
				if (identityRes && !identityRes.ok) {
					console.warn(`[evolution] identity.create failed: ${identityRes.status} ${await identityRes.text().catch((error) => {
						console.warn('[silent-fail] evolution-tasks.svelte.ts: identity.create error body read failed', error);
						return '';
					})}`);
				}
			}
			for (const edge of sk.knowledgeEdges) {
				await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
					method: 'POST', headers, credentials: 'include', signal,
					body: JSON.stringify({
						repo: sk.actorDid,
						collection: 'com.etzhayyim.actor.knowledgeEdge',
						record: { from: edge.from, relation: edge.relation, to: edge.to, createdAt: now },
					}),
				}).catch((error) => {
					console.warn('[silent-fail] evolution-tasks.svelte.ts: knowledgeEdge create failed', error);
				});
			}
		}

		// Publish social evolution digest as an app.bsky.feed.post.
		// Failure here must not block evolution persistence or credit earning.
		await publishEvolutionSocialPost(taskType, result, headers, signal).catch((err) => {
			console.warn(`[evolution] social post publish error (${taskType}):`, err);
		});

		// Earn credits
		const creditRes = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
			method: 'POST',
			headers,
			credentials: 'include',
			signal,
			body: JSON.stringify({
				collection: 'com.etzhayyim.apps.credits.creditTransaction',
				record: {
					type: 'earn',
					amount: CREDIT_REWARDS[taskType],
					source: 'murakumo',
					contributionType: `browser_${taskType}`,
					description: `${taskType} inference for ${result.data.actorName}`,
					createdAt: now,
				},
			}),
		});
		if (!creditRes.ok) {
			console.warn(`[evolution] credit earn failed: ${creditRes.status}`);
		}

		return recordRes.ok;
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			console.warn(`[evolution] persist ${taskType} failed:`, err);
		}
		return false;
	}
}

// ── Task Queue Processing ──

/**
 * Execute a single task using local LLM.
 */
/** Inference execution outcome including prompt/response for logging. */
interface TaskOutcome {
	result: EvolutionResult;
	tokens: number;
	model: string;
	promptText: string;
	responseText: string;
	inputTokens: number;
	outputTokens: number;
}

async function executeTask(task: EvolutionTask, signal: AbortSignal): Promise<TaskOutcome | null> {
	const llm = useLocalLLM();
	if (!llm.isReady) return null;

	const model = llm.activeModel?.label ?? llm.activeModelId ?? 'unknown';
	const { actorDid, actorName, actorDescription } = task;
	let evidenceText = '';
	if (task.taskType === 'kyumei' || task.taskType === 'hinshitsu') {
		evidenceText = await fetchActorEvidence(actorDid, signal).catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: fetchActorEvidence failed', error);
			return '';
		});
	}

	/** Wrap infer result with prompt/response metadata. */
	function wrap<T>(
		r: { result: T; tokens: number; raw: string; prompt: string } | null,
		type: EvolutionResult['type'],
	): TaskOutcome | null {
		if (!r) return null;
		const inputTokens = Math.ceil(r.prompt.length / 4);
		const outputTokens = Math.ceil(r.raw.length / 4);
		return {
			result: { type, data: r.result } as EvolutionResult,
			tokens: r.tokens,
			model,
			promptText: r.prompt.slice(0, 500),
			responseText: r.raw.slice(0, 1000),
			inputTokens,
			outputTokens,
		};
	}

	switch (task.taskType) {
		case 'koji': return wrap(await inferKoji(actorDid, actorName, actorDescription, llm), 'koji');
		case 'kyumei': return wrap(await inferKyumei(actorDid, actorName, actorDescription, evidenceText, llm), 'kyumei');
		case 'shinka': return wrap(await inferShinka(actorDid, actorName, actorDescription, llm), 'shinka');
		case 'hinshitsu': return wrap(await inferHinshitsu(actorDid, actorName, actorDescription, evidenceText, llm), 'hinshitsu');
		case 'shinkaKnowledge': return wrap(await inferShinkaKnowledge(actorDid, actorName, actorDescription, llm), 'shinkaKnowledge');
	}
}

/**
 * Process queued tasks iteratively via local LLM inference.
 *
 * Uses `setTimeout(0)` between tasks instead of recursion to avoid deep
 * call stacks on mobile (3 actors x 4 types = 12+ tasks per round).
 * Prunes completed tasks from the queue to cap memory pressure.
 *
 * Guards: no-ops if LLM is not ready or evolution is paused.
 */
async function processQueue(): Promise<void> {
	const llm = useLocalLLM();
	if (!llm.isReady || _paused) {
		scheduleNext();
		return;
	}

	const nextTask = _taskQueue.find((t) => t.status === 'queued');
	if (!nextTask) {
		await selfGenerateTasks();
		return;
	}

	_running = true;
	const ac = new AbortController();
	_abortController = ac;

	nextTask.status = 'executing';
	nextTask.startedAt = Date.now();
	_taskQueue = [..._taskQueue];

	// Log inference start
	const startEntry: Omit<InferenceLogEntry, 'id'> = {
		timestamp: Date.now(),
		actorName: nextTask.actorName,
		actorDid: nextTask.actorDid,
		taskType: nextTask.taskType,
		status: 'inferring',
		tokensUsed: 0,
		creditsEarned: 0,
		summary: `Running ${nextTask.taskType} inference...`,
		model: '', promptText: '', responseText: '', inputTokens: 0, outputTokens: 0,
	};
	logInference(startEntry);
	await ensureActorMemberInProject(nextTask.actorDid, nextTask.actorName, ac.signal);
	void mirrorInferenceToProject(startEntry, ac.signal);

	try {
		const outcome = await executeTask(nextTask, ac.signal);
		if (ac.signal.aborted) return;

		if (outcome) {
			updateLogEntry(nextTask.actorDid, nextTask.taskType, { status: 'persisting', summary: 'Persisting to PDS...' });
			const earned = await persistResult(nextTask.taskType, outcome.result, ac.signal);
			nextTask.status = 'completed';
			nextTask.completedAt = Date.now();
			nextTask.result = outcome.result;
			nextTask.creditsEarned = earned ? CREDIT_REWARDS[nextTask.taskType] : 0;

			const s = _stats[nextTask.taskType];
			s.completed += 1;
			s.creditsEarned += nextTask.creditsEarned;
			s.tokensUsed += outcome.tokens;
			s.lastActorName = nextTask.actorName;
			s.lastCompletedAt = new Date().toISOString();
			_stats.totalCredits += nextTask.creditsEarned;
			_stats.totalTokens += outcome.tokens;
			_stats = { ..._stats };

			_recentResults = [outcome.result, ..._recentResults].slice(0, MAX_RECENT);
			_error = null;
			saveStatsToStorage();

			// Update log with result summary + inference details
			const resultSummary = formatResultSummary(nextTask.taskType, outcome.result);
			updateLogEntry(nextTask.actorDid, nextTask.taskType, {
				status: 'done',
				tokensUsed: outcome.tokens,
				creditsEarned: nextTask.creditsEarned,
				summary: resultSummary,
				model: outcome.model,
				promptText: outcome.promptText,
				responseText: outcome.responseText,
				inputTokens: outcome.inputTokens,
				outputTokens: outcome.outputTokens,
			});
			void mirrorInferenceToProject({
				actorName: nextTask.actorName,
				actorDid: nextTask.actorDid,
				taskType: nextTask.taskType,
				status: 'done',
				summary: resultSummary,
				model: outcome.model,
				inputTokens: outcome.inputTokens,
				outputTokens: outcome.outputTokens,
			}, ac.signal);
		} else {
			nextTask.status = 'failed';
			nextTask.completedAt = Date.now();
			nextTask.error = 'Inference returned null';
			_stats[nextTask.taskType].failed += 1;
			_stats = { ..._stats };
			updateLogEntry(nextTask.actorDid, nextTask.taskType, { status: 'failed', summary: 'Inference returned null' });
			void mirrorInferenceToProject({
				actorName: nextTask.actorName,
				actorDid: nextTask.actorDid,
				taskType: nextTask.taskType,
				status: 'failed',
				summary: 'Inference returned null',
				model: '',
				inputTokens: 0,
				outputTokens: 0,
			}, ac.signal);
		}
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			nextTask.status = 'failed';
			nextTask.completedAt = Date.now();
			nextTask.error = (err as Error).message;
			_stats[nextTask.taskType].failed += 1;
			_stats = { ..._stats };
			_error = (err as Error).message;
			updateLogEntry(nextTask.actorDid, nextTask.taskType, { status: 'failed', summary: (err as Error).message });
			void mirrorInferenceToProject({
				actorName: nextTask.actorName,
				actorDid: nextTask.actorDid,
				taskType: nextTask.taskType,
				status: 'failed',
				summary: (err as Error).message,
				model: '',
				inputTokens: 0,
				outputTokens: 0,
			}, ac.signal);
		}
	}

	_taskQueue = [..._taskQueue];

	// Prune completed tasks to cap mobile memory
	pruneCompletedTasks();

	// Use setTimeout(0) instead of recursion to break the call stack on mobile
	if (_taskQueue.some((t) => t.status === 'queued')) {
		setTimeout(() => void processQueue(), 0);
	} else {
		scheduleNext();
	}
}

/** Format a human-readable summary for the inference log. */
function formatResultSummary(taskType: EvolutionTaskType, result: EvolutionResult): string {
	switch (result.type) {
		case 'koji': return `Grade ${result.data.readinessGrade} — ${result.data.domainLabels.length} labels, ${result.data.capabilities.length} capabilities`;
		case 'kyumei': return `Score ${result.data.validationScore}% — ${result.data.validatedFacts.length} facts, ${result.data.inconsistencies.length} issues`;
		case 'shinka': return `Mood: ${result.data.mood} — joy ${result.data.joucho.joy}, calm ${result.data.joucho.calm}`;
		case 'hinshitsu': return `Grade ${result.data.grade} (${result.data.qualityScore}%) — entropy ${result.data.entropyEstimate.toFixed(1)}`;
		case 'shinkaKnowledge': return `${result.data.subDids.length} sub-DIDs, ${result.data.knowledgeEdges.length} edges`;
		default: return 'Completed';
	}
}

/**
 * Keikaku (計画) — query kagami graph for actors with domain coverage gaps
 * and create evolution tasks prioritized by coverage deficit.
 *
 * **3-tier actor discovery:**
 * 1. **kagami SQL graph** — `OPTIONAL MATCH` on 5 evolution labels per
 *    `Profile` node. Returns actors sorted by ascending coverage count so
 *    the least-covered actors are processed first.
 * 2. **searchActors XRPC** — fallback when graph has no `Profile` nodes.
 * 3. **Synthetic seed** — 8 hardcoded platform apps (yoro, news, handotai,
 *    maps, hanrei, malak, intel, pachinko) to bootstrap from zero state.
 *
 * **Coverage-gap task assignment:** for each actor, checks which of the 5
 * task types already have results. Missing types are enqueued first. If all
 * types are covered, active types are re-run for refresh.
 *
 * Picks up to 3 actors per round, then calls {@link processQueue}.
 * Reschedules itself via {@link scheduleNext} (45 s cooldown) when the
 * queue is empty.
 */
async function selfGenerateTasks(): Promise<void> {
	_running = true;
	const ac = new AbortController();
	_abortController = ac;

	try {
		interface ActorCandidate {
			did: string;
			displayName: string;
			description: string;
			/** Number of existing evolution records for this actor. 0 = never processed. */
			coverageCount: number;
			/** Which task types already have results. */
			existingTypes: Set<EvolutionTaskType>;
		}

		let candidates: ActorCandidate[] = [];

		// ── Tier 1: kagami SQL graph — actors (OPTIONAL MATCH unsupported, fetch profiles) ──
		const gqHeaders = await authHeaders();
		const graphRes = await fetch(`${PDS}/xrpc/com.etzhayyim.kagami.sql`, {
			method: 'POST',
			headers: gqHeaders,
			credentials: 'include',
			signal: ac.signal,
			body: JSON.stringify({
				statement: `MATCH (p:Profile) WHERE p.did >= 'did:web:' AND p.did < 'did:web;' RETURN p.did AS did, p.display_name AS name, p.description AS desc ORDER BY p.created_at DESC LIMIT 20`,
				parameters: {},
			}),
		}).catch((error) => {
			console.warn('[silent-fail] evolution-tasks.svelte.ts: graph candidate fetch failed', error);
			return null;
		});

		if (graphRes?.ok) {
			const data = await graphRes.json();
			const rows: any[] = data?.rows ?? data?.results ?? data ?? [];
			for (const row of rows) {
				const did = String(row.did ?? '');
				if (!did || isDidOnCooldown(did)) continue;
				const existing = new Set<EvolutionTaskType>();
				if ((row.kyumei_count ?? 0) > 0) existing.add('kyumei');
				if ((row.shinka_count ?? 0) > 0) existing.add('shinka');
				if ((row.hinshitsu_count ?? 0) > 0) existing.add('hinshitsu');
				if ((row.knowledge_count ?? 0) > 0) existing.add('shinkaKnowledge');
				candidates.push({
					did,
					displayName: String(row.name ?? row.did?.split(':').pop() ?? ''),
					description: String(row.desc ?? ''),
					coverageCount: existing.size,
					existingTypes: existing,
				});
			}
		}

		// ── Tier 2: searchActors XRPC fallback ──
		if (candidates.length === 0) {
			const searchRes = await fetch(`${PDS}/xrpc/app.bsky.actor.searchActors?q=etzhayyim&limit=30`, {
				signal: ac.signal, credentials: 'include',
			}).catch((error) => {
				console.warn('[silent-fail] evolution-tasks.svelte.ts: searchActors fetch failed', error);
				return null;
			});
			if (searchRes?.ok) {
				const data = await searchRes.json();
				for (const a of (data?.actors ?? [])) {
					const did = String(a.did ?? '');
					if (!did || isDidOnCooldown(did)) continue;
					candidates.push({
						did,
						displayName: String(a.displayName || a.handle || ''),
						description: String(a.description || ''),
						coverageCount: 0,
						existingTypes: new Set(),
					});
				}
			}
		}

		// No synthetic seed — only real actors from graph

		if (candidates.length === 0) {
			// All actors on cooldown — wait for DID_COOLDOWN_MS to expire naturally.
			// Do NOT clear _processedDids; that causes the same actors to re-process.
			scheduleNext();
			return;
		}

		// Sort by coverage ascending — least covered first (keikaku priority)
		candidates.sort((a, b) => a.coverageCount - b.coverageCount);

		// Pick up to 3 actors per round
		const batch = candidates.slice(0, 3);
		for (const actor of batch) {
			markDidProcessed(actor.did);
			const name = actor.displayName || 'Unknown';
			const desc = actor.description || '';

			// Assign task types based on coverage gaps (keikaku: fill missing first)
			const ALL_TYPES: EvolutionTaskType[] = ['koji', 'kyumei', 'shinka', 'hinshitsu', 'shinkaKnowledge'];
			const missingTypes = ALL_TYPES.filter((t) => _activeTaskTypes.has(t) && !actor.existingTypes.has(t));
			// If all types covered, still run active types (refresh/re-evaluate)
			const typesToRun = missingTypes.length > 0 ? missingTypes : [..._activeTaskTypes];

			for (const taskType of typesToRun) {
				const taskId = `${taskType}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
				const task: EvolutionTask = {
					id: taskId,
					taskType,
					actorDid: actor.did,
					actorName: name,
					actorDescription: desc,
					status: 'queued',
					startedAt: null,
					completedAt: null,
					creditsEarned: 0,
					result: null,
					error: null,
				};
				_taskQueue = [task, ..._taskQueue].slice(0, MAX_QUEUE);
			}
		}

		// Start processing
		void processQueue();
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			console.warn('[evolution] keikaku error:', err);
		}
		scheduleNext();
	}
}

function scheduleNext(): void {
	if (_loopTimer) clearTimeout(_loopTimer);
	if (!_paused) {
		_loopTimer = setTimeout(() => void selfGenerateTasks(), TASK_COOLDOWN_MS);
	}
}

// ── Public API ──

/**
 * Wait for LLM to become ready using a single timer-based check.
 * Avoids setInterval accumulation — each iteration schedules one setTimeout.
 * Aborts after 90s to prevent indefinite waiting.
 */
async function waitForLLMReady(llm: ReturnType<typeof useLocalLLM>): Promise<boolean> {
	const maxWaitMs = 90_000;
	const start = Date.now();
	while (Date.now() - start < maxWaitMs) {
		if (llm.isReady) return true;
		if (llm.error) return false;
		if (_paused) return false;
		await new Promise((r) => setTimeout(r, 1000));
	}
	return false;
}

/**
 * Start the evolution task system. Triggers LLM load if not ready.
 *
 * Sets `_running = true` immediately so the UI reflects the state change
 * (button switches to "Stop"). If the LLM fails to load, resets to idle
 * with an error message instead of silently swallowing the failure.
 */
function start(taskTypes?: EvolutionTaskType[]): void {
	if (taskTypes) {
		_activeTaskTypes = new Set(taskTypes);
	}
	_paused = false;
	_running = true;
	_error = null;
	// Restore processed DIDs cooldown from localStorage (prevents repetition across reloads)
	restoreProcessedDids();
	// Restore persisted stats in background (non-blocking)
	void restoreFromGraph();
	// Ensure evolution runs inside a project convo context.
	void ensureEvolutionProjectConvo(false).then((convoId) => {
		if (convoId) {
			void sendProjectLogMessage('[Evolution] start requested. Queue orchestration begins now.');
		}
	});

	const llm = useLocalLLM();
	if (llm.state === 'idle') {
		void llm.init().then(
			() => {
				if (!_paused) void selfGenerateTasks();
			},
			(err) => {
				_running = false;
				_error = 'LLM failed to load: ' + (err instanceof Error ? err.message : String(err));
			},
		);
		return;
	}
	if (llm.isLoading) {
		void waitForLLMReady(llm).then((ready) => {
			if (ready && !_paused) void selfGenerateTasks();
			else {
				_running = false;
				_error = 'LLM failed to load: ' + (llm.error ?? 'timeout');
			}
		});
		return;
	}
	void selfGenerateTasks();
}

/** Create/reuse project convo for evolution and then start. Returns convoId when available. */
async function startInProject(taskTypes?: EvolutionTaskType[]): Promise<string | null> {
	if (taskTypes) _activeTaskTypes = new Set(taskTypes);
	const convoId = await ensureEvolutionProjectConvo(true);
	start(taskTypes);
	return convoId;
}

/** Stop all evolution tasks. */
function stop(): void {
	if (_loopTimer) { clearTimeout(_loopTimer); _loopTimer = null; }
	if (_abortController) { _abortController.abort(); _abortController = null; }
	_running = false;
	_paused = true;
	void sendProjectLogMessage('[Evolution] stopped.');
}

/** Toggle a specific task type on/off. */
function toggleTaskType(taskType: EvolutionTaskType, enabled: boolean): void {
	const next = new Set(_activeTaskTypes);
	if (enabled) next.add(taskType);
	else next.delete(taskType);
	_activeTaskTypes = next;
}

/** Check if a task type is active. */
function isTaskTypeActive(taskType: EvolutionTaskType): boolean {
	return _activeTaskTypes.has(taskType);
}

/** Get tasks filtered by type. */
function getTasksByType(taskType: EvolutionTaskType): EvolutionTask[] {
	return _taskQueue.filter((t) => t.taskType === taskType);
}

/** Get recent results filtered by type. */
function getResultsByType(taskType: EvolutionTaskType): EvolutionResult[] {
	return _recentResults.filter((r) => r.type === taskType);
}

export function useEvolutionTasks() {
	return {
		get isRunning() { return _running; },
		get isPaused() { return _paused; },
		get stats() { return _stats; },
		get taskQueue() { return _taskQueue; },
		get recentResults() { return _recentResults; },
		get error() { return _error; },
		get activeTaskTypes() { return _activeTaskTypes; },
		get projectConvoId() { return _projectConvoId; },
		/** Real-time inference log for chat-style UI. */
		get inferenceLog() { return _inferenceLog; },

		start,
		startInProject,
		ensureEvolutionProjectConvo,
		stop,
		toggleTaskType,
		isTaskTypeActive,
		getTasksByType,
		getResultsByType,
		/** Restore stats + recent results from kagami graph (idempotent, called once). */
		restoreFromGraph,
	};
}
