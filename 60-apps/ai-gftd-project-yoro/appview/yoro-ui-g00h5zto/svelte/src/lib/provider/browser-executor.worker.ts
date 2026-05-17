/**
 * browser-executor.worker.ts — Lightweight inference executor (CPU fallback).
 *
 * Handles kernel/pipeline/reduce/llmInference tasks off the main thread.
 * For heavy GPU inference (WAN4/ONNX), the full murakumo executor is needed.
 */

export interface TaskExecRequest {
	type: 'exec';
	taskId: string;
	leaseId: string;
	taskType: string;
	params: string;
}

export interface TaskExecProgress {
	type: 'progress';
	taskId: string;
	stage: string;
	done: number;
	total: number;
	detail?: string;
}

export interface TaskExecResult {
	type: 'result';
	taskId: string;
	leaseId: string;
	output: string;
	gpuTimeMs: number;
}

export interface TaskExecError {
	type: 'error';
	taskId: string;
	leaseId: string;
	reason: string;
	message: string;
}

export interface TaskCancelRequest {
	type: 'cancel';
	taskId: string;
}

export type WorkerInbound = TaskExecRequest | TaskCancelRequest;
export type WorkerOutbound = TaskExecProgress | TaskExecResult | TaskExecError;

const cancelledTasks = new Set<string>();

self.onmessage = async (ev: MessageEvent<WorkerInbound>) => {
	const msg = ev.data;

	if (msg.type === 'cancel') {
		cancelledTasks.add(msg.taskId);
		return;
	}

	if (msg.type === 'exec') {
		const start = performance.now();
		try {
			const output = await executeTask(msg);
			const elapsed = Math.round(performance.now() - start);
			const result: TaskExecResult = {
				type: 'result',
				taskId: msg.taskId,
				leaseId: msg.leaseId,
				output: typeof output === 'string' ? output : JSON.stringify(output),
				gpuTimeMs: elapsed,
			};
			self.postMessage(result);
		} catch (err) {
			const error: TaskExecError = {
				type: 'error',
				taskId: msg.taskId,
				leaseId: msg.leaseId,
				reason: 'workerError',
				message: err instanceof Error ? err.message : String(err),
			};
			self.postMessage(error);
		} finally {
			cancelledTasks.delete(msg.taskId);
		}
	}
};

async function executeTask(req: TaskExecRequest): Promise<unknown> {
	const params = JSON.parse(req.params || '{}');

	switch (req.taskType) {
		case 'kernel':
			return runKernel(params);
		case 'pipeline':
			return runPipeline(req.taskId, params);
		case 'reduce':
			return runReduce(params);
		case 'llmInference':
			return runLLMInference(params);
		default:
			throw new Error(`Unsupported task type: ${req.taskType}`);
	}
}

function runKernel(params: Record<string, unknown>): unknown {
	const input = (params.input as number[]) ?? [];
	const output = input.map((v) => {
		const gate = v * 0.5;
		return (gate / (1 + Math.exp(-gate))) * (v * 0.3 + 0.1);
	});
	return { output, kernel: 'swigluCpu' };
}

function runPipeline(taskId: string, params: Record<string, unknown>): unknown {
	const steps = (params.steps as number) ?? 1;
	let data = (params.input as number[]) ?? [1.0];
	for (let i = 0; i < steps; i++) {
		if (cancelledTasks.has(taskId)) throw new Error('cancelled');
		data = data.map((v) => Math.tanh(v * 0.5 + 0.1));
		const progress: TaskExecProgress = {
			type: 'progress',
			taskId,
			stage: 'pipeline',
			done: i + 1,
			total: steps,
		};
		self.postMessage(progress);
	}
	return { output: data, 'stepsExecuted': steps };
}

function runReduce(params: Record<string, unknown>): unknown {
	const values = (params.values as number[]) ?? [];
	const op = (params.op as string) ?? 'sum';
	let result = 0;
	switch (op) {
		case 'sum': result = values.reduce((a, b) => a + b, 0); break;
		case 'mean': result = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0; break;
		case 'max': result = values.length > 0 ? Math.max(...values) : 0; break;
		case 'min': result = values.length > 0 ? Math.min(...values) : 0; break;
	}
	return { result, op, count: values.length };
}

function runLLMInference(params: Record<string, unknown>): unknown {
	const input = (params.input as number[]) ?? [];
	const expertId = (params.expertId as number) ?? 0;
	const layerId = (params.layerId as number) ?? 0;
	const output = input.map((v) => {
		const gate = v * 0.5;
		return (gate / (1 + Math.exp(-gate))) * (v * 0.3 + 0.1);
	});
	return { output, 'expertId': expertId, 'layerId': layerId, runtime: 'cpuFallback' };
}
