// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
/**
 * Migration 0058: Ongakuka music generation vertex + edge tables (Phase 0).
 *
 * Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
 *   - 4 vertex + 5 edge tables, no MV in this migration
 *   - All cardinality bounded by user generation rate
 *   - No MAX(varchar) anywhere
 *
 * Schema:
 *   vertex_ongakuka_track       — 1 generated track (lyrics/style/status/blob_key)
 *   vertex_ongakuka_stem        — per-stem audio (vocal/inst/drums/bass)
 *   vertex_ongakuka_style       — style reference (prompt or embedding ref)
 *   vertex_ongakuka_generation  — generation event (audit + metering)
 *   edge_ongakuka_has_stem      — track → stem
 *   edge_ongakuka_used_style    — track → style
 *   edge_ongakuka_produced_by   — stem → actor DID
 *   edge_ongakuka_generated_by  — track → generation
 *   edge_ongakuka_regen_lineage — generation → parent generation
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ongakuka_track (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      project_id       VARCHAR,
      title            VARCHAR,
      style            VARCHAR,
      language         VARCHAR,
      bpm              INT,
      duration_sec     INT,
      status           VARCHAR,
      blob_key         VARCHAR,
      mime_type        VARCHAR,
      model_id         VARCHAR,
      seed             BIGINT,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ongakuka_stem (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      track_uri        VARCHAR,
      kind             VARCHAR,
      blob_key         VARCHAR,
      mime_type        VARCHAR,
      duration_sec     INT,
      loudness_lufs    DOUBLE PRECISION,
      actor_did        VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ongakuka_style (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    INT,
      owner_did          VARCHAR,
      name               VARCHAR,
      kind               VARCHAR,
      prompt             VARCHAR,
      embedding_blob_key VARCHAR,
      embedding_dim      INT,
      embedding_model    VARCHAR,
      license            VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ongakuka_generation (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    INT,
      owner_did          VARCHAR,
      target_uri         VARCHAR,
      stage              VARCHAR,
      actor_did          VARCHAR,
      model_id           VARCHAR,
      params             VARCHAR,
      prompt_tokens      INT,
      completion_tokens  INT,
      audio_sec          DOUBLE PRECISION,
      inference_ms       INT,
      credits_consumer   INT,
      credits_operator   INT,
      node               VARCHAR,
      status             VARCHAR,
      reject_reason      VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  for (const t of [
    "edge_ongakuka_has_stem",
    "edge_ongakuka_used_style",
    "edge_ongakuka_produced_by",
    "edge_ongakuka_generated_by",
    "edge_ongakuka_regen_lineage",
  ]) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.raw(t)} (
        edge_id          VARCHAR PRIMARY KEY,
        src_vid          VARCHAR,
        dst_vid          VARCHAR,
        _seq             BIGINT,
        created_date     DATE,
        sensitivity_ord  INT,
        owner_did        VARCHAR
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    "edge_ongakuka_regen_lineage",
    "edge_ongakuka_generated_by",
    "edge_ongakuka_produced_by",
    "edge_ongakuka_used_style",
    "edge_ongakuka_has_stem",
    "vertex_ongakuka_generation",
    "vertex_ongakuka_style",
    "vertex_ongakuka_stem",
    "vertex_ongakuka_track",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
