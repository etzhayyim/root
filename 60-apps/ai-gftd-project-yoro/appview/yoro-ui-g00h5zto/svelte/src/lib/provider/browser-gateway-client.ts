/**
 * browser-gateway-client.ts — Multi-transport browser ↔ murakumo gateway.
 *
 * WebTransport (QUIC, preferred) → WebSocket (fallback).
 * Mirrors murakumo browser-gateway/protocol.go message protocol.
 */

export type MsgType =
	| 'register' | 'heartbeat' | 'taskResult' | 'taskFailed' | 'checkpoint' | 'bye'
	| 'registered' | 'taskPush' | 'taskCancel' | 'heartbeatAck' | 'error';

export interface Envelope {
	type: MsgType;
	register?: RegisterMsg;
	registered?: RegisteredMsg;
	heartbeat?: HeartbeatMsg;
	heartbeatAck?: HeartbeatAckMsg;
	taskPush?: TaskPushMsg;
	taskResult?: TaskResultMsg;
	taskFailed?: TaskFailedMsg;
	taskCancel?: TaskCancelMsg;
	checkpoint?: CheckpointMsg;
	error?: ErrorMsg;
}

/** Qwen 3.5 browser inference model definition. */
export interface BrowserInferenceModel {
	/** Model identifier (e.g. "qwen3.5-0.8b"). */
	id: string;
	/** Human-readable display name. */
	label: string;
	/** Parameter count in billions. */
	paramB: number;
	/** Approximate VRAM/RAM needed (Q4 quantized) in MB. */
	sizeMb: number;
	/** Minimum GPU tier required ("g0"=CPU, "g1"=WebGPU, "g2"=f16, etc.). */
	minGpuTier: string;
	/** WebLLM-compatible model repo path. */
	mlcModelId: string;
}

/** Available models for browser WebGPU inference. Gemma 4 E2B is the default (multimodal, 2B class). */
export const BROWSER_INFERENCE_MODELS: readonly BrowserInferenceModel[] = [
	{
		id: 'gemma4-e2b',
		label: 'Gemma 4 E2B',
		paramB: 2.3,
		sizeMb: 2500,
		minGpuTier: 'g2',
		mlcModelId: 'onnx-community/gemma-4-E2B-it-ONNX',
	},
	{
		id: 'qwen3.5-0.8b',
		label: 'Qwen 3.5 0.8B',
		paramB: 0.8,
		sizeMb: 520,
		minGpuTier: 'g1',
		mlcModelId: 'Qwen/Qwen3.5-0.8B-q4f16_1-MLC',
	},
	{
		id: 'qwen3.5-2b',
		label: 'Qwen 3.5 2B',
		paramB: 2,
		sizeMb: 1400,
		minGpuTier: 'g2',
		mlcModelId: 'Qwen/Qwen3.5-2B-q4f16_1-MLC',
	},
	{
		id: 'qwen3.5-4b',
		label: 'Qwen 3.5 4B',
		paramB: 4,
		sizeMb: 2600,
		minGpuTier: 'g3',
		mlcModelId: 'Qwen/Qwen3.5-4B-q4f16_1-MLC',
	},
] as const;

/** Browser-local diffusion model definition (Stable Diffusion variants). */
export interface BrowserDiffusionModel {
	/** Model identifier (e.g. "sd15-base"). */
	id: string;
	/** Human-readable display name. */
	label: string;
	/** Base architecture (e.g. "SD 1.5"). */
	arch: string;
	/** Total model size in MB (CLIP + UNet + VAE combined). Peak VRAM = UNet only (sequential load). */
	sizeMb: number;
	/** Minimum GPU tier required. */
	minGpuTier: string;
	/** CDN base URL for ONNX model files. */
	cdnBase: string;
	/** CLIP text encoder ONNX path relative to cdnBase. */
	clipPath: string;
	/** UNet denoiser ONNX path relative to cdnBase. */
	unetPath: string;
	/** UNet external weights path relative to cdnBase (null if single-file). */
	unetWeightsPath: string | null;
	/** VAE decoder ONNX path relative to cdnBase. */
	vaePath: string;
	/** CLIP tokenizer model ID for @huggingface/transformers AutoTokenizer. */
	tokenizerModel: string;
	/** Default number of denoising steps. */
	defaultSteps: number;
	/** Default guidance scale (CFG). */
	defaultCfg: number;
	/** Output image dimensions [width, height]. */
	outputSize: [number, number];
}

/**
 * Available models for browser-local image generation (WebGPU ONNX Runtime).
 *
 * Uses sequential load/unload strategy: CLIP → (unload) → UNet ×N steps → (unload) → VAE.
 * Peak VRAM = UNet alone (~1.7GB FP16). ONNX files hosted on R2 (cdn.etzhayyim.com).
 */
export const BROWSER_DIFFUSION_MODELS: readonly BrowserDiffusionModel[] = [
	{
		id: 'sd15-base',
		label: 'Stable Diffusion 1.5',
		arch: 'SD 1.5',
		sizeMb: 2400,
		minGpuTier: 'g2',
		cdnBase: 'https://cdn.etzhayyim.com/models/sd15',
		clipPath: 'text_encoder/model.onnx',
		unetPath: 'unet/model.onnx',
		unetWeightsPath: 'unet/weights.pb',
		vaePath: 'vae_decoder/model.onnx',
		tokenizerModel: 'openai/clip-vit-base-patch32',
		defaultSteps: 20,
		defaultCfg: 7.5,
		outputSize: [512, 512],
	},
] as const;

export interface BrowserCapability {
	'wasmSimd': boolean;
	'wasmThreads': boolean;
	gpu: {
		available: boolean;
		adapter: string;
		features: string[];
		'maxStorageBufferBindingSize': number;
		'maxComputeWorkgroupStorageSize': number;
	};
	'memClass': string;
	'netClass': string;
	'powerClass': string;
	'gpuTier': string;
	cores: number;
	'userAgent': string;
	/** Selected inference model for this session. */
	'inferenceModelId'?: string;
}

export interface RegisterMsg {
	capability: BrowserCapability;
	warmShards?: string[];
}

export interface RegisteredMsg {
	'sessionId': string;
	'gpuTier': string;
	'heartbeatIntervalSec': number;
}

export interface HeartbeatMsg {
	'sessionId': string;
	visibility: string;
	battery?: { charging: boolean; level: number };
	'heapPct': number;
	'shardMemoryMb': number;
	warmShards?: string[];
}

export interface HeartbeatAckMsg {
	'serverTime': string;
}

export interface TaskPushMsg {
	'leaseId': string;
	'taskId': string;
	'taskType': string;
	params: string;
	'checkpointIntervalSec': number;
	'timeoutSec': number;
	verificationMode?: string;
}

export interface TaskResultMsg {
	'leaseId': string;
	'taskId': string;
	output: string;
	'gpuTimeMs': number;
}

export interface TaskFailedMsg {
	'leaseId': string;
	'taskId': string;
	reason: string;
	error: string;
}

export interface TaskCancelMsg {
	'leaseId': string;
	'taskId': string;
	reason: string;
}

export interface CheckpointMsg {
	'leaseId': string;
	'taskId': string;
	iteration: number;
	stateB64?: string;
}

export interface ErrorMsg {
	code: string;
	message: string;
}

export interface DatagramProgress {
	'taskId': string;
	stage: string;
	done: number;
	total: number;
	detail?: string;
}

export type TransportType = 'webtransport' | 'websocket';
export type GatewayState = 'disconnected' | 'connecting' | 'registering' | 'connected' | 'reconnecting';

export interface GatewayCallbacks {
	onStateChange: (state: GatewayState) => void;
	onRegistered: (msg: RegisteredMsg) => void;
	onTaskPush: (msg: TaskPushMsg) => void;
	onTaskCancel: (msg: TaskCancelMsg) => void;
	onHeartbeatAck: (msg: HeartbeatAckMsg) => void;
	onError: (msg: ErrorMsg) => void;
}

const DEFAULT_RECONNECT_DELAY = 2000;
const MAX_RECONNECT_DELAY = 30000;

export class BrowserGatewayConnection {
	private ws: WebSocket | null = null;
	private state: GatewayState = 'disconnected';
	private gatewayUrl: string;
	private callbacks: GatewayCallbacks;
	private capability: BrowserCapability | null = null;
	private sessionId: string | null = null;
	private heartbeatIntervalSec = 15;
	private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
	private reconnectDelay = DEFAULT_RECONNECT_DELAY;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	private intentionalClose = false;
	private warmShards: string[] = [];
	private activeTransport: TransportType = 'websocket';

	constructor(gatewayUrl: string, callbacks: GatewayCallbacks) {
		this.gatewayUrl = gatewayUrl;
		this.callbacks = callbacks;
	}

	get connected(): boolean {
		return this.state === 'connected';
	}

	get currentSessionId(): string | null {
		return this.sessionId;
	}

	get transportType(): TransportType {
		return this.activeTransport;
	}

	connect(capability: BrowserCapability): void {
		this.capability = capability;
		this.intentionalClose = false;
		this.doConnect();
	}

	disconnect(): void {
		this.intentionalClose = true;
		this.cleanup();
		this.setState('disconnected');
	}

	sendResult(msg: TaskResultMsg): void {
		this.send({ type: 'taskResult', 'taskResult': msg });
	}

	sendFailure(msg: TaskFailedMsg): void {
		this.send({ type: 'taskFailed', 'taskFailed': msg });
	}

	sendProgress(progress: DatagramProgress): void {
		// Progress is best-effort (no-op on WebSocket)
	}

	setWarmShards(shards: string[]): void {
		this.warmShards = shards;
	}

	private doConnect(): void {
		this.cleanup();
		this.setState('connecting');
		this.activeTransport = 'websocket';

		const ws = new WebSocket(this.gatewayUrl);
		this.ws = ws;

		ws.onopen = () => {
			this.setState('registering');
			if (this.capability) {
				this.send({
					type: 'register',
					register: { capability: this.capability, 'warmShards': this.warmShards },
				});
			}
		};

		ws.onmessage = (ev) => {
			try {
				this.handleMessage(JSON.parse(ev.data));
			} catch {
				// malformed message
			}
		};

		ws.onclose = () => {
			this.stopHeartbeat();
			if (!this.intentionalClose) {
				this.setState('reconnecting');
				this.scheduleReconnect();
			}
		};

		ws.onerror = () => {};
	}

	private handleMessage(env: Envelope): void {
		switch (env.type) {
			case 'registered':
				if (env.registered) {
					this.sessionId = env.registered.sessionId;
					this.heartbeatIntervalSec = env.registered.heartbeatIntervalSec || 15;
					this.reconnectDelay = DEFAULT_RECONNECT_DELAY;
					this.setState('connected');
					this.startHeartbeat();
					this.callbacks.onRegistered(env.registered);
				}
				break;
			case 'taskPush':
				if (env.taskPush) this.callbacks.onTaskPush(env.taskPush);
				break;
			case 'taskCancel':
				if (env.taskCancel) this.callbacks.onTaskCancel(env.taskCancel);
				break;
			case 'heartbeatAck':
				if (env.heartbeatAck) this.callbacks.onHeartbeatAck(env.heartbeatAck);
				break;
			case 'error':
				if (env.error) this.callbacks.onError(env.error);
				break;
		}
	}

	private send(env: Envelope): void {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify(env));
		}
	}

	private startHeartbeat(): void {
		this.stopHeartbeat();
		this.heartbeatTimer = setInterval(() => {
			if (!this.sessionId) return;
			const perf = typeof performance !== 'undefined' && (performance as any).memory;
			const heapPct = perf && perf.totalJSHeapSize > 0
				? Math.round(perf.usedJSHeapSize / perf.totalJSHeapSize * 100) : 0;

			const msg: HeartbeatMsg = {
				'sessionId': this.sessionId,
				visibility: typeof document !== 'undefined' ? document.visibilityState : 'visible',
				'heapPct': heapPct,
				'shardMemoryMb': 0,
				'warmShards': this.warmShards,
			};

			if (typeof navigator !== 'undefined' && 'getBattery' in navigator) {
				(navigator as any).getBattery().then((b: any) => {
					msg.battery = { charging: b.charging, level: b.level };
					this.send({ type: 'heartbeat', heartbeat: msg });
				}).catch((_err: unknown) => {
					this.send({ type: 'heartbeat', heartbeat: msg });
				});
			} else {
				this.send({ type: 'heartbeat', heartbeat: msg });
			}
		}, this.heartbeatIntervalSec * 1000);
	}

	private stopHeartbeat(): void {
		if (this.heartbeatTimer) {
			clearInterval(this.heartbeatTimer);
			this.heartbeatTimer = null;
		}
	}

	private scheduleReconnect(): void {
		if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
		this.reconnectTimer = setTimeout(() => {
			this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, MAX_RECONNECT_DELAY);
			this.doConnect();
		}, this.reconnectDelay);
	}

	private cleanup(): void {
		this.stopHeartbeat();
		if (this.reconnectTimer) {
			clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}
		if (this.ws) {
			this.send({ type: 'bye' });
			if (this.ws.readyState === WebSocket.OPEN) {
				this.ws.close(1000, 'bye');
			}
			this.ws.onopen = null;
			this.ws.onmessage = null;
			this.ws.onclose = null;
			this.ws.onerror = null;
			this.ws = null;
		}
		this.sessionId = null;
	}

	private setState(state: GatewayState): void {
		this.state = state;
		this.callbacks.onStateChange(state);
	}
}
