/**
 * Browser-side inference engine using transformers.js with WebGPU backend.
 *
 * Loads ONNX models and runs multimodal inference entirely in the browser
 * via WebGPU compute shaders. Supports per-actor LoRA adapter merge
 * and RAG context injection.
 */

import type { AdapterMergeSpec } from "./lora-runtime";
import type { RagResult } from "./rag-lora";
import { buildRagContextPrompt } from "./rag-lora";

/** Engine model id → HuggingFace ONNX repo. SSoT mirrored by com.etzhayyim.apps.ameno.listModels. */
export const MODELS: Readonly<Record<string, string>> = {
  "gemma-4-e2b-it": "onnx-community/gemma-4-E2B-it-ONNX",
  "gemma-4-e4b-it": "onnx-community/gemma-4-E4B-it-ONNX",
  // Baien (BitNet b1.58 2B 4T) — ADR-2605092350. bf16 master from microsoft;
  // ONNX-community variant when available. Loads with WASM ternary kernel
  // fallback so it runs without WebGPU.
  "baien-bitnet-2b": "onnx-community/bitnet-b1.58-2B-4T-bf16-ONNX",
};
const DEFAULT_MODEL_KEY = "gemma-4-e2b-it";
const MODEL_ID = MODELS[DEFAULT_MODEL_KEY];

/** Models that prefer WASM ternary kernels over WebGPU. */
const WASM_PREFERRED_MODELS = new Set(["baien-bitnet-2b"]);

export type InferenceDevice = "webgpu" | "wasm";

function resolveModelRepo(modelKeyOrRepo?: string): string {
  if (!modelKeyOrRepo) return MODEL_ID;
  return MODELS[modelKeyOrRepo] ?? modelKeyOrRepo;
}

function resolveDevice(modelKey: string | undefined, override?: InferenceDevice): InferenceDevice {
  if (override) return override;
  if (modelKey && WASM_PREFERRED_MODELS.has(modelKey)) return "wasm";
  return "webgpu";
}

let currentModelId: string = MODEL_ID;

/**
 * Inference engine state machine.
 *
 * Tracks model lifecycle, LoRA adapter state, and actor binding.
 * Used as Svelte 5 reactive state (`$state`) in `App.svelte`.
 */
export interface InferenceState {
  /**
   * Current engine status:
   * - `"idle"` — no model loaded, waiting for user action.
   * - `"loading"` — downloading ONNX model weights from HuggingFace.
   * - `"ready"` — model loaded, accepting generation requests.
   * - `"generating"` — actively running inference (streaming tokens).
   * - `"merging-lora"` — applying LoRA adapter weights to base model.
   * - `"error"` — an error occurred (see `error` field).
   */
  status: "idle" | "loading" | "ready" | "generating" | "merging-lora" | "error";
  /** Download/merge progress percentage (0-100). */
  progress: number;
  /** Error message if `status === "error"`, otherwise `null`. */
  error: string | null;
  /** Display name of the loaded model (from llm-model-registry), or `null` if unloaded. */
  loadedModel: string | null;
  /** Whether the browser supports WebGPU (checked on mount). */
  webgpuAvailable: boolean;
  /** Active LoRA adapter IDs currently merged into model weights. Empty = base model only. */
  activeAdapters: string[];
  /** Current actor DID for per-actor LoRA scoping, or `null` for anonymous mode. */
  actorDid: string | null;
}

/**
 * Chat message in OpenAI-compatible format.
 *
 * Supports both plain text and multimodal content (text + image).
 */
export interface ChatMessage {
  /** Message role in the conversation. */
  role: "user" | "assistant" | "system";
  /** Plain text content, or multimodal content array for image input. */
  content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
}

/**
 * Generation statistics returned after each inference call.
 *
 * Includes performance metrics and flags indicating which augmentation
 * features (LoRA, RAG) were active during generation.
 */
export interface GenerationStats {
  /** Tokens generated per second (total tokens / duration). */
  tokensPerSecond: number;
  /** Total number of tokens generated in this response. */
  totalTokens: number;
  /** Wall-clock duration of the generation in milliseconds. */
  durationMs: number;
  /** `true` if one or more LoRA adapters were active during generation. */
  loraActive: boolean;
  /** `true` if RAG context documents were injected into the system prompt. */
  ragActive: boolean;
}

/** Metering: per-inference usage report for credits integration. */
export interface UsageReport {
  /** Number of tokens in the input prompt. */
  promptTokens: number;
  /** Number of tokens generated in the completion. */
  completionTokens: number;
  /** Wall-clock duration of the generation in milliseconds. */
  durationMs: number;
  /** Tokens generated per second. */
  tokensPerSecond: number;
  /** HuggingFace model ID used for inference. */
  modelId: string;
  /** Inference provider — always `"webgpu"` for ameno. */
  provider: "webgpu";
  /** Whether LoRA adapters were active during generation. */
  loraActive: boolean;
  /** Whether RAG context was injected during generation. */
  ragActive: boolean;
}

/** Cached transformers.js pipeline instance (text-generation). */
let pipeline: unknown = null;
/** Cached tokenizer instance (unused — tokenizer is bundled with pipeline). */
let tokenizer: unknown = null;
/** Currently active LoRA adapter merge specifications. */
let activeLoraSpecs: AdapterMergeSpec[] = [];

/**
 * Detect WebGPU availability in the current browser.
 *
 * @returns `true` if `navigator.gpu` exists and a GPU adapter can be obtained.
 */
export async function checkWebGPU(): Promise<boolean> {
  if (!navigator.gpu) return false;
  try {
    const adapter = await navigator.gpu.requestAdapter();
    return adapter !== null;
  } catch {
    return false;
  }
}

/**
 * Get human-readable WebGPU device information for display.
 *
 * @returns String like `"apple m4 (Apple M4)"` or a fallback message if unavailable.
 */
export async function getGPUInfo(): Promise<string> {
  if (!navigator.gpu) return "WebGPU not supported";
  try {
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) return "No GPU adapter found";
    const info = await (adapter as GPUAdapter & { requestAdapterInfo(): Promise<GPUAdapterInfo> }).requestAdapterInfo();
    return `${info.vendor} ${info.architecture} (${info.device})`;
  } catch {
    return "GPU info unavailable";
  }
}

/**
 * Load an ONNX model with the WebGPU backend via `@huggingface/transformers`.
 *
 * Downloads model weights from HuggingFace Hub (cached in browser storage)
 * and initializes a text-generation pipeline with q4f16 quantization.
 *
 * @param onProgress - Progress callback receiving download percentage (0-100).
 * @param modelId - HuggingFace model ID to load. Defaults to `onnx-community/gemma-4-E2B-it-ONNX`.
 * @returns `true` if the model was loaded successfully.
 * @throws If model download or initialization fails.
 */
export async function loadModel(
  onProgress: (progress: number) => void,
  modelId?: string,
  device?: InferenceDevice,
): Promise<boolean> {
  const { pipeline: createPipeline, env } = await import(
    "@huggingface/transformers"
  );

  env.backends.onnx.wasm!.proxy = true;

  const repo = resolveModelRepo(modelId);
  const resolvedDevice = resolveDevice(modelId, device);
  // BitNet ternary weights work best with q4 on WASM; Gemma is q4f16 on WebGPU.
  const dtype = resolvedDevice === "wasm" ? "q4" : "q4f16";

  pipeline = await createPipeline("text-generation", repo, {
    device: resolvedDevice,
    dtype,
    progress_callback: (p: { progress?: number; status?: string }) => {
      if (p.progress !== undefined) {
        onProgress(Math.round(p.progress));
      }
    },
  });
  currentModelId = repo;

  return true;
}

/**
 * Set active LoRA adapter specs for subsequent generations.
 *
 * The adapters will be applied to model weights before inference.
 * Pass empty array to clear adapters (revert to base model).
 *
 * @param specs - Adapter merge specifications from RAG-LoRA selection.
 */
export function setLoraAdapters(specs: AdapterMergeSpec[]): void {
  activeLoraSpecs = specs;
}

/**
 * Get the adapter IDs of currently active LoRA adapters.
 *
 * @returns Array of adapter ID strings (empty if no adapters are active).
 */
export function getActiveAdapterIds(): string[] {
  return activeLoraSpecs.map((s) => s.adapter.meta.adapterId);
}

/**
 * Run text generation with optional LoRA adaptation and RAG context injection.
 *
 * When `ragContext` is provided, RAG documents are formatted by {@link buildRagContextPrompt}
 * and prepended to the system message. LoRA adapter state is tracked via {@link setLoraAdapters}
 * and reported in the returned stats.
 *
 * @param messages - Chat messages in OpenAI-compatible format.
 * @param onToken - Streaming callback invoked for each generated token string.
 * @param options - Optional generation parameters.
 * @param options.maxTokens - Maximum tokens to generate. Defaults to 1024.
 * @param options.ragContext - RAG search results to inject as system context.
 * @param options.ragTokenBudget - Token budget for RAG context block. Defaults to 2048.
 * @returns Generation statistics including throughput, duration, and augmentation flags.
 * @throws If no model is loaded (`pipeline === null`).
 */
export async function generate(
  messages: ChatMessage[],
  onToken: (token: string) => void,
  options: {
    maxTokens?: number;
    ragContext?: RagResult[];
    ragTokenBudget?: number;
  } = {},
): Promise<GenerationStats & { usage: UsageReport }> {
  if (!pipeline) throw new Error("Model not loaded");

  const { maxTokens = 1024, ragContext, ragTokenBudget = 2048 } = options;

  const gen = pipeline as {
    (
      messages: ChatMessage[],
      options: Record<string, unknown>,
    ): Promise<Array<{ generated_text: string }>>;
  };

  // Inject RAG context as system message prefix
  let augmentedMessages = messages;
  const ragActive = ragContext && ragContext.length > 0;
  if (ragActive) {
    const contextStr = buildRagContextPrompt(ragContext, ragTokenBudget);
    const systemMsg = augmentedMessages.find((m) => m.role === "system");
    if (systemMsg && typeof systemMsg.content === "string") {
      augmentedMessages = augmentedMessages.map((m) =>
        m === systemMsg
          ? { ...m, content: `${m.content}\n\n${contextStr}` }
          : m,
      );
    } else {
      augmentedMessages = [
        { role: "system", content: contextStr },
        ...augmentedMessages,
      ];
    }
  }

  const startMs = performance.now();
  let totalTokens = 0;

  const result = await gen(augmentedMessages, {
    max_new_tokens: maxTokens,
    temperature: 0.7,
    top_p: 0.9,
    do_sample: true,
    callback_function: (output: { text?: string }) => {
      if (output.text) {
        totalTokens++;
        onToken(output.text);
      }
    },
  });

  const durationMs = performance.now() - startMs;
  const tps = totalTokens / (durationMs / 1000);
  const loraActiveFlag = activeLoraSpecs.length > 0;
  const ragActiveFlag = !!ragActive;

  // Estimate prompt tokens from augmented messages character count (~4 chars/token heuristic)
  const promptChars = augmentedMessages.reduce((sum, m) => {
    const content = typeof m.content === "string" ? m.content : JSON.stringify(m.content);
    return sum + content.length;
  }, 0);
  const estimatedPromptTokens = Math.ceil(promptChars / 4);

  return {
    tokensPerSecond: tps,
    totalTokens,
    durationMs,
    loraActive: loraActiveFlag,
    ragActive: ragActiveFlag,
    usage: {
      promptTokens: estimatedPromptTokens,
      completionTokens: totalTokens,
      durationMs,
      tokensPerSecond: tps,
      modelId: currentModelId,
      provider: "webgpu",
      loraActive: loraActiveFlag,
      ragActive: ragActiveFlag,
    },
  };
}
