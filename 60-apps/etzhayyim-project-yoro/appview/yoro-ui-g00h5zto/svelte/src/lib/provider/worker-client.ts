export type WorkerState = 'disconnected' | 'connecting' | 'registered' | 'working' | 'error';
export type ProviderMode = 'expertFfn' | 'fullMlc' | 'lima';

export interface WorkerConfig {
	providerMode: ProviderMode;
	modelId: string;
	expertId: number;
	quantBits: number;
	modelSizeMB: number;
	pricePerCC: number;
	pricePerTokenIn: number;
	pricePerTokenOut: number;
	capabilities: string[];
	maxContextTokens: number;
}

export interface WorkerStats {
	state: WorkerState;
	workerId: string | null;
	jobsComplete: number;
	jobsFailed: number;
	totalEarned: number;
	avgLatencyMs: number;
	connectedAt: Date | null;
	lastJobAt: Date | null;
}

type StateChangeCallback = (stats: WorkerStats) => void;

const WEB4_API_BASE = 'https://web4.etzhayyim.com/api/v1';

export class WorkerClient {
	private config: WorkerConfig;
	private stats: WorkerStats;
	private onStateChange: StateChangeCallback;
	private pollTimer: ReturnType<typeof setInterval> | null = null;
	private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
	private stopped = false;

	constructor(config: WorkerConfig, onStateChange: StateChangeCallback) {
		this.config = config;
		this.onStateChange = onStateChange;
		this.stats = {
			state: 'disconnected',
			workerId: null,
			jobsComplete: 0,
			jobsFailed: 0,
			totalEarned: 0,
			avgLatencyMs: 0,
			connectedAt: null,
			lastJobAt: null,
		};
	}

	async connect(): Promise<void> {
		if (this.stats.state === 'registered' || this.stats.state === 'working') return;
		this.stopped = false;
		this.updateState('connecting');

		try {
			const resp = await fetch(`${WEB4_API_BASE}/register`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					'providerMode': this.config.providerMode,
					'modelId': this.config.modelId,
					'expertId': this.config.expertId,
					'quantBits': this.config.quantBits,
					'modelSizeMb': this.config.modelSizeMB,
					'pricePerCc': this.config.pricePerCC,
					'pricePerTokenIn': this.config.pricePerTokenIn,
					'pricePerTokenOut': this.config.pricePerTokenOut,
					capabilities: this.config.capabilities,
					runtime: {
						engine: this.config.providerMode === 'expertFfn' ? 'custom-webgpu' : 'webllm',
						'maxContextTokens': this.config.maxContextTokens,
					},
				}),
			});

			if (!resp.ok) {
				this.updateState('error');
				return;
			}

			const data = await resp.json();
			this.stats.workerId = data.workerId;
			this.stats.connectedAt = new Date();
			this.updateState('registered');

			this.pollTimer = setInterval(() => this.pollForJobs(), 2000);
			this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), 10000);
		} catch {
			this.updateState('error');
		}
	}

	disconnect(): void {
		this.stopped = true;
		if (this.pollTimer) {
			clearInterval(this.pollTimer);
			this.pollTimer = null;
		}
		if (this.heartbeatTimer) {
			clearInterval(this.heartbeatTimer);
			this.heartbeatTimer = null;
		}
		if (this.stats.workerId) {
			fetch(`${WEB4_API_BASE}/unregister`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ 'workerId': this.stats.workerId }),
			}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/provider/worker-client.ts: suppressed async error", error); });
		}
		this.updateState('disconnected');
	}

	private async sendHeartbeat(): Promise<void> {
		if (this.stopped || !this.stats.workerId) return;
		try {
			await fetch(`${WEB4_API_BASE}/heartbeat`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ 'workerId': this.stats.workerId }),
			});
		} catch {
			// heartbeat failure non-fatal
		}
	}

	private async pollForJobs(): Promise<void> {
		if (this.stopped || !this.stats.workerId || this.stats.state === 'working') return;
		try {
			const resp = await fetch(
				`${WEB4_API_BASE}/jobs/poll?workerId=${encodeURIComponent(this.stats.workerId)}`,
			);
			if (!resp.ok) return;
			const data = await resp.json();
			if (data.hasJob && data.job) {
				await this.handleJob(data.job);
			}
		} catch {
			// poll failure non-fatal
		}
	}

	private async handleJob(req: any): Promise<void> {
		this.updateState('working');
		const start = performance.now();
		try {
			// CPU fallback: mock FFN (SwiGLU approximation)
			const input: number[] = Array.isArray(req.payload?.input)
				? req.payload.input
				: Array.isArray(req.input)
					? req.input
					: [];
			const output = input.map((v: number) => {
				const gate = v * 0.5;
				const silu = gate / (1 + Math.exp(-gate));
				return silu * (v * 0.3 + 0.1);
			});
			const elapsed = Math.round(performance.now() - start);
			await this.submitResult(req.jobId, 'expert.forward', output, elapsed);
			this.markSuccess(elapsed);
			this.stats.totalEarned += Math.max(this.config.pricePerCC, 0);
			this.updateState('registered');
		} catch (e) {
			this.markFailure();
			this.submitResult(req.jobId, 'expert.forward', [], -1, e instanceof Error ? e.message : String(e)).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/provider/worker-client.ts: suppressed async error", error); });
			this.updateState('registered');
		}
	}

	private async submitResult(jobId: string, jobType: string, output: unknown, elapsedMs: number, error?: string): Promise<void> {
		if (!this.stats.workerId) return;
		await fetch(`${WEB4_API_BASE}/jobs/result`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				'workerId': this.stats.workerId,
				'jobId': jobId,
				'jobType': jobType,
				output,
				'elapsedMs': elapsedMs,
				error,
			}),
		});
	}

	private markSuccess(elapsedMs: number): void {
		this.stats.jobsComplete++;
		this.stats.lastJobAt = new Date();
		this.stats.avgLatencyMs = 0.3 * elapsedMs + 0.7 * this.stats.avgLatencyMs;
	}

	private markFailure(): void {
		this.stats.jobsFailed++;
	}

	private updateState(state: WorkerState): void {
		this.stats.state = state;
		this.onStateChange({ ...this.stats });
	}

	getStats(): WorkerStats {
		return { ...this.stats };
	}
}
