import { Kysely, sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260501100000: IVF+PQ codebook and PQ-encoded WET chunk table.
 *
 * Adds product-quantization (PQ, M=96 subspaces, K=256 centroids, 768-dim)
 * infrastructure for scalable approximate nearest-neighbour search over
 * vertex_wet_chunk without loading raw 768-dim float32 vectors at query time.
 *
 * Memory: 96 bytes/row (vs 3072 bytes raw) — 32× reduction.
 * Codebook JSON size: ~1.5 MB (96 × 256 × 8 floats × 4 bytes ≈ 786 KB gzip).
 *
 * Related: ADR-2604262359 (RisingWave multimodal vector search topology),
 *          ADR-0044 (RisingWave UDF language strategy — Python External UDF io_threads=100)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // PQ codebook versioned per collection.
  // codebook_json stores [[K][subspace_dim]] per subspace as JSON array of arrays
  // so the full shape is float[M][K][subspace_dim] = float[96][256][8].
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pq_codebook (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      collection_id      VARCHAR NOT NULL,
      version_tag        VARCHAR NOT NULL,
      m_subspaces        BIGINT  NOT NULL DEFAULT 96,
      k_centroids        BIGINT  NOT NULL DEFAULT 256,
      dim                BIGINT  NOT NULL DEFAULT 768,
      subspace_dim       BIGINT  NOT NULL DEFAULT 8,
      n_train_vectors    BIGINT,
      codebook_json      VARCHAR,
      trained_at         VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'active'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_pq_codebook_collection_status
      ON vertex_pq_codebook (collection_id, status)
  `.execute(db);

  // PQ-encoded WET chunks — APPEND ONLY (no in-place updates; new version =
  // new codebook_version + re-encode with fresh INSERT rows).
  // pq_code is stored as base64-encoded 96-byte string (BYTEA not reliably
  // supported in RisingWave APPEND ONLY tables — use VARCHAR base64 instead).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wet_chunk_pq (
      pq_id              VARCHAR PRIMARY KEY,
      chunk_vertex_id    VARCHAR NOT NULL,
      ivf_cluster_id     BIGINT  NOT NULL,
      codebook_version   VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      pq_code            VARCHAR NOT NULL,
      encoded_at         VARCHAR NOT NULL
    ) APPEND ONLY
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wet_chunk_pq_cluster
      ON vertex_wet_chunk_pq (ivf_cluster_id, codebook_version)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wet_chunk_pq_domain
      ON vertex_wet_chunk_pq (domain, ivf_cluster_id, codebook_version)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_wet_chunk_pq_domain`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_wet_chunk_pq_cluster`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wet_chunk_pq`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_pq_codebook_collection_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pq_codebook`.execute(db);
}
