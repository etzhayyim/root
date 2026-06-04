/**
 * ameno.svelte.ts — Svelte 5 provider for @etzhayyim/ameno browser WebGPU inference.
 *
 * Wraps the @etzhayyim/ameno package (transformers.js ONNX + WebGPU LoRA merge +
 * RAG context injection) with Svelte 5 runes for reactive state management.
 *
 * Architecture: Dual-backend with local-llm.svelte.ts (WebLLM).
 *   - **Ameno (this)**: transformers.js ONNX, per-actor LoRA, RAG-LoRA context.
 *     Preferred for Gemma 4 E2B multimodal (text + image + audio).
 *   - **WebLLM**: MLC-compiled models, Web Worker. Preferred for Qwen 3.5 series.
 *
 * The caller (graph-rag, project convo, etc.) selects the backend based on the
 * active model: Gemma 4 E2B → ameno, Qwen 3.5 → WebLLM.
 *
 * @module
 */

import {
	checkWebGPU,
	getGPUInfo,
	loadModel,
	generate,
	setLoraAdapters,
	getActiveAdapterIds,
	type InferenceState,
	type ChatMessage as AmenoChatMessage,
	type GenerationStats,
} from '@etzhayyim/ameno/inference';

import {
	fetchLoraAdapter,
	applyLoraAdapters,
	type AdapterMergeSpec,
	type LoadedLoraAdapter,
} from '@etzhayyim/ameno/lora-runtime';

import {
	ragSearch,
	ragLoraSelect,
	buildRagContextPrompt,
	type RagResult,
	type RagLoraContext,
} from '@etzhayyim/ameno/rag-lora';

export type AmenoState = 'idle' | 'loading' | 'ready' | 'generating' | 'merging-lora' | 'error';

/** Re-export for consumers. */
export type { GenerationStats, RagResult, RagLoraContext, AdapterMergeSpec, LoadedLoraAdapter };

/*
 * ── Module-level singleton state ──
 * $state runes at file scope — persist across SvelteKit route navigations.
 */
let _state = $state<AmenoState>('idle');
let _loadProgress = $state(0);
let _webgpuAvailable = $state(false);
let _gpuInfo = $state('');
let _loadedModel = $state<string | null>(null);
let _error = $state<string | null>(null);
let _activeAdapters = $state<string[]>([]);
let _actorDid = $state<string | null>(null);
let _lastStats = $state<GenerationStats | null>(null);

/** Guard against concurrent load calls. */
let _loadPromise: Promise<void> | null = null;

/** Maximum time to wait for model load (ms). */
const LOAD_TIMEOUT_MS = 120_000;

/** Default ONNX model: Gemma 4 E2B IT (multimodal, 2.3B effective). */
const DEFAULT_MODEL = 'onnx-community/gemma-4-E2B-it-ONNX';

/**
 * Load the ameno inference engine with the specified ONNX model.
 *
 * Steps:
 * 1. Probe WebGPU availability.
 * 2. Download ONNX model from HuggingFace Hub (cached in browser storage).
 * 3. Initialize transformers.js pipeline with q4f16 quantization.
 *
 * @param modelId - HuggingFace ONNX model ID. Defaults to Gemma 4 E2B IT.
 */
async function init(modelId?: string): Promise<void> {
	if (_state === 'loading' && _loadPromise) return _loadPromise;
	if (_state === 'ready' && _loadedModel === (modelId ?? DEFAULT_MODEL)) return;

	_loadPromise = _doInit(modelId ?? DEFAULT_MODEL);
	try {
		await _loadPromise;
	} finally {
		_loadPromise = null;
	}
}

async function _doInit(modelId: string): Promise<void> {
	_state = 'loading';
	_loadProgress = 0;
	_error = null;

	try {
		// 1. WebGPU probe
		_webgpuAvailable = await checkWebGPU();
		if (!_webgpuAvailable) {
			_state = 'error';
			_error = 'WebGPU not available. Use a WebGPU-capable browser (Chrome 113+, Edge 113+).';
			return;
		}
		_gpuInfo = await getGPUInfo();

		// 2. Load ONNX model via transformers.js
		const timeoutPromise = new Promise<never>((_, reject) => {
			setTimeout(() => reject(new Error(`Model load timed out after ${LOAD_TIMEOUT_MS / 1000}s`)), LOAD_TIMEOUT_MS);
		});

		const loadPromise = loadModel(
			(progress) => { _loadProgress = progress; },
			modelId,
		);

		await Promise.race([loadPromise, timeoutPromise]);

		_loadedModel = modelId;
		_state = 'ready';
	} catch (err) {
		_state = 'error';
		_error = err instanceof Error ? err.message : String(err);
		console.warn('[ameno] Failed to load model:', err);
	}
}

/**
 * Run chat completion via ameno (transformers.js ONNX + WebGPU).
 *
 * Supports optional RAG context injection and per-actor LoRA adapters.
 * Returns null if the engine is not ready (caller should fall back to PDS).
 *
 * @param messages - OpenAI-compatible chat messages.
 * @param opts - Generation options.
 * @returns Generated text, or null if not ready.
 */
async function chatCompletion(
	messages: AmenoChatMessage[],
	opts?: {
		maxTokens?: number;
		ragContext?: RagResult[];
		ragTokenBudget?: number;
	},
): Promise<string | null> {
	if (_state !== 'ready') return null;

	_state = 'generating';
	try {
		let fullResponse = '';
		const stats = await generate(
			messages,
			(token) => { fullResponse += token; },
			{
				maxTokens: opts?.maxTokens ?? 1024,
				ragContext: opts?.ragContext,
				ragTokenBudget: opts?.ragTokenBudget ?? 2048,
			},
		);
		_lastStats = stats;
		_state = 'ready';
		return fullResponse;
	} catch (err) {
		_state = 'error';
		_error = err instanceof Error ? err.message : String(err);
		console.warn('[ameno] Generation failed:', err);
		return null;
	}
}

/**
 * Run streaming chat completion. Yields tokens as they arrive.
 *
 * @param messages - OpenAI-compatible chat messages.
 * @param opts - Generation options.
 */
async function* chatCompletionStream(
	messages: AmenoChatMessage[],
	opts?: {
		maxTokens?: number;
		ragContext?: RagResult[];
		ragTokenBudget?: number;
	},
): AsyncGenerator<string, void, unknown> {
	if (_state !== 'ready') return;

	_state = 'generating';
	try {
		const tokens: string[] = [];
		const stats = await generate(
			messages,
			(token) => { tokens.push(token); },
			{
				maxTokens: opts?.maxTokens ?? 1024,
				ragContext: opts?.ragContext,
				ragTokenBudget: opts?.ragTokenBudget ?? 2048,
			},
		);
		_lastStats = stats;
		_state = 'ready';

		for (const token of tokens) {
			yield token;
		}
	} catch (err) {
		_state = 'error';
		_error = err instanceof Error ? err.message : String(err);
		console.warn('[ameno] Streaming generation failed:', err);
	}
}

/**
 * Load per-actor LoRA adapters from R2 CDN and activate them.
 *
 * @param actorDid - Actor DID for adapter scoping.
 * @param adapterId - Adapter identifier.
 * @param pdsBaseUrl - PDS base URL for R2 fetch.
 */
async function loadActorAdapter(
	actorDid: string,
	adapterId: string,
	pdsBaseUrl = 'https://atproto.etzhayyim.com',
): Promise<LoadedLoraAdapter | null> {
	_state = 'merging-lora';
	_actorDid = actorDid;
	try {
		const adapter = await fetchLoraAdapter(actorDid, adapterId, pdsBaseUrl);
		setLoraAdapters([{ adapter, weight: 1.0 }]);
		_activeAdapters = getActiveAdapterIds();
		_state = 'ready';
		return adapter;
	} catch (err) {
		console.warn('[ameno] LoRA adapter load failed:', err);
		_state = 'ready';
		return null;
	}
}

/**
 * Clear all active LoRA adapters (revert to base model).
 */
function clearAdapters(): void {
	setLoraAdapters([]);
	_activeAdapters = [];
	_actorDid = null;
}

/**
 * Reset the ameno engine (unload model, clear state).
 */
function reset(): void {
	_state = 'idle';
	_loadedModel = null;
	_loadProgress = 0;
	_error = null;
	_activeAdapters = [];
	_actorDid = null;
	_lastStats = null;
	_loadPromise = null;
}

/**
 * Composable accessor for the singleton ameno inference state.
 *
 * Every call returns the same underlying module-level `$state`, so multiple
 * components share one engine instance.
 */
export function useAmeno() {
	return {
		// ── State ──
		get state() { return _state; },
		get isReady() { return _state === 'ready'; },
		get isLoading() { return _state === 'loading'; },
		get isGenerating() { return _state === 'generating'; },
		get loadProgress() { return _loadProgress; },
		get loadedModel() { return _loadedModel; },
		get webgpuAvailable() { return _webgpuAvailable; },
		get gpuInfo() { return _gpuInfo; },
		get error() { return _error; },
		get lastStats() { return _lastStats; },

		// ── LoRA state ──
		get activeAdapters() { return _activeAdapters; },
		get actorDid() { return _actorDid; },

		// ── Actions ──
		init,
		chatCompletion,
		chatCompletionStream,
		reset,

		// ── LoRA ──
		loadActorAdapter,
		clearAdapters,

		// ── RAG (re-export from @etzhayyim/ameno) ──
		ragSearch,
		ragLoraSelect,
		buildRagContextPrompt,
	};
}
