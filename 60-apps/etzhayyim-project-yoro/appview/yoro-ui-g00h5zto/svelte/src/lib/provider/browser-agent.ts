/**
 * browser-agent.ts — Browser inference agent for murakumo.etzhayyim.com gateway.
 *
 * 1. Probes GPU/memory/battery capabilities
 * 2. Connects to murakumo browser-gateway via WebSocket
 * 3. Spawns a Web Worker for inference execution (off main thread)
 * 4. Receives push-based tasks from gateway, dispatches to executor
 */

import {
	BrowserGatewayConnection,
	type GatewayState,
	type TransportType,
	type RegisteredMsg,
	type TaskPushMsg,
	type TaskCancelMsg,
	type HeartbeatAckMsg,
	type ErrorMsg,
	type BrowserCapability,
} from './browser-gateway-client.js';
import { probeCapabilities } from './capability-probe.js';
import { useShinkaInference } from './shinka-inference.svelte.js';
import type {
	TaskExecRequest,
	TaskExecProgress,
	TaskExecResult,
	TaskExecError,
	TaskCancelRequest,
} from './browser-executor.worker.js';

/** Task types handled by the local LLM via shinka module (not Web Worker). */
const LLM_TASK_TYPES = new Set(['llmInference', 'shinkaInference', 'heartbeatInference', 'joucho', 'converse']);

export type AgentState = 'idle' | 'probing' | 'connecting' | 'connected' | 'executing' | 'reconnecting' | 'error' | 'offline';

export interface AgentStats {
	state: AgentState;
	gatewayState: GatewayState;
	transportType: TransportType;
	sessionId: string | null;
	gpuTier: string;
	gpuAdapter: string;
	memClass: string;
	powerClass: string;
	cores: number;
	jobsDone: number;
	jobsFailed: number;
	totalGpuTimeMs: number;
	currentTaskId: string | null;
	currentProgress?: { done: number; total: number; stage: string; detail?: string };
	lastHeartbeatAck: string | null;
}

type OnUpdate = (stats: AgentStats) => void;

const MURAKUMO_GATEWAY_URL = 'wss://murakumo.etzhayyim.com/browser-gateway/ws';

export class BrowserInferenceAgent {
	private stats: AgentStats = {
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
	};

	private onUpdate: OnUpdate;
	private gateway: BrowserGatewayConnection | null = null;
	private executor: Worker | null = null;
	private stopped = false;
	private gatewayUrl: string;
	/** Selected inference model ID (e.g. "qwen3.5-2b"). */
	private inferenceModelId: string | undefined;

	constructor(onUpdate: OnUpdate, gatewayUrl?: string, inferenceModelId?: string) {
		this.gatewayUrl = gatewayUrl ?? MURAKUMO_GATEWAY_URL;
		this.onUpdate = onUpdate;
		this.inferenceModelId = inferenceModelId;
	}

	async start(): Promise<void> {
		if (this.stats.state !== 'idle' && this.stats.state !== 'offline' && this.stats.state !== 'error') return;
		this.stopped = false;

		this.setState('probing');
		let capability: BrowserCapability;
		try {
			capability = await probeCapabilities();
			if (this.inferenceModelId) {
				capability.inferenceModelId = this.inferenceModelId;
			}
			this.stats.gpuTier = capability.gpuTier;
			this.stats.gpuAdapter = capability.gpu.adapter;
			this.stats.memClass = capability.memClass;
			this.stats.powerClass = capability.powerClass;
			this.stats.cores = capability.cores;
		} catch {
			this.setState('error');
			return;
		}

		try {
			this.executor = new Worker(
				new URL('./browser-executor.worker.ts', import.meta.url),
				{ type: 'module' },
			);
			this.executor.onmessage = (ev) => this.handleWorkerMessage(ev.data);
			this.executor.onerror = () => {};
		} catch {
			this.setState('error');
			return;
		}

		this.setState('connecting');
		this.gateway = new BrowserGatewayConnection(this.gatewayUrl, {
			onStateChange: (state) => this.handleGatewayState(state),
			onRegistered: (msg) => this.handleRegistered(msg),
			onTaskPush: (msg) => this.handleTaskPush(msg),
			onTaskCancel: (msg) => this.handleTaskCancel(msg),
			onHeartbeatAck: (msg) => this.handleHeartbeatAck(msg),
			onError: (msg) => this.handleGatewayError(msg),
		});
		this.gateway.connect(capability);

		if (typeof document !== 'undefined') {
			window.addEventListener('beforeunload', this.handleUnload);
		}
	}

	async stop(): Promise<void> {
		this.stopped = true;

		if (typeof window !== 'undefined') {
			window.removeEventListener('beforeunload', this.handleUnload);
		}

		if (this.gateway) {
			this.gateway.disconnect();
			this.gateway = null;
		}

		if (this.executor) {
			this.executor.terminate();
			this.executor = null;
		}

		this.setState('offline');
	}

	getStats(): AgentStats {
		return { ...this.stats };
	}

	private handleGatewayState(state: GatewayState): void {
		this.stats.gatewayState = state;
		if (this.gateway) {
			this.stats.transportType = this.gateway.transportType;
		}
		if (state === 'connected') {
			this.setState('connected');
		} else if (state === 'reconnecting') {
			this.setState('reconnecting');
		} else if (state === 'disconnected' && !this.stopped) {
			this.setState('offline');
		}
	}

	private handleRegistered(msg: RegisteredMsg): void {
		this.stats.sessionId = msg.sessionId;
		this.stats.gpuTier = msg.gpuTier;
		this.notify();
	}

	private handleTaskPush(msg: TaskPushMsg): void {
		if (this.stats.state === 'executing') {
			if (this.gateway) {
				this.gateway.sendFailure({
					'leaseId': msg.leaseId,
					'taskId': msg.taskId,
					reason: 'busy',
					error: 'worker is already executing a task',
				});
			}
			return;
		}

		this.stats.currentTaskId = msg.taskId;
		this.stats.currentProgress = undefined;
		this.setState('executing');

		// Route LLM-class tasks to local LLM via shinka module (main thread, WebLLM).
		// Non-LLM tasks go to the Web Worker executor (CPU compute).
		if (LLM_TASK_TYPES.has(msg.taskType)) {
			this.executeLlmTask(msg);
		} else if (this.executor) {
			const req: TaskExecRequest = {
				type: 'exec',
				taskId: msg.taskId,
				leaseId: msg.leaseId,
				taskType: msg.taskType,
				params: msg.params,
			};
			this.executor.postMessage(req);
		} else {
			if (this.gateway) {
				this.gateway.sendFailure({
					'leaseId': msg.leaseId,
					'taskId': msg.taskId,
					reason: 'noExecutor',
					error: 'no executor available',
				});
			}
			this.setState('connected');
		}
	}

	/**
	 * Execute LLM inference task using the local LLM via shinka module.
	 * Runs on main thread (WebLLM requires DOM/WebGPU access).
	 */
	private async executeLlmTask(msg: TaskPushMsg): Promise<void> {
		const start = performance.now();
		try {
			const params = JSON.parse(msg.params || '{}');
			const shinka = useShinkaInference();
			const output = await shinka.executeGatewayTask(msg.taskId, msg.leaseId, msg.taskType, params);
			const elapsed = Math.round(performance.now() - start);

			if (this.gateway) {
				this.gateway.sendResult({
					'leaseId': msg.leaseId,
					'taskId': msg.taskId,
					output,
					'gpuTimeMs': elapsed,
				});
			}
			this.stats.jobsDone++;
			this.stats.totalGpuTimeMs += elapsed;
		} catch (err) {
			if (this.gateway) {
				this.gateway.sendFailure({
					'leaseId': msg.leaseId,
					'taskId': msg.taskId,
					reason: 'llmError',
					error: err instanceof Error ? err.message : String(err),
				});
			}
			this.stats.jobsFailed++;
		}

		this.stats.currentTaskId = null;
		this.stats.currentProgress = undefined;
		this.setState('connected');
	}

	private handleTaskCancel(msg: TaskCancelMsg): void {
		if (this.stats.currentTaskId === msg.taskId && this.executor) {
			const cancel: TaskCancelRequest = { type: 'cancel', taskId: msg.taskId };
			this.executor.postMessage(cancel);
		}
		this.stats.currentTaskId = null;
		this.stats.currentProgress = undefined;
		this.setState('connected');
	}

	private handleHeartbeatAck(msg: HeartbeatAckMsg): void {
		this.stats.lastHeartbeatAck = msg.serverTime;
		this.notify();
	}

	private handleGatewayError(_msg: ErrorMsg): void {}

	private handleWorkerMessage(msg: TaskExecProgress | TaskExecResult | TaskExecError): void {
		switch (msg.type) {
			case 'progress':
				this.stats.currentProgress = {
					done: msg.done,
					total: msg.total,
					stage: msg.stage,
					detail: msg.detail,
				};
				if (this.gateway && this.stats.currentTaskId) {
					this.gateway.sendProgress({
						'taskId': this.stats.currentTaskId,
						stage: msg.stage,
						done: msg.done,
						total: msg.total,
						detail: msg.detail,
					});
				}
				this.notify();
				break;

			case 'result':
				if (this.gateway) {
					this.gateway.sendResult({
						'leaseId': msg.leaseId,
						'taskId': msg.taskId,
						output: msg.output,
						'gpuTimeMs': msg.gpuTimeMs,
					});
				}
				this.stats.jobsDone++;
				this.stats.totalGpuTimeMs += msg.gpuTimeMs;
				this.stats.currentTaskId = null;
				this.stats.currentProgress = undefined;
				this.setState('connected');
				break;

			case 'error':
				if (this.gateway) {
					this.gateway.sendFailure({
						'leaseId': msg.leaseId,
						'taskId': msg.taskId,
						reason: msg.reason,
						error: msg.message,
					});
				}
				this.stats.jobsFailed++;
				this.stats.currentTaskId = null;
				this.stats.currentProgress = undefined;
				this.setState('connected');
				break;
		}
	}

	private handleUnload = (): void => {
		if (this.gateway) this.gateway.disconnect();
	};

	private setState(state: AgentState): void {
		this.stats.state = state;
		this.notify();
	}

	private notify(): void {
		this.onUpdate({ ...this.stats });
	}
}
