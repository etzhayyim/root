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

export {
  fetchGovProcedures,
  tokenize,
  retrieveProcedures,
  buildKotobaContext,
  groundedMessages,
  type KotobaProcedure,
  type RetrievedProcedure,
  type GroundChatMessage,
} from "./kotoba-ground";
