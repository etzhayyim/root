import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * gameka.etzhayyim.com studio actor — 4 vertex + 2 edge tables (ADR 2604250900).
 *
 * P1 wires only proposeGame → vertex_gameka_spec; the remaining tables
 * (artifact / qa / title) are created up front so generateGame /
 * playtestGame / publishGame phases land without follow-up migrations.
 *
 * vertex_id convention (ADR-0036 + ADR-0056 addendum):
 *   at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameSpec/{rkey}
 *   at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.buildArtifact/{rkey}
 *   at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameQa/{rkey}
 *   at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameTitle/{slug}
 *
 * RW caveats honoured: VARCHAR for JSON payload columns, DOUBLE PRECISION
 * for monetary / score, no MV (ADR-0026 §MV Memory Safety Guardrails).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ─── vertex_gameka_spec — LangGraph deliberation output ──────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gameka_spec (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      spec_id VARCHAR, brief VARCHAR, title VARCHAR, slug VARCHAR,
      genre VARCHAR, mechanic_json VARCHAR, scene_json VARCHAR,
      budget_usd DOUBLE PRECISION, score DOUBLE PRECISION, rationale VARCHAR,
      iteration BIGINT, lineage_parent VARCHAR, model_id VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_spec_slug
      ON vertex_gameka_spec (slug)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_spec_score_created
      ON vertex_gameka_spec (score DESC, created_at DESC)
  `.execute(db);

  // ─── vertex_gameka_artifact — kami-codegen build output ──────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gameka_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, spec_id VARCHAR,
      wasm_cid VARCHAR, wasm_size BIGINT, wasm_url VARCHAR,
      build_log_url VARCHAR, build_status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_artifact_spec
      ON vertex_gameka_artifact (spec_id, created_at DESC)
  `.execute(db);

  // ─── vertex_gameka_qa — playtest verdict ─────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gameka_qa (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      qa_id VARCHAR, artifact_id VARCHAR,
      fps_p50 DOUBLE PRECISION, crashes BIGINT, asset_404 BIGINT,
      scene_load_ms BIGINT, llm_score DOUBLE PRECISION,
      publish BOOLEAN, issues_json VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_qa_artifact
      ON vertex_gameka_qa (artifact_id, created_at DESC)
  `.execute(db);

  // ─── vertex_gameka_title — published title (sub-DID anchor) ──────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gameka_title (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      title_id VARCHAR, slug VARCHAR, sub_did VARCHAR,
      parent_spec_id VARCHAR, parent_artifact_id VARCHAR,
      play_url VARCHAR, version VARCHAR,
      published_at VARCHAR, created_at VARCHAR,
      org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_title_slug
      ON vertex_gameka_title (slug)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_title_sub_did
      ON vertex_gameka_title (sub_did)
  `.execute(db);

  // ─── edge_gameka_spec_revises — LangGraph iteration lineage ──────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gameka_spec_revises (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      iteration BIGINT, score_delta DOUBLE PRECISION,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_spec_revises_src
      ON edge_gameka_spec_revises (src_vid)
  `.execute(db);

  // ─── edge_gameka_title_published_by — actor publication graph ────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_gameka_title_published_by (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      published_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_title_published_by_dst
      ON edge_gameka_title_published_by (dst_vid)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_gameka_title_published_by_dst`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gameka_title_published_by`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_spec_revises_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gameka_spec_revises`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_title_sub_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_title_slug`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gameka_title`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_qa_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gameka_qa`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_artifact_spec`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gameka_artifact`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_spec_score_created`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gameka_spec_slug`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gameka_spec`.execute(db);
}
