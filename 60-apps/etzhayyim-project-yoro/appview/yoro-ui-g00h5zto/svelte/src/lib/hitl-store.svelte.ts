/**
 * Background poller for LangGraph interrupted threads (HITL decision inbox).
 * Calls the Yoro Worker proxy at /api/hitl/* — never the LangGraph server directly.
 * The HITL_API_KEY is the operator's bearer token stored in localStorage.
 */
import { browser } from '$app/environment';

export const HITL_TOKEN_KEY = 'etzhayyim:hitl-api-key';
const POLL_MS = 10_000;

function createHitlStore() {
	let pendingCount = $state(0);
	let pregelPendingCount = $state(0);
	let timer: ReturnType<typeof setInterval> | null = null;

	function token(): string {
		if (!browser) return '';
		try { return localStorage.getItem(HITL_TOKEN_KEY) ?? ''; } catch { return ''; }
	}

	function hitlHeaders(): HeadersInit {
		const t = token();
		return t ? { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` } : { 'Content-Type': 'application/json' };
	}

	async function poll() {
		try {
			const res = await fetch('/api/hitl/threads/search', {
				method: 'POST',
				headers: hitlHeaders(),
				body: JSON.stringify({ status: 'interrupted', limit: 50 }),
				signal: AbortSignal.timeout(5000),
			});
			if (res.status === 401 || res.status === 503) { pendingCount = 0; return; }
			if (!res.ok) { pendingCount = 0; return; }
			const list: unknown[] = await res.json();
			pendingCount = Array.isArray(list) ? list.length : 0;
		} catch {
			// proxy unreachable — keep last count silently
		}
	}

	async function pollPregel() {
		try {
			const res = await fetch('/api/pregel/threads/search', {
				method: 'POST',
				headers: hitlHeaders(),
				body: JSON.stringify({ status: 'interrupted', limit: 50 }),
				signal: AbortSignal.timeout(5000),
			});
			if (res.status === 401 || res.status === 503) { pregelPendingCount = 0; return; }
			if (!res.ok) { pregelPendingCount = 0; return; }
			const list: unknown[] = await res.json();
			pregelPendingCount = Array.isArray(list) ? list.length : 0;
		} catch {
			// pregel proxy unreachable — keep last count silently
		}
	}

	function start() {
		if (!browser || timer !== null) return;
		void poll();
		void pollPregel();
		timer = setInterval(() => { void poll(); void pollPregel(); }, POLL_MS);
	}

	function stop() {
		if (timer !== null) { clearInterval(timer); timer = null; }
	}

	return {
		get pending() { return pendingCount; },
		get pregelPending() { return pregelPendingCount; },
		get token() { return token(); },
		start,
		stop,
		poll,
		pollPregel,
		hitlHeaders,
	};
}

export const hitl = createHitlStore();
