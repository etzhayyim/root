import type { Kysely } from "kysely";
import { sql } from "kysely";

// RisingWave v2.6+ native vector(n) type (ADR-0049 D3 erratum, 2026-04-27).
//
// Original 20260427230000 migration declared `embedding real[]`, predating
// awareness of RisingWave's native vector(n) data type (introduced v2.6,
// 2025-10). v2.6 also ships `<->` / `<=>` / `<+>` / `<#>` distance operators
// and an experimental HNSW index, removing the need for the
// cosine_similarity_real() SQL UDF (20260427230600 — kept harmless, still
// useful for other real[] columns like vertex_profile_fragment.embedding).
//
// This migration converts vertex_legal_corpus_document.embedding from
// real[] to vector(1024) so the searchDocument BPMN can use the native
// `<=>` operator (cosine distance), which is plan-time vectorized.
//
// HNSW index is intentionally NOT added here. RisingWave constraint:
// "Vector indexes can currently be built only on append-only tables or
// materialized views." vertex_legal_corpus_document is non-append-only
// (embedding is UPDATEd after ingest by the embed pipeline). HNSW
// acceleration requires either:
//
//   (a) Redesign as APPEND ONLY: write doc + embedding atomically per row,
//       drop dedupe-then-embed flow.
//   (b) Build append-only MV `mv_legal_corpus_document_searchable` from a
//       paired event log, INCLUDE all query-returned columns.
//
// Both are deferred to Phase B+ when N > ~100K. Brute-force `<=>` over
// real[] / vector(n) on RW's native vectorized executor is acceptable
// for the initial corpus size (<100K).
//
// Refs:
// - https://docs.risingwave.com/sql/data-types/vector
// - https://docs.risingwave.com/processing/vector-indexes
// - https://risingwave.com/blog/risingwave-native-vector-search/

export async function up(db: Kysely<unknown>): Promise<void> {
  // RisingWave 2.8.1 blocks DROP COLUMN on any table that has downstream
  // streaming indexes, even when the column being dropped is not referenced
  // by any of them. Workaround: add a new native vector column `embedding_vec`
  // alongside the old `embedding real[]` column. The old column stays to avoid
  // breaking any index maintenance streams; searchDocument BPMN uses `embedding_vec`.
  // DROP of the old `embedding` column is deferred to a Phase B+ migration once
  // all indexes are rebuilt or the table is restructured as APPEND ONLY.
  //
  // Note: mv_legal_corpus_jurisdiction_coverage was dropped by a prior failed
  // attempt of this migration (DROP MATERIALIZED VIEW IF EXISTS is idempotent).
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_legal_corpus_jurisdiction_coverage`.execute(db);

  await sql`ALTER TABLE vertex_legal_corpus_document ADD COLUMN IF NOT EXISTS embedding_vec vector(1024)`.execute(db);

  // Recreate the MV (same definition as 20260427230000).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_legal_corpus_jurisdiction_coverage AS
      SELECT
        jurisdiction,
        source_id,
        COUNT(*) AS document_count,
        MAX(fetched_at) AS last_fetched_at
      FROM vertex_legal_corpus_document
      GROUP BY jurisdiction, source_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_legal_corpus_document DROP COLUMN IF EXISTS embedding`.execute(db);
  await sql`ALTER TABLE vertex_legal_corpus_document ADD COLUMN embedding real[]`.execute(db);
}
