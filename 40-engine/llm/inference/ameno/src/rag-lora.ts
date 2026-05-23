/**
 * RAG-LoRA adapter selection via DuckDB-WASM.
 *
 * Queries kagami P10v2 per-label Parquet data to:
 * 1. Perform RAG search (embedding cosine similarity).
 * 2. Select optimal LoRA adapter(s) based on RAG result domain distribution.
 * 3. Compute adapter merge weights for multi-adapter composition.
 *
 * Operates entirely client-side — DuckDB-WASM + R2 Parquet, zero egress.
 */
import type { LoadedLoraAdapter, AdapterMergeSpec } from "./lora-runtime";
import { fetchLoraAdapter } from "./lora-runtime";

/**
 * Single RAG search result from DuckDB-WASM cosine similarity query.
 *
 * Represents a kagami vertex that matched the query embedding.
 */
export interface RagResult {
  /** Kagami vertex ID of the matched document. */
  vertexId: string;
  /** Graph label of the matched vertex (e.g. `"Post"`, `"Article"`). */
  label: string;
  /** Text content of the matched vertex. */
  text: string;
  /** Cosine similarity score in range `[0.0, 1.0]`. */
  similarity: number;
}

/**
 * LoRA adapter candidate discovered from kagami `LoraAdapter` vertices.
 *
 * Scored by domain affinity relative to RAG search results.
 */
export interface AdapterCandidate {
  /** Adapter identifier matching the R2 key segment. */
  adapterId: string;
  /** Owner actor DID. */
  actorDid: string;
  /** Domain tag from the adapter's `region` column (e.g. `"finance"`). */
  domain: string;
  /** Affinity score computed from `ADAPTER_AFFINITY` edge weights × RAG label counts. */
  score: number;
  /** Adapter status (`"active"` adapters only are returned by default). */
  status: string;
}

/**
 * Complete RAG-LoRA context ready for inference.
 *
 * Contains RAG documents for prompt injection and selected adapter
 * merge specs for weight-space personalization.
 */
export interface RagLoraContext {
  /** Top-K RAG documents for context injection into the system prompt. */
  ragDocuments: RagResult[];
  /** Selected adapter merge specs (empty if no adapters match the query domain). */
  adapterSpecs: AdapterMergeSpec[];
  /** Label → count distribution of RAG results, used for adapter scoring. */
  domainDistribution: Map<string, number>;
}

/**
 * Minimal DuckDB-WASM connection interface.
 *
 * Compatible with `@duckdb/duckdb-wasm` `AsyncDuckDBConnection`.
 */
interface DuckDBConnection {
  /** Execute a SQL query and return typed rows. */
  query<T = Record<string, unknown>>(sql: string): Promise<{ toArray(): T[] }>;
}

/**
 * Execute RAG vector search on a kagami P10v2 per-label table via DuckDB-WASM.
 *
 * Computes `list_cosine_similarity(embedding, queryEmbedding)` across all
 * vertices with non-null embeddings.
 *
 * @param conn - DuckDB-WASM connection with per-label Parquet tables loaded from R2.
 * @param queryEmbedding - Query embedding vector as `number[]`. Must match the
 *   dimensionality of `embedding` in the target table.
 * @param topK - Maximum number of results to return. Defaults to 20.
 * @param minSimilarity - Minimum cosine similarity threshold. Results below
 *   this threshold are filtered out post-query. Defaults to 0.5.
 * @param label - Vertex label to search (P10v2 per-label table). Defaults to `"Post"`.
 * @returns Sorted RAG results (highest similarity first), filtered by `minSimilarity`.
 */
export async function ragSearch(
  conn: DuckDBConnection,
  queryEmbedding: number[],
  topK = 20,
  minSimilarity = 0.5,
  label = "Post",
): Promise<RagResult[]> {
  const embStr = `[${queryEmbedding.join(",")}]`;
  const table = `graphar.vertex_${label.toLowerCase()}`;

  const result = await conn.query<{
    vertex_id: string;
    text: string;
    similarity: number;
  }>(`
    SELECT
      vertex_id,
      text,
      list_cosine_similarity(
        embedding,
        ${embStr}::FLOAT[]
      ) AS similarity
    FROM ${table}
    WHERE embedding IS NOT NULL
      AND text IS NOT NULL
    ORDER BY similarity DESC
    LIMIT ${topK}
  `);

  return result
    .toArray()
    .filter((r) => r.similarity >= minSimilarity)
    .map((r) => ({
      vertexId: r.vertex_id,
      label,
      text: r.text,
      similarity: r.similarity,
    }));
}

/**
 * Query available LoRA adapters for an actor from kagami typed LoRA adapter table.
 *
 * Filters the `LoraAdapter` label vertices by `did` and `status = 'active'`.
 * Returns at most 100 adapters.
 *
 * @param conn - DuckDB-WASM connection with per-label Parquet tables loaded from R2.
 * @param actorDid - Actor DID to scope adapters (exact match on `did` column).
 * @returns Adapter candidates with initial score of 0 (scored later by {@link selectAdapters}).
 */
export async function listActorAdapters(
  conn: DuckDBConnection,
  actorDid: string,
): Promise<AdapterCandidate[]> {
  const result = await conn.query<{
    vertex_id: string;
    did: string;
    adapter_id: string;
    domain: string;
    status: string;
  }>(`
    SELECT vertex_id, did, adapter_id, domain, status
    FROM graphar.vertex_lora_adapter
    WHERE did = '${escapeSql(actorDid)}'
      AND status = 'active'
    LIMIT 100
  `);

  return result.toArray().map((r) => ({
    adapterId: r.adapter_id,
    actorDid: r.did,
    domain: r.domain || "general",
    score: 0,
    status: r.status || "active",
  }));
}

/**
 * Select optimal LoRA adapter(s) based on RAG result domain distribution.
 *
 * Scoring algorithm:
 * 1. Count label occurrences in RAG results (domain distribution).
 * 2. Query `ADAPTER_AFFINITY` edges from document labels to `LoraAdapter` vertices.
 * 3. Score each adapter as `Σ(edge_weight × label_count)` across all affinity edges.
 * 4. If no affinity edges exist, assign equal scores to all actor adapters (uniform fallback).
 * 5. Return top-scored adapters, sorted descending.
 *
 * @param conn - DuckDB-WASM connection with per-label Parquet tables loaded from R2.
 * @param ragResults - RAG search results from {@link ragSearch}.
 * @param actorDid - Actor DID to scope adapter candidates.
 * @param maxAdapters - Maximum number of adapters to return. Defaults to 3.
 * @returns Scored and sorted adapter candidates (highest score first).
 */
export async function selectAdapters(
  conn: DuckDBConnection,
  ragResults: RagResult[],
  actorDid: string,
  maxAdapters = 3,
): Promise<AdapterCandidate[]> {
  if (ragResults.length === 0) return [];

  // Compute domain distribution from RAG results
  const labelCounts = new Map<string, number>();
  for (const r of ragResults) {
    labelCounts.set(r.label, (labelCounts.get(r.label) || 0) + 1);
  }

  // Query adapter affinity edges: (doc label) -[ADAPTER_AFFINITY]-> (LoraAdapter)
  const labels = [...labelCounts.keys()].map((l) => `'${escapeSql(l)}'`).join(",");

  const affinityResult = await conn.query<{
    dst_vid: string;
    src_label: string;
    weight: number;
  }>(`
    SELECT dst_vid, src_label, COALESCE(weight, 1.0) AS weight
    FROM graphar.edge_lora_adapter_affinity
    WHERE dst_label = 'LoraAdapter'
      AND src_label IN (${labels})
    LIMIT 1000
  `);

  // Score adapters by weighted affinity
  const adapterScores = new Map<string, number>();
  for (const row of affinityResult.toArray()) {
    const labelCount = labelCounts.get(row.src_label) || 0;
    const score = row.weight * labelCount;
    adapterScores.set(row.dst_vid, (adapterScores.get(row.dst_vid) || 0) + score);
  }

  // Get adapter metadata
  const adapters = await listActorAdapters(conn, actorDid);

  // Merge scores with actor adapters
  for (const adapter of adapters) {
    const vertexId = `lora:${adapter.actorDid}:${adapter.adapterId}`;
    adapter.score = adapterScores.get(vertexId) || 0;
  }

  // If no affinity edges exist, assign equal scores to all actor adapters
  if (adapterScores.size === 0 && adapters.length > 0) {
    for (const adapter of adapters) {
      adapter.score = 1.0;
    }
  }

  return adapters
    .sort((a, b) => b.score - a.score)
    .slice(0, maxAdapters);
}

/**
 * End-to-end RAG-LoRA pipeline: search → select adapters → fetch weights → prepare merge specs.
 *
 * Orchestrates the full client-side pipeline:
 * 1. {@link ragSearch} — find relevant documents via embedding similarity.
 * 2. {@link selectAdapters} — score adapters by domain affinity to RAG results.
 * 3. {@link fetchLoraAdapter} — download adapter weights from R2 CDN (parallel).
 * 4. Compute merge weights proportional to adapter scores.
 *
 * All operations are client-side (DuckDB-WASM + R2 CDN fetch). Zero server compute.
 *
 * @param conn - DuckDB-WASM connection with the `P9_TABLE` table loaded from R2 Parquet.
 * @param queryEmbedding - Query embedding vector for RAG similarity search.
 * @param actorDid - Actor DID for per-actor adapter scoping.
 * @param pdsBaseUrl - PDS base URL for R2 adapter weight fetch (e.g. `"https://atproto.etzhayyim.com"`).
 * @param options - Optional pipeline parameters.
 * @param options.topK - RAG search top-K limit. Defaults to 20.
 * @param options.minSimilarity - RAG search minimum similarity. Defaults to 0.5.
 * @param options.maxAdapters - Maximum adapters to merge. Defaults to 3.
 * @returns Complete RAG-LoRA context with documents, adapter specs, and domain distribution.
 */
export async function ragLoraSelect(
  conn: DuckDBConnection,
  queryEmbedding: number[],
  actorDid: string,
  pdsBaseUrl: string,
  options: {
    topK?: number;
    minSimilarity?: number;
    maxAdapters?: number;
  } = {},
): Promise<RagLoraContext> {
  const { topK = 20, minSimilarity = 0.5, maxAdapters = 3 } = options;

  // 1. RAG search
  const ragDocuments = await ragSearch(conn, queryEmbedding, topK, minSimilarity);

  // 2. Domain distribution
  const domainDistribution = new Map<string, number>();
  for (const doc of ragDocuments) {
    domainDistribution.set(doc.label, (domainDistribution.get(doc.label) || 0) + 1);
  }

  // 3. Select adapters
  const candidates = await selectAdapters(conn, ragDocuments, actorDid, maxAdapters);

  if (candidates.length === 0) {
    return { ragDocuments, adapterSpecs: [], domainDistribution };
  }

  // 4. Fetch and load adapters from R2
  const totalScore = candidates.reduce((sum, c) => sum + c.score, 0);
  const adapterSpecs: AdapterMergeSpec[] = [];

  const fetchPromises = candidates.map(async (candidate) => {
    const adapter = await fetchLoraAdapter(
      candidate.actorDid,
      candidate.adapterId,
      pdsBaseUrl,
    );
    const mergeWeight = totalScore > 0 ? candidate.score / totalScore : 1.0 / candidates.length;
    return { adapter, weight: mergeWeight };
  });

  const loaded = await Promise.all(fetchPromises);
  adapterSpecs.push(...loaded);

  return { ragDocuments, adapterSpecs, domainDistribution };
}

/**
 * Build a RAG context string for system prompt injection.
 *
 * Formats RAG documents as a numbered list with label and similarity score.
 * Respects an approximate token budget by estimating ~4 chars per token.
 * Stops adding documents when the budget would be exceeded.
 *
 * @param ragResults - RAG search results from {@link ragSearch}, ordered by similarity.
 * @param maxTokensBudget - Approximate token budget for the context block. Defaults to 2048.
 * @returns Formatted context string prefixed with `[Context from knowledge graph]`,
 *   or empty string if no results.
 */
export function buildRagContextPrompt(
  ragResults: RagResult[],
  maxTokensBudget = 2048,
): string {
  if (ragResults.length === 0) return "";

  const lines: string[] = ["[Context from knowledge graph]"];
  let approxTokens = 10;

  for (let i = 0; i < ragResults.length; i++) {
    const doc = ragResults[i];
    const line = `[${i + 1}] (${doc.label}, sim=${doc.similarity.toFixed(2)}) ${doc.text}`;
    const lineTokens = Math.ceil(line.length / 4);

    if (approxTokens + lineTokens > maxTokensBudget) break;

    lines.push(line);
    approxTokens += lineTokens;
  }

  return lines.join("\n");
}

/**
 * Escape single quotes for DuckDB SQL string literals.
 *
 * Doubles each `'` to prevent SQL injection in template queries.
 *
 * @param s - Raw string value to escape.
 * @returns Escaped string safe for use in SQL `'...'` literals.
 */
function escapeSql(s: string): string {
  return s.replace(/'/g, "''");
}
