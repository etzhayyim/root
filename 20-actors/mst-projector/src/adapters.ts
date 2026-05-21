/**
 * mst-projector LanceDB + DuckDB adapter STUBS.
 *
 * These are NOT runnable as-is — the LanceDB / DuckDB packages are not
 * declared as dependencies in this package. Phase 3 production deployment
 * installs:
 *   - @lancedb/lancedb (vector store for IVF text search)
 *   - duckdb-async (in-process OLAP for aggregates + inverted indexes)
 *   - @huggingface/inference (embedding model client)
 *
 * Per ADR-2605212000 §"Storage": Phase 3 progression is:
 *   - Phase 3a: in-memory (Phase 3 reference, always available)
 *   - Phase 3b: DuckDB (production aggregate + attribute persistence)
 *   - Phase 3c: LanceDB (production IVF vector text search)
 */

/**
 * Marker interface for pluggable storage backend adapters.
 */
export interface BackendAdapter {
  readonly kind: "inmemory" | "lancedb" | "duckdb";
  init(): Promise<void>;
  close(): Promise<void>;
}

/**
 * LanceDB text index stub.
 */
export class LanceDbTextIndexStub implements BackendAdapter {
  readonly kind = "lancedb" as const;

  async init(): Promise<void> {
    throw new Error(
      "LanceDB adapter not installed — fall back to InMemoryTextIndex. " +
        "Production deployment: install @lancedb/lancedb and " +
        "@huggingface/inference or @xenova/transformers.",
    );
  }

  async close(): Promise<void> {}
}

/**
 * DuckDB aggregate + attribute index stub.
 */
export class DuckDbAggregateIndexStub implements BackendAdapter {
  readonly kind = "duckdb" as const;

  async init(): Promise<void> {
    throw new Error(
      "DuckDB adapter not installed — fall back to InMemoryAggregateIndex. " +
        "Production deployment: install duckdb-async.",
    );
  }

  async close(): Promise<void> {}
}

/**
 * Embedding provider stub.
 */
export class EmbeddingProviderStub {
  async embed(_text: string): Promise<Float32Array> {
    throw new Error(
      "Embedding provider not configured — " +
        "set HF_INFERENCE_TOKEN for API-based embeddings or " +
        "install @xenova/transformers for local embeddings.",
    );
  }
}
