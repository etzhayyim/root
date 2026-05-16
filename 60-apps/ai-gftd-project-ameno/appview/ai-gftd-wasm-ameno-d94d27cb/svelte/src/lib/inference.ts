/**
 * Re-export from @gftd/ameno package.
 * @see packages/llm/inference/ameno/src/inference.ts
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
  type ChatMessage,
  type GenerationStats,
} from "@gftd/ameno/inference";
