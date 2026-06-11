/**
 * local-diffusion.svelte.ts — Browser-local image generation via ONNX Runtime WebGPU.
 *
 * **Sequential load/unload architecture**: CLIP → UNet ×N → VAE run in a dedicated
 * Web Worker (`diffusion-worker.ts`). Only one model component occupies VRAM at a time,
 * so peak VRAM ≈ UNet alone (~1.7GB FP16). Same budget as Gemma 4 E2B.
 *
 * Module-level singleton state (`$state` at file scope) survives SvelteKit route
 * navigations. Same pattern as `local-llm.svelte.ts`.
 *
 * @module
 */

import { BROWSER_DIFFUSION_MODELS, type BrowserDiffusionModel } from './browser-gateway-client.js';
import type { DiffusionWorkerMessage } from './diffusion-worker.js';

export type DiffusionState = 'idle' | 'generating' | 'error';

export interface DiffusionProgress {
	stage: string;
	step: number;
	totalSteps: number;
	label: string;
}

export interface GenerateOpts {
	prompt: string;
	negativePrompt?: string;
	steps?: number;
	cfgScale?: number;
	seed?: number;
}

/* ── Module-level singleton state ── */

let _state = $state<DiffusionState>('idle');
let _progress = $state<DiffusionProgress | null>(null);
let _selectedModelId = $state<string>(BROWSER_DIFFUSION_MODELS[0].id);
let _lastImage = $state<ImageData | null>(null);
let _lastImageUrl = $state<string | null>(null);
let _error = $state<string | null>(null);
let _worker: Worker | null = null;
let _workerReady = false;

/**
 * Ensure the diffusion Web Worker is spawned and ready.
 * Reuses existing worker if already spawned.
 */
function ensureWorker(): Worker {
	if (_worker) return _worker;

	_worker = new Worker(
		new URL('./diffusion-worker.ts', import.meta.url),
		{ type: 'module' },
	);

	_worker.onmessage = (ev: MessageEvent<DiffusionWorkerMessage>) => {
		const msg = ev.data;
		switch (msg.type) {
			case 'ready':
				_workerReady = true;
				break;
			case 'progress':
				if (msg.progress) {
					_progress = {
						stage: msg.progress.stage,
						step: msg.progress.step,
						totalSteps: msg.progress.totalSteps,
						label: msg.progress.label,
					};
				}
				break;
			case 'image':
				if (msg.image) {
					const imageData = new ImageData(new Uint8ClampedArray(msg.image.data), msg.image.width, msg.image.height);
					_lastImage = imageData;

					// Convert to blob URL for <img> display
					const canvas = new OffscreenCanvas(msg.image.width, msg.image.height);
					const ctx = canvas.getContext('2d')!;
					ctx.putImageData(imageData, 0, 0);
					canvas.convertToBlob({ type: 'image/png' }).then((blob) => {
						if (_lastImageUrl) URL.revokeObjectURL(_lastImageUrl);
						_lastImageUrl = URL.createObjectURL(blob);
					});

					_state = 'idle';
					_progress = null;
				}
				break;
			case 'error':
				_state = 'error';
				_error = msg.error ?? 'Unknown diffusion error';
				_progress = null;
				break;
		}
	};

	_worker.onerror = (err) => {
		_state = 'error';
		_error = err.message || 'Worker error';
		_progress = null;
	};

	return _worker;
}

/**
 * Run image generation with the given prompt and options.
 *
 * Spawns the Web Worker on first call. All ONNX model loading, WebGPU shader
 * compilation, and denoising happen off the main thread.
 *
 * @returns Promise that resolves when generation completes (image in `lastImageUrl`).
 */
async function generate(opts: GenerateOpts): Promise<void> {
	if (_state === 'generating') return;

	const model = BROWSER_DIFFUSION_MODELS.find((m) => m.id === _selectedModelId) ?? BROWSER_DIFFUSION_MODELS[0];

	_state = 'generating';
	_error = null;
	_progress = { stage: 'scheduler', step: 0, totalSteps: opts.steps ?? model.defaultSteps, label: 'Initializing...' };

	const worker = ensureWorker();

	const msg: DiffusionWorkerMessage = {
		type: 'generate',
		params: {
			prompt: opts.prompt,
			negativePrompt: opts.negativePrompt ?? '',
			steps: opts.steps ?? model.defaultSteps,
			cfgScale: opts.cfgScale ?? model.defaultCfg,
			width: model.outputSize[0],
			height: model.outputSize[1],
			seed: opts.seed ?? Math.floor(Math.random() * 2147483647),
			cdnBase: model.cdnBase,
			clipPath: model.clipPath,
			unetPath: model.unetPath,
			unetWeightsPath: model.unetWeightsPath,
			vaePath: model.vaePath,
			tokenizerModel: model.tokenizerModel,
		},
	};

	worker.postMessage(msg);

	// Wait for completion (image or error)
	return new Promise<void>((resolve) => {
		const checkDone = setInterval(() => {
			if (_state !== 'generating') {
				clearInterval(checkDone);
				resolve();
			}
		}, 100);
	});
}

/**
 * Composable accessor for the singleton diffusion state.
 *
 * Mirrors the pattern of `useLocalLLM()` — every call returns the same
 * underlying module-level `$state`.
 */
export function useLocalDiffusion() {
	return {
		get state() { return _state; },
		get isGenerating() { return _state === 'generating'; },
		get progress() { return _progress; },
		get error() { return _error; },

		/** Available diffusion models. */
		get models() { return BROWSER_DIFFUSION_MODELS; },

		/** Currently selected model ID. */
		get selectedModelId() { return _selectedModelId; },
		set selectedModelId(id: string) {
			if (BROWSER_DIFFUSION_MODELS.some((m) => m.id === id)) _selectedModelId = id;
		},

		/** Currently selected model metadata. */
		get selectedModel(): BrowserDiffusionModel {
			return BROWSER_DIFFUSION_MODELS.find((m) => m.id === _selectedModelId) ?? BROWSER_DIFFUSION_MODELS[0];
		},

		/** Last generated image as blob URL (for `<img src>`). */
		get lastImageUrl() { return _lastImageUrl; },

		/** Last generated image as raw ImageData. */
		get lastImage() { return _lastImage; },

		/** Start image generation. */
		generate,

		/** Terminate worker and reset state. */
		reset() {
			if (_worker) {
				_worker.terminate();
				_worker = null;
				_workerReady = false;
			}
			_state = 'idle';
			_progress = null;
			_error = null;
			if (_lastImageUrl) {
				URL.revokeObjectURL(_lastImageUrl);
				_lastImageUrl = null;
			}
			_lastImage = null;
		},
	};
}
