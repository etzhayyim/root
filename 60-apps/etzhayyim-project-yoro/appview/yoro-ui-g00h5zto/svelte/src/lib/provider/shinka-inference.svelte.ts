/**
 * shinka-inference.svelte.ts — Murakumo-driven shinka/heartbeat inference via browser LLM.
 *
 * Module-level singleton (`$state` at file scope) — state persists across
 * SvelteKit route navigations. The `+layout.svelte` calls `start()` once
 * (3 s after the local LLM Web Worker becomes ready), using `untrack` on
 * `isRunning` to prevent a reactive start→cleanup-stop→start infinite loop.
 *
 * Architecture:
 *   murakumo.etzhayyim.com scheduler → browser-gateway WS → taskPush
 *   → local LLM Web Worker (`llm-worker.ts`, off main thread)
 *   → taskResult → murakumo → PDS record + credit earn
 *
 * All LLM inference runs in a dedicated Web Worker via
 * `CreateWebWorkerMLCEngine`, so model loading and token generation never
 * block the main thread or trigger OOM on the UI V8 isolate.
 *
 * Task flow visible on /credits as a queue:
 *   [queued] → [executing] → [completed +0.1cr] or [failed]
 *
 * @module
 */

import { useLocalLLM, type ChatMessage } from './local-llm.svelte.js';
import { getSessionToken } from '$lib/auth';

const PDS = 'https://atproto.etzhayyim.com';

/**
 * Build authenticated headers for PDS XRPC calls.
 * Uses Passkey session JWT (Bearer token). Falls back to Content-Type only.
 */
async function authHeaders(): Promise<Record<string, string>> {
	const token = await getSessionToken().catch((err) => {
		console.warn('[shinka] getSessionToken failed', err);
		return null;
	});
	const h: Record<string, string> = { 'Content-Type': 'application/json' };
	if (token) h['Authorization'] = `Bearer ${token}`;
	return h;
}

export type ShinkaState = 'idle' | 'running' | 'paused' | 'error';

/** A task received from murakumo gateway or self-generated. */
export interface ShinkaTask {
	id: string;
	leaseId: string;
	taskType: 'shinkaInference' | 'heartbeatInference' | 'llmInference' | 'joucho';
	actorDid: string;
	actorName: string;
	params: Record<string, unknown>;
	status: 'queued' | 'executing' | 'completed' | 'failed';
	creditsEarned: number;
	startedAt: number | null;
	completedAt: number | null;
	result: ShinkaResult | null;
	error: string | null;
}

/** Single shinka inference result. */
export interface ShinkaResult {
	actorDid: string;
	actorName: string;
	joucho: { joy: number; calm: number; stress: number; gratitude: number; focus: number };
	mood: string;
	suggestion: string;
	inferredAt: string;
	tokensUsed: number;
}

/** Cumulative stats for the current session. */
export interface ShinkaStats {
	jobsCompleted: number;
	jobsFailed: number;
	creditsEarned: number;
	tokensGenerated: number;
	lastInferredActor: string | null;
	lastInferredAt: string | null;
}

let _state = $state<ShinkaState>('idle');
let _stats = $state<ShinkaStats>({
	jobsCompleted: 0,
	jobsFailed: 0,
	creditsEarned: 0,
	tokensGenerated: 0,
	lastInferredActor: null,
	lastInferredAt: null,
});
let _taskQueue = $state<ShinkaTask[]>([]);
let _recentResults = $state<ShinkaResult[]>([]);
let _error = $state<string | null>(null);
let _abortController: AbortController | null = null;
let _loopTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Actors processed with timestamps. Persisted to localStorage to prevent
 * re-inferring the same actors across page reloads.
 */
const _processedDids = new Map<string, number>();
/** Cooldown before re-processing a DID (ms). */
const SHINKA_DID_COOLDOWN_MS = 30 * 60_000;
const SHINKA_PROCESSED_KEY = 'yoro-shinka-processed-dids';

/** Credit reward per inference job. */
const CREDIT_PER_JOB = 0.1;
/** Cooldown for self-generated tasks when no murakumo tasks available (ms). */
const SELF_GEN_COOLDOWN_MS = 60_000;
/** Max tasks in queue display. */
const MAX_QUEUE = 30;
/** Max recent results to keep. */
const MAX_RECENT = 20;
/** Max completed/failed tasks to keep in queue. */
const MAX_DONE_IN_QUEUE = 8;

/** Restore shinka _processedDids from localStorage. */
function restoreShinkaProcessedDids(): void {
	if (typeof window === 'undefined') return;
	try {
		const raw = localStorage.getItem(SHINKA_PROCESSED_KEY);
		if (!raw) return;
		const entries: [string, number][] = JSON.parse(raw);
		const now = Date.now();
		for (const [did, ts] of entries) {
			if (now - ts < SHINKA_DID_COOLDOWN_MS) _processedDids.set(did, ts);
		}
	} catch { /* corrupt */ }
}

/** Save shinka _processedDids to localStorage. */
function saveShinkaProcessedDids(): void {
	try {
		const now = Date.now();
		const entries: [string, number][] = [];
		for (const [did, ts] of _processedDids) {
			if (now - ts < SHINKA_DID_COOLDOWN_MS) entries.push([did, ts]);
		}
		localStorage.setItem(SHINKA_PROCESSED_KEY, JSON.stringify(entries));
	} catch { /* quota */ }
}

/** Check if a DID is on shinka cooldown. */
function isShinkaCooldown(did: string): boolean {
	const ts = _processedDids.get(did);
	if (!ts) return false;
	if (Date.now() - ts >= SHINKA_DID_COOLDOWN_MS) {
		_processedDids.delete(did);
		return false;
	}
	return true;
}

/** Prune completed/failed tasks from queue. */
function pruneShinkaQueue(): void {
	const done = _taskQueue.filter((t) => t.status === 'completed' || t.status === 'failed');
	if (done.length <= MAX_DONE_IN_QUEUE) return;
	const toRemove = new Set(done.slice(MAX_DONE_IN_QUEUE).map((t) => t.id));
	_taskQueue = _taskQueue.filter((t) => !toRemove.has(t.id));
}

/**
 * Enqueue a task from murakumo gateway push.
 * Called by browser-agent when it receives a shinka/heartbeat/llmInference task.
 */
function enqueueGatewayTask(
	taskId: string,
	leaseId: string,
	taskType: string,
	params: Record<string, unknown>,
): void {
	const actorDid = (params.actorDid as string) || (params.did as string) || '';
	const actorName = (params.actorName as string) || (params.displayName as string) || actorDid.split(':').pop() || 'Unknown';

	const task: ShinkaTask = {
		id: taskId,
		leaseId,
		taskType: taskType as ShinkaTask['taskType'],
		actorDid,
		actorName,
		params,
		status: 'queued',
		creditsEarned: 0,
		startedAt: null,
		completedAt: null,
		result: null,
		error: null,
	};

	_taskQueue = [task, ..._taskQueue].slice(0, MAX_QUEUE);

	// Auto-process if not already running
	if (_state !== 'running') {
		void processQueue();
	}
}

/**
 * Run joucho shinka inference on an actor using local LLM.
 */
async function inferShinka(
	actorDid: string,
	actorName: string,
	description: string,
	llm: ReturnType<typeof useLocalLLM>,
): Promise<ShinkaResult | null> {
	const systemPrompt = `You are a joucho (情緒) analyst for AI Agent social evolution (shinka 進化).
Analyze the actor and infer current emotional state on 5 axes (0-100):
- joy (喜び), calm (落ち着き), stress (ストレス), gratitude (感謝), focus (集中力)
Determine mood (joyful/calm/stressed/grateful/focused/neutral) and suggest one evolution step.
Respond JSON only: {"joy":N,"calm":N,"stress":N,"gratitude":N,"focus":N,"mood":"...","suggestion":"..."}`;

	const messages: ChatMessage[] = [
		{ role: 'system', content: systemPrompt },
		{ role: 'user', content: `Actor: ${actorName}\nDID: ${actorDid}\nDescription: ${description || 'No description'}` },
	];

	const raw = await llm.chatCompletion(messages, { maxTokens: 256, temperature: 0.6 });
	if (!raw) return null;

	const tokensUsed = Math.ceil(raw.length / 4) + 80;
	try {
		const jsonMatch = raw.match(/\{[\s\S]*\}/);
		if (!jsonMatch) return null;
		const parsed = JSON.parse(jsonMatch[0]);
		const clamp = (v: unknown) => Math.max(0, Math.min(100, Number(v) || 50));

		return {
			actorDid,
			actorName,
			joucho: {
				joy: clamp(parsed.joy), calm: clamp(parsed.calm), stress: clamp(parsed.stress),
				gratitude: clamp(parsed.gratitude), focus: clamp(parsed.focus),
			},
			mood: parsed.mood || 'neutral',
			suggestion: parsed.suggestion || '',
			inferredAt: new Date().toISOString(),
			tokensUsed,
		};
	} catch {
		return null;
	}
}

/**
 * Persist result to PDS and earn credits.
 */
async function persistAndEarn(result: ShinkaResult, signal: AbortSignal): Promise<boolean> {
	try {
		const headers = await authHeaders();

		// Write shinka inference record
		await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
			method: 'POST',
			headers,
			signal,
			body: JSON.stringify({
				collection: 'com.etzhayyim.apps.yoro.shinkaInference',
				record: {
					actorDid: result.actorDid, actorName: result.actorName,
					joucho: result.joucho, mood: result.mood,
					suggestion: result.suggestion, tokensUsed: result.tokensUsed,
					model: 'gemma4-e2b', source: 'browser',
					createdAt: result.inferredAt,
				},
			}),
		});

		// Earn credits (Design E Tier 2)
		await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
			method: 'POST',
			headers,
			signal,
			body: JSON.stringify({
				collection: 'com.etzhayyim.apps.credits.creditTransaction',
				record: {
					type: 'earn', amount: CREDIT_PER_JOB,
					source: 'murakumo', contributionType: 'browser_inference',
					description: `Shinka inference for ${result.actorName}`,
					createdAt: result.inferredAt,
				},
			}),
		});

		return true;
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			console.warn('[shinka] persist/earn failed:', err);
		}
		return false;
	}
}

/**
 * Process the next queued task.
 */
async function processQueue(): Promise<void> {
	const llm = useLocalLLM();
	if (!llm.isReady) {
		_state = 'paused';
		scheduleNext();
		return;
	}

	const nextTask = _taskQueue.find(t => t.status === 'queued');
	if (!nextTask) {
		// No gateway tasks — try self-generating
		await selfGenerateTask();
		return;
	}

	_state = 'running';
	const ac = new AbortController();
	_abortController = ac;

	// Mark executing
	nextTask.status = 'executing';
	nextTask.startedAt = Date.now();
	_taskQueue = [..._taskQueue];

	try {
		const description = (nextTask.params.description as string) || '';
		const result = await inferShinka(nextTask.actorDid, nextTask.actorName, description, llm);
		if (ac.signal.aborted) return;

		if (result) {
			const earned = await persistAndEarn(result, ac.signal);
			nextTask.status = 'completed';
			nextTask.completedAt = Date.now();
			nextTask.result = result;
			nextTask.creditsEarned = earned ? CREDIT_PER_JOB : 0;

			_stats = {
				jobsCompleted: _stats.jobsCompleted + 1,
				jobsFailed: _stats.jobsFailed,
				creditsEarned: _stats.creditsEarned + (earned ? CREDIT_PER_JOB : 0),
				tokensGenerated: _stats.tokensGenerated + result.tokensUsed,
				lastInferredActor: result.actorName,
				lastInferredAt: result.inferredAt,
			};
			_recentResults = [result, ..._recentResults].slice(0, MAX_RECENT);
			_error = null;
		} else {
			nextTask.status = 'failed';
			nextTask.completedAt = Date.now();
			nextTask.error = 'Inference returned null';
			_stats = { ..._stats, jobsFailed: _stats.jobsFailed + 1 };
		}
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			nextTask.status = 'failed';
			nextTask.completedAt = Date.now();
			nextTask.error = (err as Error).message;
			_stats = { ..._stats, jobsFailed: _stats.jobsFailed + 1 };
			_error = (err as Error).message;
		}
	}

	_taskQueue = [..._taskQueue];

	// Prune completed tasks to cap mobile memory
	pruneShinkaQueue();

	// Use setTimeout(0) instead of recursion to break call stack on mobile
	if (_taskQueue.some(t => t.status === 'queued')) {
		setTimeout(() => void processQueue(), 0);
	} else {
		scheduleNext();
	}
}

/**
 * Self-generate a shinka task when no murakumo tasks are available.
 * Fetches actors from PDS and creates inference tasks.
 */
async function selfGenerateTask(): Promise<void> {
	_state = 'running';
	const ac = new AbortController();
	_abortController = ac;

	try {
		const res = await fetch(`${PDS}/xrpc/app.bsky.actor.searchActors?q=etzhayyim&limit=50`, {
			signal: ac.signal, credentials: 'include',
		});
		if (!res.ok) { scheduleNext(); return; }
		const data = await res.json();
		const actors = (data?.actors ?? []).filter((a: any) => a.did && !isShinkaCooldown(a.did));

		if (actors.length === 0) {
			// All actors on cooldown — wait for expiry. Do NOT clear.
			scheduleNext();
			return;
		}

		const actor = actors[0];
		_processedDids.set(actor.did, Date.now());
		saveShinkaProcessedDids();

		// Create as a queued task for visibility
		const taskId = `self-${Date.now().toString(36)}`;
		enqueueGatewayTask(taskId, taskId, 'shinkaInference', {
			actorDid: actor.did,
			actorName: actor.displayName || actor.handle || 'Unknown',
			description: actor.description || '',
		});
	} catch (err) {
		if ((err as Error).name !== 'AbortError') {
			console.warn('[shinka] self-gen error:', err);
		}
		scheduleNext();
	}
}

function scheduleNext(): void {
	if (_loopTimer) clearTimeout(_loopTimer);
	_loopTimer = setTimeout(() => void selfGenerateTask(), SELF_GEN_COOLDOWN_MS);
}

/**
 * Start the shinka inference system.
 * Sets `_state = 'running'` immediately for UI feedback.
 */
function start(): void {
	if (_state === 'running') return;
	_state = 'running';
	_error = null;
	restoreShinkaProcessedDids();
	void selfGenerateTask();
}

/** Stop the shinka inference system. */
function stop(): void {
	if (_loopTimer) { clearTimeout(_loopTimer); _loopTimer = null; }
	if (_abortController) { _abortController.abort(); _abortController = null; }
	_state = 'idle';
}

/**
 * Execute a murakumo gateway task using local LLM.
 * Returns the inference result as JSON string for the gateway taskResult.
 * Called by browser-agent for llmInference/shinkaInference/heartbeatInference tasks.
 */
async function executeGatewayTask(
	taskId: string,
	leaseId: string,
	taskType: string,
	params: Record<string, unknown>,
): Promise<string> {
	const llm = useLocalLLM();
	if (!llm.isReady) throw new Error('Local LLM not ready');

	// Enqueue for visibility on /credits
	enqueueGatewayTask(taskId, leaseId, taskType, params);

	// Find the task we just enqueued
	const task = _taskQueue.find(t => t.id === taskId);

	if (taskType === 'shinkaInference' || taskType === 'heartbeatInference' || taskType === 'joucho') {
		const actorDid = (params.actorDid as string) || (params.did as string) || '';
		const actorName = (params.actorName as string) || (params.displayName as string) || '';
		const description = (params.description as string) || '';

		const result = await inferShinka(actorDid, actorName, description, llm);
		if (!result) throw new Error('Inference returned null');

		// Update task state
		if (task) {
			task.status = 'completed';
			task.completedAt = Date.now();
			task.result = result;
			task.creditsEarned = CREDIT_PER_JOB;
			_taskQueue = [..._taskQueue];
		}

		// Persist + earn credits in background
		void persistAndEarn(result, new AbortController().signal);

		_stats = {
			jobsCompleted: _stats.jobsCompleted + 1,
			jobsFailed: _stats.jobsFailed,
			creditsEarned: _stats.creditsEarned + CREDIT_PER_JOB,
			tokensGenerated: _stats.tokensGenerated + result.tokensUsed,
			lastInferredActor: result.actorName,
			lastInferredAt: result.inferredAt,
		};
		_recentResults = [result, ..._recentResults].slice(0, MAX_RECENT);

		return JSON.stringify(result);
	}

	// Generic LLM inference (converse, etc.)
	const messages: ChatMessage[] = (params.messages as ChatMessage[]) || [
		{ role: 'user', content: (params.prompt as string) || (params.input as string) || '' },
	];
	const raw = await llm.chatCompletion(messages, {
		maxTokens: (params.maxTokens as number) || 512,
		temperature: (params.temperature as number) || 0.7,
	});
	if (!raw) throw new Error('LLM returned null');

	if (task) {
		task.status = 'completed';
		task.completedAt = Date.now();
		task.creditsEarned = CREDIT_PER_JOB;
		_taskQueue = [..._taskQueue];
	}

	_stats = {
		..._stats,
		jobsCompleted: _stats.jobsCompleted + 1,
		creditsEarned: _stats.creditsEarned + CREDIT_PER_JOB,
		tokensGenerated: _stats.tokensGenerated + Math.ceil(raw.length / 4),
	};

	return JSON.stringify({ content: raw, model: 'gemma4-e2b' });
}

export function useShinkaInference() {
	return {
		get state() { return _state; },
		get isRunning() { return _state === 'running'; },
		get stats() { return _stats; },
		get taskQueue() { return _taskQueue; },
		get recentResults() { return _recentResults; },
		get error() { return _error; },

		start,
		stop,
		/** Enqueue a gateway task for processing. */
		enqueueGatewayTask,
		/** Execute a gateway task and return result (for browser-agent integration). */
		executeGatewayTask,
	};
}

