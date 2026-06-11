/**
 * browser-inference-state.svelte.ts — Svelte 5 reactive state for murakumo browser inference.
 *
 * Module-level singleton (`$state` at file scope) — state survives SvelteKit
 * route navigations. `join()` creates one `BrowserInferenceAgent` and sets
 * `_isJoined = true`; subsequent calls no-op. This prevents the WebSocket
 * gateway connection from being re-established on every page change.
 *
 * @module
 */

import { BrowserInferenceAgent, type AgentStats, type AgentState } from './browser-agent.js';
import { BROWSER_INFERENCE_MODELS, type BrowserInferenceModel } from './browser-gateway-client.js';

let _stats = $state<AgentStats>({
	state: 'idle',
	gatewayState: 'disconnected',
	transportType: 'websocket',
	sessionId: null,
	gpuTier: 'g0',
	gpuAdapter: 'unknown',
	memClass: 'mid',
	powerClass: 'desktop',
	cores: 1,
	jobsDone: 0,
	jobsFailed: 0,
	totalGpuTimeMs: 0,
	currentTaskId: null,
	lastHeartbeatAck: null,
});

let _isJoined = $state(false);
/** Selected model ID (default: smallest model). */
let _selectedModelId = $state<string>(BROWSER_INFERENCE_MODELS[0].id);
let agent: BrowserInferenceAgent | null = null;

function handleUpdate(stats: AgentStats) {
	_stats = stats;
}

export function useBrowserInference() {
	return {
		get stats() { return _stats; },
		get isJoined() { return _isJoined; },
		get isActive() { return _stats.state === 'connected' || _stats.state === 'executing'; },
		get isExecuting() { return _stats.state === 'executing'; },

		/** Available Qwen 3.5 models for browser inference. */
		get models(): readonly BrowserInferenceModel[] { return BROWSER_INFERENCE_MODELS; },
		/** Currently selected model ID. */
		get selectedModelId() { return _selectedModelId; },
		set selectedModelId(id: string) {
			if (BROWSER_INFERENCE_MODELS.some((m) => m.id === id)) _selectedModelId = id;
		},
		/** Currently selected model definition. */
		get selectedModel(): BrowserInferenceModel {
			return BROWSER_INFERENCE_MODELS.find((m) => m.id === _selectedModelId) ?? BROWSER_INFERENCE_MODELS[0];
		},

		async join(gatewayUrl?: string) {
			if (_isJoined) return;
			agent = new BrowserInferenceAgent(handleUpdate, gatewayUrl, _selectedModelId);
			await agent.start();
			_isJoined = true;
		},

		async leave() {
			if (!_isJoined || !agent) return;
			await agent.stop();
			agent = null;
			_isJoined = false;
		},
	};
}

export type { AgentStats, AgentState, BrowserInferenceModel };
