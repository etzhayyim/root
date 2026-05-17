import type { Kysely } from "kysely";
import { sql } from "kysely";

// HuggingFace Hub model catalog ingest schema.
//
// Extends the dataset schema (20260506220000) to cover models.
// API fields sourced from: GET /api/models/{repo_id}
//
// Tables:
//   vertex_hfhub_model          — model card per repo_id
//   edge_hfhub_model_tag        — model → HF tag
//   edge_hfhub_model_task       — model → pipeline_tag / task category
//   edge_hfhub_model_language   — model → BCP-47 lang code
//   edge_hfhub_model_base       — fine-tune → base model (self-referential, by model_id)
//   edge_hfhub_model_dataset    — model trained_on → dataset vertex_id
//   mv_hfhub_model_task_stats   — per-task: count + avg_downloads + param distribution
//   mv_hfhub_library_popularity — per-library: model count
//   mv_hfhub_model_size_bucket  — param bucket distribution (bounded: ~5 buckets)
//
// Also alters vertex_hfhub_filter to add entity_type column (dataset|model|both).

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_hfhub_model ───────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_model (
      vertex_id            VARCHAR PRIMARY KEY,   -- 'hf:model:{repo_id}'
      _seq                 BIGINT,
      created_date         DATE,

      repo_id              VARCHAR NOT NULL,      -- e.g. "google/gemma-4-31B-it"
      author               VARCHAR,
      sha                  VARCHAR,

      -- Primary classification
      pipeline_tag         VARCHAR,               -- text-generation | image-text-to-text | ...
      library_name         VARCHAR,               -- transformers | diffusers | gguf | ...
      model_type           VARCHAR,               -- from config.model_type (llama / qwen2 / gemma4 ...)
      architecture         VARCHAR,               -- config.architectures[0]
      auto_model_class     VARCHAR,               -- transformersInfo.auto_model
      inference_state      VARCHAR,               -- warmed | cold | none

      -- Scale
      num_parameters       BIGINT,                -- safetensors.total (raw param count)
      primary_dtype        VARCHAR,               -- dominant quantization (BF16/F32/Q4_K_M/...)
      used_storage_bytes   BIGINT,                -- usedStorage (sum of sibling file sizes)

      -- Catalog attrs
      license              VARCHAR,               -- cardData.license or tags license:*
      base_model           VARCHAR,               -- cardData.base_model[0] (first parent)
      trending_score       DOUBLE PRECISION,
      downloads_month      BIGINT DEFAULT 0,
      likes                INTEGER DEFAULT 0,
      gated                BOOLEAN DEFAULT FALSE,
      disabled             BOOLEAN DEFAULT FALSE,
      private              BOOLEAN DEFAULT FALSE,

      -- Raw card data
      card_data            VARCHAR,               -- JSON blob of cardData (max 8KB)
      spaces_count         INTEGER DEFAULT 0,     -- length of spaces[] array

      -- Ingest lifecycle
      status               VARCHAR DEFAULT 'pending',
      last_scanned_at      TIMESTAMP,
      error_message        VARCHAR,
      created_at_hf        VARCHAR,               -- original HF createdAt ISO string
      last_modified_hf     VARCHAR,               -- HF lastModified ISO string

      -- ADR-0095 canonical columns
      actor_did            VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',
      org_did              VARCHAR,
      at_did               VARCHAR,
      created_at           TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_author ON vertex_hfhub_model (author)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_pipeline ON vertex_hfhub_model (pipeline_tag)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_library ON vertex_hfhub_model (library_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_status ON vertex_hfhub_model (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_downloads ON vertex_hfhub_model (downloads_month DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_params ON vertex_hfhub_model (num_parameters DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_license ON vertex_hfhub_model (license)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_model_scanned ON vertex_hfhub_model (last_scanned_at)`.execute(db);

  // ── edge_hfhub_model_tag ─────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_model_tag (
      model_id             VARCHAR NOT NULL,      -- FK vertex_hfhub_model.vertex_id
      tag                  VARCHAR NOT NULL,
      PRIMARY KEY (model_id, tag)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_mtag_tag ON edge_hfhub_model_tag (tag)`.execute(db);

  // ── edge_hfhub_model_task ────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_model_task (
      model_id             VARCHAR NOT NULL,
      task_category        VARCHAR NOT NULL,
      PRIMARY KEY (model_id, task_category)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_mtask_task ON edge_hfhub_model_task (task_category)`.execute(db);

  // ── edge_hfhub_model_language ────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_model_language (
      model_id             VARCHAR NOT NULL,
      lang_code            VARCHAR NOT NULL,
      PRIMARY KEY (model_id, lang_code)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_mlang_lang ON edge_hfhub_model_language (lang_code)`.execute(db);

  // ── edge_hfhub_model_base — fine-tune → base model chain ────────────────────
  // base_model_id is the raw string from cardData.base_model (may not yet exist
  // in vertex_hfhub_model — resolved lazily by scan task).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_model_base (
      model_id             VARCHAR NOT NULL,      -- fine-tuned model vertex_id
      base_model_id        VARCHAR NOT NULL,      -- base model repo_id (string, not FK)
      depth                INTEGER DEFAULT 1,     -- lineage depth (1 = direct parent)
      PRIMARY KEY (model_id, base_model_id)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_mbase_base ON edge_hfhub_model_base (base_model_id)`.execute(db);

  // ── edge_hfhub_model_dataset — model trained on dataset ─────────────────────
  // Links vertex_hfhub_model → vertex_hfhub_dataset (cross-type edge).
  // dataset_repo_id stored for lazy resolution; dataset_vertex_id NULL if not yet catalogued.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_model_dataset (
      model_id             VARCHAR NOT NULL,      -- FK vertex_hfhub_model.vertex_id
      dataset_repo_id      VARCHAR NOT NULL,      -- raw dataset name from cardData.datasets
      dataset_vertex_id    VARCHAR,               -- FK vertex_hfhub_dataset.vertex_id (nullable)
      PRIMARY KEY (model_id, dataset_repo_id)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_mds_dataset ON edge_hfhub_model_dataset (dataset_repo_id)`.execute(db);

  // ── Streaming MVs (bounded cardinality) ───────────────────────────────────

  // mv_hfhub_model_task_stats — per pipeline_tag (~50 distinct values)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_model_task_stats AS
    SELECT
      pipeline_tag,
      COUNT(*)                                                        AS model_count,
      SUM(downloads_month)                                            AS total_downloads,
      AVG(downloads_month)                                            AS avg_downloads,
      AVG(num_parameters)    FILTER (WHERE num_parameters IS NOT NULL) AS avg_parameters,
      MAX(num_parameters)                                             AS max_parameters,
      SUM(likes)                                                      AS total_likes
    FROM vertex_hfhub_model
    WHERE pipeline_tag IS NOT NULL
    GROUP BY pipeline_tag
  `.execute(db);

  // mv_hfhub_library_popularity — per library_name (~20 distinct values)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_library_popularity AS
    SELECT
      library_name,
      COUNT(*)              AS model_count,
      SUM(downloads_month)  AS total_downloads,
      MAX(downloads_month)  AS max_downloads
    FROM vertex_hfhub_model
    WHERE library_name IS NOT NULL
    GROUP BY library_name
  `.execute(db);

  // mv_hfhub_model_size_bucket — bounded: 6 param buckets
  // Buckets mirror HF size_categories convention for consistency.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_model_size_bucket AS
    SELECT
      CASE
        WHEN num_parameters IS NULL           THEN 'unknown'
        WHEN num_parameters < 1000000000     THEN 'n<1B'
        WHEN num_parameters < 7000000000     THEN '1B<n<7B'
        WHEN num_parameters < 13000000000    THEN '7B<n<13B'
        WHEN num_parameters < 35000000000    THEN '13B<n<35B'
        WHEN num_parameters < 70000000000    THEN '35B<n<70B'
        ELSE                                      'n>70B'
      END                      AS size_bucket,
      COUNT(*)                 AS model_count,
      AVG(downloads_month)     AS avg_downloads,
      SUM(downloads_month)     AS total_downloads
    FROM vertex_hfhub_model
    GROUP BY 1
  `.execute(db);

  // ── Alter vertex_hfhub_filter: add entity_type (dataset | model | both) ─────
  // Allows re-using the same filter infrastructure for both entity types.
  // ALTER TABLE ADD COLUMN IF NOT EXISTS — RisingWave supports this.
  await sql`
    ALTER TABLE vertex_hfhub_filter
    ADD COLUMN IF NOT EXISTS entity_type VARCHAR DEFAULT 'dataset'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_hfhub_model_size_bucket",
    "mv_hfhub_library_popularity",
    "mv_hfhub_model_task_stats",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const tbl of [
    "edge_hfhub_model_dataset",
    "edge_hfhub_model_base",
    "edge_hfhub_model_language",
    "edge_hfhub_model_task",
    "edge_hfhub_model_tag",
    "vertex_hfhub_model",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(tbl)}`.execute(db);
  }
}
