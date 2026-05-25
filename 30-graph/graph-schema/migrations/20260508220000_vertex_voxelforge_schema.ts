import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (voxelforge — design prompts + run state + artifact metadata.
//          Per-row org_did + actor_did set; prompts may carry user IP
//          (e.g. "build my company HQ at 35.6, 139.6"), classified
//          confidential not Tier-3 PII. Visible to org owner + actor.)

/**
 * voxelforge.etzhayyim.com — LangGraph 3D design pipeline schema (ADR-2605080700).
 *
 * Pattern: T2 actor with LangGraph Server execution runtime
 * (ADR-2605080600). Domain writes go through `createKyselyDb(env.HYPERDRIVE)`
 * direct from the LangGraph nodes (ADR-0036). PDS commit pipeline is NOT
 * used for `app.etzhayyim.apps.voxelforge.*` (non-federable, see federable
 * whitelist in deps.toml — voxelforge is default block).
 *
 * Tables (3 vertex + 1 edge):
 *
 *   vertex_voxelforge_design  — design request (text / image / CAD code).
 *                                Content-addressed PK (ADR-0041) keyed on
 *                                sha256(actor_did + ts_ms + prompt_hash).
 *
 *   vertex_voxelforge_run     — LangGraph Server `/runs` instance + thread
 *                                state. PK = run_id = thread_id (LangGraph
 *                                native). checkpoint_json stores the full
 *                                Pregel state snapshot for crash recovery /
 *                                HITL resume via `interrupt()`.
 *
 *   vertex_voxelforge_artifact — output artifact (.glb / .vox / voxel_grid /
 *                                manifest). Content-addressed PK keyed on
 *                                sha256(b2_key + format).
 *
 *   edge_voxelforge_derived_from — artifact → design lineage (composite
 *                                key src_vid + dst_vid).
 *
 * Streaming MV (1):
 *
 *   mv_voxelforge_artifact_count_by_format
 *     GROUP BY (format, generated_by, day) — bounded ~10 keys × 30d × 4
 *     formats = ~1.2K rows. Safe (no MAX(varchar), narrow keys).
 *
 * MV memory safety: no high-cardinality GROUP BY on artifact_id /
 * vertex_id; only on (format, generated_by, day). All 3 are low-cardinality
 * controlled vocabularies, so streaming agg state stays under 1 MiB.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Tables ────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_voxelforge_design (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      kind varchar NOT NULL,
      prompt varchar,
      cad_code varchar,
      image_url varchar,
      reference_artifact_id varchar,
      target_format varchar NOT NULL,
      target_voxel_dim int,
      palette_json varchar,
      params_json varchar,
      ts_ms bigint NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_design_actor ON vertex_voxelforge_design (actor_did, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_design_org_kind ON vertex_voxelforge_design (org_did, kind)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_voxelforge_run (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      run_id varchar NOT NULL,
      thread_id varchar NOT NULL,
      design_vertex_id varchar NOT NULL,
      status varchar NOT NULL,
      current_node varchar,
      checkpoint_json varchar,
      error_text varchar,
      started_at varchar NOT NULL,
      finished_at varchar,
      cost_jpy_micro bigint,
      runpod_pod_id varchar,
      llm_tokens_in bigint,
      llm_tokens_out bigint,
      gpu_seconds double precision,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_run_design ON vertex_voxelforge_run (design_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_run_status ON vertex_voxelforge_run (status, started_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_run_actor ON vertex_voxelforge_run (actor_did, started_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_voxelforge_artifact (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      design_vertex_id varchar NOT NULL,
      run_vertex_id varchar NOT NULL,
      format varchar NOT NULL,
      b2_bucket varchar NOT NULL,
      b2_key varchar NOT NULL,
      sha256_hex varchar NOT NULL,
      byte_size bigint NOT NULL,
      voxel_dim int,
      polygon_count bigint,
      vertex_count bigint,
      generated_by varchar NOT NULL,
      ts_ms bigint NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_artifact_design ON vertex_voxelforge_artifact (design_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_artifact_run ON vertex_voxelforge_artifact (run_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_artifact_format ON vertex_voxelforge_artifact (format, ts_ms)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_voxelforge_derived_from (
      edge_id varchar PRIMARY KEY,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      derivation_kind varchar,
      created_at varchar NOT NULL,
      org_did varchar NOT NULL,
      actor_did varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_derived_src ON edge_voxelforge_derived_from (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_voxelforge_derived_dst ON edge_voxelforge_derived_from (dst_vid)`.execute(db);

  // ── Streaming MV ──────────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_voxelforge_artifact_count_by_format AS
      SELECT
        format,
        generated_by,
        CAST(to_timestamp(ts_ms / 1000.0) AS date) AS day,
        COUNT(*) AS artifact_count,
        SUM(byte_size) AS total_byte_size
      FROM vertex_voxelforge_artifact
      GROUP BY format, generated_by, CAST(to_timestamp(ts_ms / 1000.0) AS date);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_voxelforge_artifact_count_by_format`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_voxelforge_derived_from`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_voxelforge_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_voxelforge_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_voxelforge_design`.execute(db);
}
