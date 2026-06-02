import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (manimani — user intake / project / artifact rows. Per-row
//          actor_did + org_did set; raw_text may carry user PII (memos,
//          notes, captured links). Non-federable: AT Repo emit is
//          default block (ADR-2605080800). Visible to org owner + actor.)

/**
 * manimani.etzhayyim.com — LangGraph user-intake routing pipeline schema
 * (ADR-2605080800).
 *
 * Pattern: T3 actor (CF Worker = edge facade only, ADR-2604282300) with
 * LangGraph Server execution runtime (ADR-2605080600). Domain writes go
 * through `createKyselyDb(env.HYPERDRIVE)` direct from LangGraph nodes
 * (ADR-0036). PDS commit pipeline is NOT used for `com.etzhayyim.apps.manimani.*`
 * (non-federable; default block).
 *
 * Tables (4 vertex + 1 edge):
 *
 *   vertex_manimani_intake   — single user input (text / url / file_ref).
 *                              Content-addressed PK (ADR-0041) keyed on
 *                              sha256(actor_did + ts_ms + raw_text_hash).
 *
 *   vertex_manimani_project  — project bucket (auto-emerged or user-named).
 *                              Content-addressed PK keyed on
 *                              sha256(actor_did + slug). project_did is
 *                              path-based sub-DID
 *                              `did:web:manimani.etzhayyim.com:project:{slug}`.
 *
 *   vertex_manimani_artifact — LLM output per (intake, project, processor).
 *                              Content-addressed PK keyed on
 *                              sha256(intake_id + processor + content_hash).
 *
 *   vertex_manimani_run      — LangGraph Server `/runs` instance + thread
 *                              state. PK = run_id = thread_id. checkpoint_json
 *                              stores LangGraph Pregel state snapshot for
 *                              crash recovery / HITL resume via interrupt()
 *                              (Phase B; Phase A is in-process cache).
 *
 *   edge_manimani_belongs_to — intake → project membership. is_primary=true
 *                              row count must equal vertex_manimani_intake
 *                              count (1 primary edge per intake).
 *
 * Streaming MV (2):
 *
 *   mv_manimani_project_active
 *     GROUP BY (project_vertex_id, kind, day) — bounded ~1000 projects ×
 *     30 days × 4 kinds = 120K keys. Filters intakes within last 30 days.
 *     No MAX(varchar). Safe.
 *
 *   mv_manimani_intake_unrouted
 *     Filter-only MV (no GROUP BY). Drains as user re-classifies.
 *     Bounded by `created_at > now() - INTERVAL '14 days'` AND
 *     `artifact_kind IN ('raw_passthrough', 'error')`. Safe.
 *
 * MV memory safety: no high-cardinality GROUP BY on intake_id / artifact_id;
 * project_vertex_id GROUP BY in mv_manimani_project_active is bounded by
 * actual active project count (a single user typically has 20-50 projects).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Tables ────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manimani_intake (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source_kind varchar NOT NULL,
      raw_text varchar,
      source_uri varchar,
      parsed_text varchar,
      lang varchar,
      byte_size bigint,
      ts_ms bigint NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_intake_actor ON vertex_manimani_intake (actor_did, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_intake_org ON vertex_manimani_intake (org_did, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_intake_kind ON vertex_manimani_intake (source_kind, ts_ms)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manimani_project (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      project_did varchar NOT NULL,
      slug varchar NOT NULL,
      title varchar NOT NULL,
      kind varchar NOT NULL,
      initial_tags_csv varchar,
      posterior double precision,
      intake_count bigint,
      last_intake_at varchar,
      status varchar NOT NULL,
      ts_ms bigint NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_project_actor_slug ON vertex_manimani_project (actor_did, slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_project_did ON vertex_manimani_project (project_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_project_status ON vertex_manimani_project (status, last_intake_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_project_kind ON vertex_manimani_project (kind, status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manimani_artifact (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      intake_vertex_id varchar NOT NULL,
      project_vertex_id varchar NOT NULL,
      run_vertex_id varchar NOT NULL,
      artifact_kind varchar NOT NULL,
      content varchar,
      model_id varchar,
      tokens_in int,
      tokens_out int,
      error_text varchar,
      ts_ms bigint NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_artifact_intake ON vertex_manimani_artifact (intake_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_artifact_project ON vertex_manimani_artifact (project_vertex_id, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_artifact_run ON vertex_manimani_artifact (run_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_artifact_kind ON vertex_manimani_artifact (artifact_kind, ts_ms)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manimani_run (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      run_id varchar NOT NULL,
      thread_id varchar NOT NULL,
      intake_vertex_id varchar NOT NULL,
      project_vertex_id varchar,
      status varchar NOT NULL,
      current_node varchar,
      checkpoint_json varchar,
      error_text varchar,
      started_at varchar NOT NULL,
      finished_at varchar,
      cost_jpy_micro bigint,
      llm_tokens_in bigint,
      llm_tokens_out bigint,
      classifier_model_id varchar,
      processor_model_id varchar,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_run_intake ON vertex_manimani_run (intake_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_run_status ON vertex_manimani_run (status, started_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_run_actor ON vertex_manimani_run (actor_did, started_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_manimani_belongs_to (
      edge_id varchar PRIMARY KEY,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      confidence double precision,
      is_primary boolean,
      classification_method varchar,
      created_at varchar NOT NULL,
      org_did varchar NOT NULL,
      actor_did varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_belongs_src ON edge_manimani_belongs_to (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_belongs_dst ON edge_manimani_belongs_to (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manimani_belongs_primary ON edge_manimani_belongs_to (is_primary, dst_vid)`.execute(db);

  // ── Streaming MV ──────────────────────────────────────────────────────

  // Active project view: count intakes per project per kind per day, last 30 days.
  // GROUP BY cardinality bounded by (project × 4 kinds × 30 days). For a single
  // user with 50 active projects this is ~6K keys — well under MV memory budget.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_manimani_project_active AS
      SELECT
        e.dst_vid AS project_vertex_id,
        p.kind,
        p.actor_did,
        p.org_did,
        CAST(to_timestamp(i.ts_ms / 1000.0) AS date) AS day,
        COUNT(*) AS intake_count
      FROM edge_manimani_belongs_to e
      JOIN vertex_manimani_intake i ON i.vertex_id = e.src_vid
      JOIN vertex_manimani_project p ON p.vertex_id = e.dst_vid
      WHERE e.is_primary = true
        AND to_timestamp(i.ts_ms / 1000.0) > now() - INTERVAL '30 days'
      GROUP BY
        e.dst_vid,
        p.kind,
        p.actor_did,
        p.org_did,
        CAST(to_timestamp(i.ts_ms / 1000.0) AS date);
  `.execute(db);

  // Unrouted intake view: artifacts that are deferred or errored, last 14 days.
  // Filter-only (no GROUP BY) so streaming state stays minimal.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_manimani_intake_unrouted AS
      SELECT
        a.intake_vertex_id,
        a.project_vertex_id,
        a.run_vertex_id,
        a.artifact_kind,
        a.actor_did,
        a.org_did,
        a.error_text,
        a.ts_ms
      FROM vertex_manimani_artifact a
      WHERE a.artifact_kind IN ('raw_passthrough', 'error')
        AND to_timestamp(a.ts_ms / 1000.0) > now() - INTERVAL '14 days';
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_manimani_intake_unrouted`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_manimani_project_active`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_manimani_belongs_to`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manimani_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manimani_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manimani_project`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manimani_intake`.execute(db);
}
