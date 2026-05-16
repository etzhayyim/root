// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
/**
 * Migration 0059: Yukkuri video generation vertex + edge tables (Phase 0).
 *
 * Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
 *   - 5 vertex + 7 edge tables, no MV in this migration
 *   - All cardinality bounded by user generation rate
 *   - No MAX(varchar) anywhere
 *
 * Schema:
 *   vertex_yukkuri_video       — 1 generated yukkuri video (topic/status/final blob_key)
 *   vertex_yukkuri_scene       — ordered scene within a video
 *   vertex_yukkuri_line        — 1 spoken line (speaker L/R/narrator + tts blob)
 *   vertex_yukkuri_asset       — image/sfx/bgm/character/timeline/video blob
 *   vertex_yukkuri_generation  — generation event (audit + metering)
 *   edge_yukkuri_has_scene     — video → scene
 *   edge_yukkuri_has_line      — scene → line
 *   edge_yukkuri_uses_asset    — scene → asset
 *   edge_yukkuri_voiced_by     — line → actor DID
 *   edge_yukkuri_produced_by   — asset → actor DID
 *   edge_yukkuri_generated_by  — video → generation
 *   edge_yukkuri_regen_lineage — generation → parent generation
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yukkuri_video (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      project_id       VARCHAR,
      title            VARCHAR,
      topic            VARCHAR,
      language         VARCHAR,
      target_sec       INT,
      duration_sec     INT,
      resolution       VARCHAR,
      fps              INT,
      status           VARCHAR,
      blob_key         VARCHAR,
      mime_type        VARCHAR,
      seed             BIGINT,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yukkuri_scene (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      video_uri        VARCHAR,
      idx              INT,
      start_sec        DOUBLE PRECISION,
      duration_sec     DOUBLE PRECISION,
      summary          VARCHAR,
      background_asset_uri VARCHAR,
      bgm_asset_uri    VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yukkuri_line (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      video_uri        VARCHAR,
      scene_uri        VARCHAR,
      idx              INT,
      speaker          VARCHAR,
      text             VARCHAR,
      emotion          VARCHAR,
      voice_preset     VARCHAR,
      voice_blob_key   VARCHAR,
      mime_type        VARCHAR,
      duration_sec     DOUBLE PRECISION,
      phoneme_blob_key VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yukkuri_asset (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  INT,
      owner_did        VARCHAR,
      video_uri        VARCHAR,
      scene_uri        VARCHAR,
      kind             VARCHAR,
      blob_key         VARCHAR,
      mime_type        VARCHAR,
      width            INT,
      height           INT,
      duration_sec     DOUBLE PRECISION,
      loudness_lufs    DOUBLE PRECISION,
      actor_did        VARCHAR,
      source_ref       VARCHAR,
      license          VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yukkuri_generation (
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
      video_sec          DOUBLE PRECISION,
      render_backend     VARCHAR,
      inference_ms       INT,
      render_ms          INT,
      credits_consumer   INT,
      credits_operator   INT,
      node               VARCHAR,
      status             VARCHAR,
      reject_reason      VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  for (const t of [
    "edge_yukkuri_has_scene",
    "edge_yukkuri_has_line",
    "edge_yukkuri_uses_asset",
    "edge_yukkuri_voiced_by",
    "edge_yukkuri_produced_by",
    "edge_yukkuri_generated_by",
    "edge_yukkuri_regen_lineage",
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
    "edge_yukkuri_regen_lineage",
    "edge_yukkuri_generated_by",
    "edge_yukkuri_produced_by",
    "edge_yukkuri_voiced_by",
    "edge_yukkuri_uses_asset",
    "edge_yukkuri_has_line",
    "edge_yukkuri_has_scene",
    "vertex_yukkuri_generation",
    "vertex_yukkuri_asset",
    "vertex_yukkuri_line",
    "vertex_yukkuri_scene",
    "vertex_yukkuri_video",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
