/**
 * embedding.svelte.ts — Client-side text embedding via Transformers.js (Web Worker).
 *
 * Uses EmbeddingGemma-300m (Google, 768 dims, 100+ languages including
 * Japanese, Hindi, Chinese, Arabic). Gemma 3 backbone with bi-directional attention.
 * All embedding computation runs in the browser — zero server cost.
 * Server-side (Graph Worker) uses @cf/google/embeddinggemma-300m (same model, same dim).
 *
 * Module-level singleton state (`$state` at file scope) persists across
 * SvelteKit route navigations. The model is loaded once and cached in
 * Origin Private File System (OPFS) for instant subsequent loads.
 *
 * @module
 */

export type EmbeddingState = 'idle' | 'loading' | 'ready' | 'error';

/** Embedding model: EmbeddingGemma-300m (768 dims, 100+ langs, ONNX q8). */
const MODEL_ID = 'onnx-community/embeddinggemma-300m-ONNX';
const EMBEDDING_DIM = 768;

/** Module-level singleton state — survives route navigations. */
let _state = $state<EmbeddingState>('idle');
let _loadProgress = $state(0);
let _error = $state<string | null>(null);
let _pipeline: any = null;
let _loadPromise: Promise<void> | null = null;

/**
 * Initialize the embedding model. Idempotent — concurrent calls share the same load promise.
 *
 * Model weights are cached in OPFS after first download (~45MB).
 * Subsequent loads are near-instant (~100ms).
 */
async function init(): Promise<void> {
	if (_state === 'ready' || _state === 'loading') return _loadPromise ?? Promise.resolve();

	_loadPromise = (async () => {
		_state = 'loading';
		_loadProgress = 0;
		_error = null;

		try {
			const { pipeline, env } = await import('@huggingface/transformers');
			// Prefer WebGPU, fallback to WASM
			if (env.backends?.onnx?.wasm) env.backends.onnx.wasm.numThreads = 1;

			_pipeline = await pipeline('feature-extraction', MODEL_ID, {
				progress_callback: (p: { progress?: number; status?: string }) => {
					if (typeof p.progress === 'number') _loadProgress = Math.round(p.progress);
				},
			});

			_state = 'ready';
			_loadProgress = 100;
		} catch (err) {
			_state = 'error';
			_error = err instanceof Error ? err.message : String(err);
			console.error('[embedding] init failed:', err);
		}
	})();

	return _loadPromise;
}

/**
 * Generate embedding vector for text input.
 *
 * EmbeddingGemma uses bi-directional attention — no query/passage prefix needed.
 *
 * @param text - Input text
 * @param isQuery - Unused (kept for API compat). EmbeddingGemma doesn't need prefixes.
 * @returns 768-dimensional normalized embedding vector, or null if model not ready
 */
async function embed(text: string, _isQuery = false): Promise<number[] | null> {
	if (_state !== 'ready' || !_pipeline || !text.trim()) return null;

	try {
		const output = await _pipeline(text, { pooling: 'mean', normalize: true });
		const data: number[] = Array.from(output.data as Float32Array);
		if (data.length !== EMBEDDING_DIM) {
			console.warn(`[embedding] unexpected dim: ${data.length}, expected ${EMBEDDING_DIM}`);
			return null;
		}
		return data;
	} catch (err) {
		console.error('[embedding] embed failed:', err);
		return null;
	}
}

/**
 * Generate embeddings for multiple texts in sequence.
 *
 * @param texts - Input texts
 * @param isQuery - Unused (API compat)
 * @returns Array of 768-dim vectors (null entries on failure)
 */
async function embedBatch(texts: string[], isQuery = false): Promise<(number[] | null)[]> {
	const results: (number[] | null)[] = [];
	for (const text of texts) {
		results.push(await embed(text, isQuery));
	}
	return results;
}

/**
 * Svelte 5 composable for embedding state.
 *
 * Usage:
 * ```svelte
 * <script>
 *   const emb = useEmbedding();
 *   // Auto-init on first use
 *   $effect(() => { if (emb.state === 'idle') emb.init(); });
 *   // Embed text
 *   const vec = await emb.embed("半導体サプライチェーン", true);
 * </script>
 * ```
 */
export function useEmbedding() {
	return {
		get state() { return _state; },
		get loadProgress() { return _loadProgress; },
		get error() { return _error; },
		get isReady() { return _state === 'ready'; },
		get isLoading() { return _state === 'loading'; },
		get dim() { return EMBEDDING_DIM; },
		get modelId() { return MODEL_ID; },
		init,
		embed,
		embedBatch,
	};
}
