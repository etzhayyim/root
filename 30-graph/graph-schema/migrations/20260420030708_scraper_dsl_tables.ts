import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0040 — Scraper DSL persistence (Schema-First LLM-Filled, η=0.788).
 *
 * 4 tables — all follow vertex_ / edge_ convention + RLS 3-col + created_at.
 *   vertex_scraper_source — source URL + fetch strategy (per-publication parent)
 *   vertex_scraper_dsl    — Schema-First DSL row (target schema + LLM hints)
 *   vertex_scraper_run    — execution history (cron + manual)
 *   edge_scraper_emits    — run → emitted target row lineage
 *
 * No JSON columns; nested data (target_columns / extract_hints / edge_emit)
 * stored as TEXT carrying compact JSON, parsed at runtime.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_scraper_source (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      source_url       VARCHAR,
      ministry_did     VARCHAR,
      fetch_method     VARCHAR,
      content_type     VARCHAR,
      ua               VARCHAR,
      rate_ms          BIGINT,
      robots_allow     VARCHAR,
      status           VARCHAR,
      last_fetched_at  VARCHAR,
      last_status      VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vss_ministry ON vertex_scraper_source (ministry_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vss_status   ON vertex_scraper_source (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_scraper_dsl (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      source_vid         VARCHAR,
      dsl_kind           VARCHAR,
      target_table       VARCHAR,
      target_columns     VARCHAR,
      extract_hints      VARCHAR,
      edge_emit          VARCHAR,
      llm_model          VARCHAR,
      max_rows_per_run   BIGINT,
      prompt_override    VARCHAR,
      bpmn_process_id    VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vsd_source   ON vertex_scraper_dsl (source_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vsd_target   ON vertex_scraper_dsl (target_table)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_scraper_run (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      dsl_vid          VARCHAR,
      started_at       VARCHAR,
      finished_at      VARCHAR,
      status           VARCHAR,
      fetched_bytes    BIGINT,
      extracted_rows   BIGINT,
      emitted_records  BIGINT,
      emitted_edges    BIGINT,
      llm_tokens_in    BIGINT,
      llm_tokens_out   BIGINT,
      error_summary    VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vsr_dsl    ON vertex_scraper_run (dsl_vid, started_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vsr_status ON vertex_scraper_run (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_scraper_emits (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      emitted_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      created_at       VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ese_src ON edge_scraper_emits (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ese_dst ON edge_scraper_emits (dst_vid)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_ese_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_ese_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_scraper_emits`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vsr_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vsr_dsl`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_scraper_run`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vsd_target`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vsd_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_scraper_dsl`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vss_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vss_ministry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_scraper_source`.execute(db);
}
