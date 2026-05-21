/**
 * HuggingFace Inference API embedder.
 *
 * Calls out to `api-inference.huggingface.co` for embedding via HTTP.
 * Useful when local transformers.js is too slow or unavailable.
 *
 * Install: pnpm add @huggingface/inference
 *
 * Set `HF_INFERENCE_TOKEN` env var (from https://huggingface.co/settings/tokens).
 *
 * Per ADR-2605212000 §Phase 3c: embedding provider unification.
 */

import type { EmbeddingProvider } from "../adapters.js";

export interface HuggingFaceEmbeddingConfig {
  /** HuggingFace model id, e.g. "sentence-transformers/all-MiniLM-L6-v2". */
  model: string;
  /** API token (from HF_INFERENCE_TOKEN env var or explicit). */
  apiKey: string;
  /** Expected embedding dimension (must match the model). */
  vectorDim: number;
}

/**
 * Create a HuggingFace Inference API embedder.
 *
 * Throws a clear error if the API token is missing or invalid.
 * Uses fetch internally (available in Node 18+).
 */
export async function createHuggingFaceEmbedder(
  config: HuggingFaceEmbeddingConfig,
): Promise<EmbeddingProvider> {
  if (!config.apiKey) {
    throw new Error(
      "HuggingFace embedder: apiKey is required. " +
        "Set HF_INFERENCE_TOKEN env var or pass it explicitly.",
    );
  }

  const modelId = config.model;
  const dim = config.vectorDim;
  const apiKey = config.apiKey;

  const embedder: EmbeddingProvider = {
    dim,
    modelId,
    async embed(text: string): Promise<Float32Array> {
      const res = await fetch(
        `https://api-inference.huggingface.co/pipeline/feature-extraction/${modelId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${apiKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            inputs: text,
            options: { wait_for_model: true },
          }),
        },
      );

      if (!res.ok) {
        throw new Error(
          `HuggingFace Inference ${res.status}: ${await res.text()}`,
        );
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const j: number[] | number[][] = await res.json();

      // Some models return [[...]], others [...]
      const arr = Array.isArray(j[0]) ? (j[0] as number[]) : (j as number[]);

      if (arr.length !== dim) {
        throw new Error(
          `HuggingFace Inference returned ${arr.length}-dim vector, expected ${dim}`,
        );
      }

      return Float32Array.from(arr);
    },
  };

  return embedder;
}

/**
 * Production preset configs for common HuggingFace embedding models.
 *
 * API-based embedders are slower than local transformers.js but can use
 * larger/better models if the latency budget permits.
 *
 * Pick by use-case:
 *   - sentence-transformers/all-MiniLM-L6-v2 — 384-dim, fast, general-purpose
 *   - sentence-transformers/bge-large-en-v1.5 — 1024-dim, higher quality
 */
export const HUGGINGFACE_PRESETS = {
  "all-MiniLM-L6-v2": {
    model: "sentence-transformers/all-MiniLM-L6-v2" as const,
    vectorDim: 384 as const,
  },
  "bge-large-en-v1.5": {
    model: "sentence-transformers/bge-large-en-v1.5" as const,
    vectorDim: 1024 as const,
  },
} as const;
