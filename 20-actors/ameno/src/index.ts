/**
 * @etzhayyim/ameno — Browser WebGPU inference engine.
 *
 * Provides client-side LLM inference via transformers.js + ONNX + WebGPU,
 * per-actor LoRA adapter merge via WebGPU compute shaders,
 * and RAG context injection via DuckDB-WASM.
 *
 * @packageDocumentation
 */

export {
  MODELS,
  checkWebGPU,
  getGPUInfo,
  loadModel,
  setLoraAdapters,
  getActiveAdapterIds,
  generate,
  type InferenceState,
  type InferenceDevice,
  type ChatMessage,
  type GenerationStats,
} from "./inference";

export {
  parseSafetensors,
  fetchLoraAdapter,
  applyLoraAdapters,
  type LoraAdapterMeta,
  type LoraLayerWeights,
  type LoadedLoraAdapter,
  type AdapterMergeSpec,
} from "./lora-runtime";

export {
  ragSearch,
  listActorAdapters,
  selectAdapters,
  ragLoraSelect,
  buildRagContextPrompt,
  type RagResult,
  type AdapterCandidate,
  type RagLoraContext,
} from "./rag-lora";

// WebNN inference fast path (ADR-2605252100). Detection + routing
// only at R0; `dispatchWebnnInference` throws until R1 wires the ORT
// WebNN EP.
export {
  detectWebnnSupport,
  selectInferenceBackend,
  probeAndSelect,
  dispatchWebnnInference,
  type WebnnSupport,
  type WebnnDeviceType,
  type InferenceBackend,
} from "./inference/webnn";

export {
  TRAIN_DEFAULTS,
  DEVICE_STEP_BUDGET,
  detectDeviceClass,
  runFederatedRound,
  signDeltaManifest,
  publishDeltaRecord,
  // R1a framework re-exports
  probeDeviceProfile,
  selectNumericsPath,
  loadShard,
  gradeResponse,
  scanShard,
  computeRoundId,
  openRoundDir,
  type TrainDeviceClass,
  type LoraTrainConfig,
  type TrainShardRef,
  type RoundContext,
  type CharterRiderScanResult,
  type TrainRoundResult,
  type SignedDeltaManifest,
  type RunRoundDeps,
  type DeviceProfile,
  type NumericsPath,
  type WarmupShard,
  type LoadedShard,
  type ShardExample,
  type ScanResult,
  type RoundMeta,
  type RngState,
  type RoundDirHandle,
} from "./train";
