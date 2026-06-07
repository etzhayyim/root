/**
 * Minimal LLM model registry inlined for the CF Worker.
 *
 * Source: 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts
 * (legacy upstream). Extracted here to drop the `@etzhayyim/kotodama-host-sdk`
 * dependency per ADR-2605191358 (substrate boundary: no direct legacy SDK
 * imports from etzhayyim/* code). Only the data structures consumed by
 * buildOpenAiModelList() and remapModelForFleet() are kept.
 */

export interface ModelDef {
  cfModel: string;
  maxTokens: number;
  contextWindow: number;
  available: boolean;
  ollamaModel?: string;
  huggingfaceModel?: string;
}

export const MODEL_REGISTRY: Record<string, ModelDef> = {
  "gemma-4-e4b-it": {
    cfModel: "@cf/google/gemma-4-e4b-it",
    maxTokens: 4096,
    contextWindow: 128000,
    available: true,
    ollamaModel: "gemma4:e4b",
  },
  "gemma4-runpod": {
    cfModel: "openai/gemma-4-e4b-it",
    maxTokens: 8192,
    contextWindow: 128000,
    available: true,
    ollamaModel: "gemma4:26b-a4b-it-q4_K_M",
  },
  "tier0-runpod": {
    cfModel: "openai/gemma-4-e4b-it",
    maxTokens: 8192,
    contextWindow: 128000,
    available: true,
    ollamaModel: "gemma4:26b-a4b-it-q4_K_M",
  },
  "gemma-4-e2b-it": {
    cfModel: "@cf/google/gemma-4-e2b-it",
    maxTokens: 4096,
    contextWindow: 128000,
    available: true,
    ollamaModel: "gemma4:e2b",
  },
  "qwen3-30b": {
    cfModel: "@cf/qwen/qwen3-30b-a3b-fp8",
    maxTokens: 4096,
    contextWindow: 32768,
    available: true,
    ollamaModel: "gemma4:e4b",
  },
  "qwq-32b": {
    cfModel: "@cf/qwen/qwq-32b",
    maxTokens: 8192,
    contextWindow: 32768,
    available: true,
  },
  "llama-3.3-70b": {
    cfModel: "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    maxTokens: 4096,
    contextWindow: 8192,
    available: true,
  },
  "gemma-3-12b": {
    cfModel: "@cf/google/gemma-3-12b-it",
    maxTokens: 4096,
    contextWindow: 8192,
    available: true,
  },
  "deepseek-pro-v4": {
    cfModel: "deepseek/deepseek-chat",
    maxTokens: 8192,
    contextWindow: 131072,
    available: true,
  },
};

export const MODEL_ALIASES: Record<string, string> = {
  "gemma-3-12b-it": "gemma-3-12b",
  "@cf/google/gemma-3-12b-it": "gemma-3-12b",
  "gemma-4-e2b": "gemma-4-e2b-it",
  "@cf/google/gemma-4-e2b-it": "gemma-4-e2b-it",
  "gemma-4-e4b": "gemma-4-e4b-it",
  "@cf/google/gemma-4-e4b-it": "gemma-4-e4b-it",
  "qwen3.5-4b": "qwen3-30b",
  "qwen3.5-4b-instruct": "qwen3-30b",
  "qwen3.5-9b": "qwen3-30b",
  "qwen3.5-9b-instruct": "qwen3-30b",
};
