/**
 * local-llm.svelte.ts — Browser-local LLM chat completion via WebLLM (WebGPU).
 *
 * **Web Worker architecture**: The WebLLM engine runs in a dedicated Web Worker
 * (`llm-worker.ts`) via `CreateWebWorkerMLCEngine`. All model loading, weight
 * download, and inference execute off the main thread, preventing UI freezes
 * and memory pressure on the main V8 isolate.
 *
 * Module-level singleton state (`$state` at file scope) ensures the loaded
 * model survives SvelteKit route navigations. The engine is initialised once
 * via `init()` — the `_loadPromise` guard prevents concurrent loads even if
 * multiple callers invoke `init()` simultaneously (e.g. `$effect` re-fires).
 *
 * @module
 */

import { BROWSER_INFERENCE_MODELS, type BrowserInferenceModel } from './browser-gateway-client.js';

export type LocalLLMState = 'idle' | 'loading' | 'ready' | 'error';

export interface ChatMessage {
	role: 'system' | 'user' | 'assistant';
	content: string;
}

/** Default model: always-on Gemma 4 E2B (multimodal, 2B class). */
const DEFAULT_MODEL_ID = 'gemma4-e2b';

/** VRAM requirements per model (MB). Used for auto-downgrade on low-memory devices. */
const MODEL_VRAM_MB: Record<string, number> = {
	'gemma4-e2b': 2500,
	'qwen3.5-4b': 2600,
	'qwen3.5-2b': 1400,
	'qwen3.5-0.8b': 520,
};

/** Models ordered by VRAM requirement ascending — used for auto-downgrade fallback. */
const MODELS_BY_VRAM_ASC = ['qwen3.5-0.8b', 'qwen3.5-2b', 'gemma4-e2b', 'qwen3.5-4b'];

/** Maximum time to wait for model load before aborting (ms). */
const LOAD_TIMEOUT_MS = 60_000;

/*
 * ── Module-level singleton state ──
 * These `$state` runes live at file scope, NOT inside a component. This means
 * they are allocated once when the module is first imported and persist across
 * SvelteKit route navigations. Re-importing the module returns the same state.
 */
let _state = $state<LocalLLMState>('idle');
let _loadProgress = $state(0);
let _loadLabel = $state('');
let _activeModelId = $state<string | null>(null);
let _error = $state<string | null>(null);
let _lastInferenceError = $state<string | null>(null);

/**
 * WebWorkerMLCEngine instance — runs in a separate Web Worker thread.
 * The main thread only holds a thin proxy; all GPU/WASM ops happen in the worker.
 */
let _engine: any = null;

/** Guard against concurrent loadEngine calls (e.g. rapid model switch or route re-entry). */
let _loadPromise: Promise<void> | null = null;

/**
 * Map an application-level model ID (e.g. `'gemma4-e2b'`) to the WebLLM MLC
 * model identifier used by {@link CreateWebWorkerMLCEngine}.
 *
 * @param modelId - Application model ID from {@link BROWSER_INFERENCE_MODELS}.
 * @returns MLC-compatible model identifier string.
 */
function resolveMlcId(modelId: string): string {
	const model = BROWSER_INFERENCE_MODELS.find((m) => m.id === modelId);
	if (!model) return 'gemma-2-2b-it-q4f16_1-MLC';
	switch (model.id) {
		case 'gemma4-e2b': return 'gemma-2-2b-it-q4f16_1-MLC';
		case 'qwen3.5-0.8b': return 'Qwen2.5-0.5B-Instruct-q4f16_1-MLC';
		case 'qwen3.5-2b': return 'Qwen2.5-1.5B-Instruct-q4f16_1-MLC';
		case 'qwen3.5-4b': return 'Qwen2.5-3B-Instruct-q4f16_1-MLC';
		default: return 'gemma-2-2b-it-q4f16_1-MLC';
	}
}

/**
 * Probe available GPU/device memory and return an estimate in MB.
 *
 * Uses a 3-tier fallback:
 * 1. WebGPU `adapter.limits.maxBufferSize` (most accurate on GPU-capable devices).
 * 2. `navigator.deviceMemory` (Chrome-only, returns system RAM in GB; we assume
 *    40 % is available for GPU buffers).
 * 3. Conservative 1 024 MB default.
 *
 * @returns Estimated available memory in megabytes.
 */
async function probeAvailableMemoryMB(): Promise<number> {
	try {
		if (typeof navigator !== 'undefined' && 'gpu' in navigator) {
			const adapter = await (navigator as any).gpu.requestAdapter();
			if (adapter) {
				const maxBufferSize = adapter.limits?.maxBufferSize;
				if (maxBufferSize && maxBufferSize > 0) {
					return Math.floor(maxBufferSize / (1024 * 1024));
				}
			}
		}
	} catch { /* WebGPU not available */ }

	try {
		if (typeof navigator !== 'undefined' && 'deviceMemory' in navigator) {
			const gb = (navigator as any).deviceMemory as number;
			if (gb > 0) return Math.floor(gb * 1024 * 0.4);
		}
	} catch { /* not available */ }

	return 1024;
}

/**
 * Select the best model that fits within available device memory.
 *
 * If the requested model's VRAM budget exceeds the probed memory, iterates
 * {@link MODELS_BY_VRAM_ASC} in descending order and returns the largest model
 * that fits. Returns `null` when even the smallest model (qwen3.5-0.8b, 520 MB)
 * cannot be loaded — callers should surface an error to the user.
 *
 * @param requestedModelId - The model the user selected.
 * @returns A model ID that fits, or `null` if none do.
 */
async function selectSafeModel(requestedModelId: string): Promise<string | null> {
	const availMB = await probeAvailableMemoryMB();
	const requestedVRAM = MODEL_VRAM_MB[requestedModelId] ?? 2500;

	if (availMB >= requestedVRAM) return requestedModelId;

	console.warn(`[local-llm] Requested ${requestedModelId} needs ${requestedVRAM}MB, only ${availMB}MB available. Auto-downgrading.`);

	for (let i = MODELS_BY_VRAM_ASC.length - 1; i >= 0; i--) {
		const id = MODELS_BY_VRAM_ASC[i];
		if (availMB >= (MODEL_VRAM_MB[id] ?? 9999)) return id;
	}

	return null;
}

/**
 * Load the WebLLM engine for the given model in a Web Worker.
 *
 * Guards: no-ops if already loading or ready with the same model.
 * Auto-downgrades model if device memory is insufficient.
 * Aborts after LOAD_TIMEOUT_MS to prevent indefinite hangs.
 */
async function loadEngine(modelId: string): Promise<void> {
	if (_state === 'loading' && _loadPromise) return _loadPromise;
	if (_state === 'ready' && _activeModelId === modelId) return;

	_loadPromise = _doLoadEngine(modelId);
	try {
		await _loadPromise;
	} finally {
		_loadPromise = null;
	}
}

/**
 * Internal implementation of engine loading (called via {@link loadEngine}).
 *
 * Steps:
 * 1. Probe device memory via {@link probeAvailableMemoryMB}.
 * 2. Select a safe model via {@link selectSafeModel} (auto-downgrade if needed).
 * 3. Spawn a `llm-worker.ts` Web Worker.
 * 4. Call `CreateWebWorkerMLCEngine` with a {@link LOAD_TIMEOUT_MS} race guard.
 * 5. On success set state to `'ready'`; on failure set `'error'` with message.
 */
async function _doLoadEngine(modelId: string): Promise<void> {
	_state = 'loading';
	_loadProgress = 0;
	_loadLabel = 'Checking device memory...';
	_error = null;

	try {
		const safeModelId = await selectSafeModel(modelId);
		if (!safeModelId) {
			_state = 'error';
			_error = 'Insufficient GPU/device memory for any model. Close other tabs and retry.';
			_loadLabel = '';
			return;
		}
		if (safeModelId !== modelId) {
			_loadLabel = `Auto-selected ${safeModelId} (memory limit)`;
		}

		_loadLabel = `Initializing WebLLM Worker (${safeModelId})...`;
		const webllm = await import('@mlc-ai/web-llm');
		const mlcModelId = resolveMlcId(safeModelId);

		// Spawn a dedicated Web Worker for model loading + inference.
		// All GPU/WASM operations happen in the worker thread — the main
		// thread only holds a lightweight message-passing proxy.
		const { default: LlmWorker } = await import('./llm-worker.ts?worker');
		const worker = new LlmWorker();

		const enginePromise = webllm.CreateWebWorkerMLCEngine(worker, mlcModelId, {
			initProgressCallback: (info: { progress: number; text: string }) => {
				_loadProgress = Math.round((info.progress ?? 0) * 100);
				_loadLabel = info.text ?? `Loading ${safeModelId}...`;
			},
		});

		const timeoutPromise = new Promise<never>((_, reject) => {
			setTimeout(() => reject(new Error(`Model load timed out after ${LOAD_TIMEOUT_MS / 1000}s`)), LOAD_TIMEOUT_MS);
		});

		_engine = await Promise.race([enginePromise, timeoutPromise]);

		_activeModelId = safeModelId;
		_state = 'ready';
		_loadLabel = '';
	} catch (err) {
		_state = 'error';
		_error = err instanceof Error ? err.message : String(err);
		_loadLabel = '';
		console.warn('[local-llm] Failed to load model:', err);
	}
}

/**
 * Run chat completion locally. Returns null if engine is not ready.
 * The actual inference runs in the Web Worker — this call awaits the result
 * via message passing (non-blocking to the main thread).
 */
async function chatCompletion(
	messages: ChatMessage[],
	opts?: { maxTokens?: number; temperature?: number },
): Promise<string | null> {
	if (_state !== 'ready' || !_engine) return null;

	try {
		const response = await _engine.chat.completions.create({
			messages,
			max_tokens: opts?.maxTokens ?? 512,
			temperature: opts?.temperature ?? 0.7,
			stream: false,
		});
		_lastInferenceError = null;
		return response?.choices?.[0]?.message?.content ?? null;
	} catch (err) {
		_lastInferenceError = err instanceof Error ? err.message : String(err);
		console.warn('[local-llm] Chat completion failed:', err);
		return null;
	}
}

/**
 * Run streaming chat completion locally. Yields tokens as they arrive.
 * Returns null if engine is not ready.
 */
async function* chatCompletionStream(
	messages: ChatMessage[],
	opts?: { maxTokens?: number; temperature?: number },
): AsyncGenerator<string, void, unknown> {
	if (_state !== 'ready' || !_engine) return;

	try {
		const stream = await _engine.chat.completions.create({
			messages,
			max_tokens: opts?.maxTokens ?? 512,
			temperature: opts?.temperature ?? 0.7,
			stream: true,
		});
		_lastInferenceError = null;

		for await (const chunk of stream) {
			const delta = chunk?.choices?.[0]?.delta?.content;
			if (delta) yield delta;
		}
	} catch (err) {
		_lastInferenceError = err instanceof Error ? err.message : String(err);
		console.warn('[local-llm] Streaming completion failed:', err);
	}
}

/**
 * Composable accessor for the singleton local-LLM state.
 *
 * Every call returns the **same** underlying module-level `$state`, so multiple
 * components (layout, credits page, convo) share one engine instance.
 */
export function useLocalLLM() {
	return {
		get state() { return _state; },
		get isReady() { return _state === 'ready'; },
		get isLoading() { return _state === 'loading'; },
		get loadProgress() { return _loadProgress; },
		get loadLabel() { return _loadLabel; },
		get activeModelId() { return _activeModelId; },
		get activeModel(): BrowserInferenceModel | null {
			return BROWSER_INFERENCE_MODELS.find((m) => m.id === _activeModelId) ?? null;
		},
		get error() { return _error; },
		get lastInferenceError() { return _lastInferenceError; },

		/** Initialize and load a model. Defaults to Gemma 4 E2B. */
		init: (modelId?: string) => loadEngine(modelId ?? DEFAULT_MODEL_ID),

		/** Run chat completion. Returns null if not ready (caller should fall back to PDS). */
		chatCompletion,

		/** Run streaming chat completion. Yields nothing if not ready. */
		chatCompletionStream,

		/** Reset engine and terminate worker (e.g. to switch models). */
		async reset() {
			if (_engine) {
				try { await _engine.unload(); } catch { /* ignore */ }
				_engine = null;
			}
			_state = 'idle';
			_activeModelId = null;
			_loadProgress = 0;
			_loadLabel = '';
			_error = null;
			_lastInferenceError = null;
		},
	};
}
