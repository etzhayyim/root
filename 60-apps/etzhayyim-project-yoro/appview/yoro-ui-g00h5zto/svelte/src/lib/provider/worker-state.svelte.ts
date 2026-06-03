import { WorkerClient, type WorkerStats, type WorkerConfig, type ProviderMode } from './worker-client.js';
import { recommendExpert } from './market-client.js';

const PROVIDER_MODE_EXPERT: ProviderMode = 'expertFfn';
const PROVIDER_MODE_FULL_MLC: ProviderMode = 'fullMlc';
const PROVIDER_MODE_LIMA: ProviderMode = 'lima';
const WAN_MODEL_ID = 'etzhayyim/etzhayyim-distributed-ti2v-moe-260222';
const QWEN_MODEL_ID = 'etzhayyim/etzhayyim-distributed-moe-260222';
const DISTRIBUTED_2260224_MODEL_ID = 'etzhayyim/etzhayyim-distributed-2260224';
const EXPERT_PROVIDER_MODEL_IDS = [WAN_MODEL_ID, QWEN_MODEL_ID] as const;
const FULL_MLC_PROVIDER_MODEL_IDS = [DISTRIBUTED_2260224_MODEL_ID] as const;

let _workerStats = $state<WorkerStats>({
	state: 'disconnected',
	workerId: null,
	jobsComplete: 0,
	jobsFailed: 0,
	totalEarned: 0,
	avgLatencyMs: 0,
	connectedAt: null,
	lastJobAt: null,
});

let _expertId = $state(0);
let _pricePerCC = $state(0.001);
let _pricePerTokenIn = $state(0.00001);
let _pricePerTokenOut = $state(0.00002);
let _maxContextTokens = $state(4096);
let _isJoined = $state(false);
let _manualExpert = $state(false);
let _providerMode = $state<ProviderMode>(PROVIDER_MODE_EXPERT);
let _modelId = $state<string>(WAN_MODEL_ID);

let client: WorkerClient | null = null;

function isLLMProviderMode(mode: ProviderMode): boolean {
	return mode === PROVIDER_MODE_FULL_MLC || mode === PROVIDER_MODE_LIMA;
}

function providerModelsForMode(mode: ProviderMode): readonly string[] {
	return isLLMProviderMode(mode) ? FULL_MLC_PROVIDER_MODEL_IDS : EXPERT_PROVIDER_MODEL_IDS;
}

function defaultModelForMode(mode: ProviderMode): string {
	return isLLMProviderMode(mode) ? DISTRIBUTED_2260224_MODEL_ID : WAN_MODEL_ID;
}

function normalizeProviderMode(v: string): ProviderMode {
	if (v === PROVIDER_MODE_FULL_MLC) return PROVIDER_MODE_FULL_MLC;
	if (v === PROVIDER_MODE_LIMA) return PROVIDER_MODE_LIMA;
	return PROVIDER_MODE_EXPERT;
}

function normalizeProviderModelId(modelId: string, mode: ProviderMode): string {
	const models = providerModelsForMode(mode);
	return models.includes(modelId) ? modelId : defaultModelForMode(mode);
}

function handleStateChange(stats: WorkerStats) {
	_workerStats = stats;
}

export function useProviderWorker() {
	return {
		get workerStats() { return _workerStats; },
		get providerModes() {
			return [PROVIDER_MODE_EXPERT, PROVIDER_MODE_FULL_MLC, PROVIDER_MODE_LIMA] as const;
		},
		get providerMode() { return _providerMode; },
		set providerMode(v: string) {
			const mode = normalizeProviderMode(v);
			_providerMode = mode;
			_modelId = normalizeProviderModelId(_modelId, mode);
		},
		get providerModels() { return [...providerModelsForMode(_providerMode)]; },
		get modelId() { return _modelId; },
		set modelId(v: string) { _modelId = normalizeProviderModelId(v, _providerMode); },
		get expertId() { return _expertId; },
		set expertId(v: number) { _expertId = v; },
		get pricePerCC() { return _pricePerCC; },
		set pricePerCC(v: number) { _pricePerCC = v; },
		get pricePerTokenIn() { return _pricePerTokenIn; },
		set pricePerTokenIn(v: number) { _pricePerTokenIn = v; },
		get pricePerTokenOut() { return _pricePerTokenOut; },
		set pricePerTokenOut(v: number) { _pricePerTokenOut = v; },
		get maxContextTokens() { return _maxContextTokens; },
		set maxContextTokens(v: number) { _maxContextTokens = v; },
		get isFullMLCMode() { return isLLMProviderMode(_providerMode); },
		get isJoined() { return _isJoined; },
		get manualExpert() { return _manualExpert; },
		set manualExpert(v: boolean) { _manualExpert = v; },
		async joinNetwork() {
			const mode = normalizeProviderMode(_providerMode);
			_providerMode = mode;
			let modelId = normalizeProviderModelId(_modelId, mode);
			_modelId = modelId;

			// Auto-assign expert via web4 scheduler
			if (mode === PROVIDER_MODE_EXPERT && !_manualExpert) {
				try {
					const rec = await recommendExpert(modelId, mode);
					if (rec.expertId >= 0 && rec.expertId < 32) {
						_expertId = rec.expertId;
					}
					if (rec.pricePerCc > 0) {
						_pricePerCC = rec.pricePerCc;
					}
					if (rec.modelId) {
						modelId = normalizeProviderModelId(rec.modelId, mode);
						_modelId = modelId;
					}
				} catch {
					// Fallback: random expert if scheduler unavailable
					_expertId = Math.floor(Math.random() * 32);
				}
			}

			const config: WorkerConfig = {
				providerMode: mode,
				modelId,
				expertId: mode === PROVIDER_MODE_EXPERT ? _expertId : -1,
				quantBits: mode === PROVIDER_MODE_EXPERT ? 4 : 0,
				modelSizeMB: mode === PROVIDER_MODE_EXPERT ? 33 : 0,
				pricePerCC: mode === PROVIDER_MODE_EXPERT ? _pricePerCC : 0,
				pricePerTokenIn: isLLMProviderMode(mode) ? _pricePerTokenIn : 0,
				pricePerTokenOut: isLLMProviderMode(mode) ? _pricePerTokenOut : 0,
				capabilities:
					mode === PROVIDER_MODE_LIMA
						? ['llm.chatCompletion', 'lima']
						: isLLMProviderMode(mode)
							? ['llm.chatCompletion', 'fullMlc']
							: ['expert.forward'],
				maxContextTokens: isLLMProviderMode(mode) ? _maxContextTokens : 0,
			};
			client = new WorkerClient(config, handleStateChange);
			client.connect();
			_isJoined = true;
		},
		async autoJoin() {
			if (_isJoined) return;
			_providerMode = PROVIDER_MODE_EXPERT;
			_manualExpert = false;
			_modelId = WAN_MODEL_ID;
			await this.joinNetwork();
		},
		leaveNetwork() {
			client?.disconnect();
			client = null;
			_isJoined = false;
		},
		getClient(): WorkerClient | null {
			return client;
		},
	};
}
