/**
 * ADR-0057 follow-up — per-kind typed Kysely vertex/edge tables for mangaka.
 *
 * Why: ADR-0057 originally wrote into the catch-all `vertex_mangaka` (kind
 * discriminator) which then projects through the lossy `vertex_repo_record`
 * MV. The 2026-04-25 cluster recovery exposed: PDS createRecord returns
 * 200 + URI but the MV projection dropped the row (Bulma case — commit
 * present in `vertex_repo_commit`, missing in `vertex_repo_record`).
 *
 * Fix: write domain rows directly to per-kind typed tables (bypass the
 * generic projection entirely). ADR-0036 Worker-direct Hyperdrive — Kysely
 * INSERT, 1-RTT synchronous, no MV propagation race.
 *
 * Tables:
 *   - vertex_mangaka_work     (1 row per episode)
 *   - vertex_mangaka_page     (20 rows per episode)
 *   - vertex_mangaka_panel    (60-80 rows per episode)
 *   - edge_mangaka_work_contains_page
 *   - edge_mangaka_page_contains_panel
 *
 * The legacy `vertex_mangaka` (kind discriminator, 20260416233000) is left
 * in place — apps that read via the existing flat view continue to work.
 * New writes go to the typed tables; a follow-up backfill MV unifies reads.
 */
import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_mangaka_work ────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "vertex_mangaka_work" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "protagonist_did"  VARCHAR,
      "protagonist"      VARCHAR,
      "title"            VARCHAR,
      "genre"            VARCHAR,
      "setting"          VARCHAR,
      "page_count"       BIGINT,
      "panel_count"      BIGINT,
      "status"           VARCHAR,
      "cover_cid"        VARCHAR,
      "script_cid"       VARCHAR,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_repo_rkey      ON vertex_mangaka_work (repo, rkey)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_protagonist    ON vertex_mangaka_work (protagonist_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_genre          ON vertex_mangaka_work (genre, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_status_created ON vertex_mangaka_work (status, created_at)`.execute(db);

  // ── vertex_mangaka_page ────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "vertex_mangaka_page" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "work_uri"         VARCHAR,
      "page_num"         BIGINT,
      "act"              VARCHAR,
      "panel_count"      BIGINT,
      "width"            BIGINT,
      "height"           BIGINT,
      "image_cid"        VARCHAR,
      "image_size"       BIGINT,
      "alt_text"         TEXT,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_page_work_pagenum ON vertex_mangaka_page (work_uri, page_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_page_act          ON vertex_mangaka_page (act)`.execute(db);

  // ── vertex_mangaka_panel ───────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "vertex_mangaka_panel" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "page_uri"         VARCHAR,
      "panel_num"        BIGINT,
      "panel_order"      BIGINT,
      "prompt"           TEXT,
      "dialogue_json"    TEXT,
      "image_cid"        VARCHAR,
      "x"                DOUBLE PRECISION,
      "y"                DOUBLE PRECISION,
      "w"                DOUBLE PRECISION,
      "h"                DOUBLE PRECISION,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_panel_page_panelnum ON vertex_mangaka_panel (page_uri, panel_num)`.execute(db);

  // ── edges ──────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "edge_mangaka_work_contains_page" (
      "edge_id"   VARCHAR PRIMARY KEY,
      "src_vid"   VARCHAR,
      "dst_vid"   VARCHAR,
      "page_num"  BIGINT,
      "created_at" VARCHAR,
      "org_id"    VARCHAR,
      "user_id"   VARCHAR,
      "actor_id"  VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_mangaka_work_contains_page_src ON edge_mangaka_work_contains_page (src_vid, page_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_mangaka_work_contains_page_dst ON edge_mangaka_work_contains_page (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS "edge_mangaka_page_contains_panel" (
      "edge_id"   VARCHAR PRIMARY KEY,
      "src_vid"   VARCHAR,
      "dst_vid"   VARCHAR,
      "panel_num" BIGINT,
      "created_at" VARCHAR,
      "org_id"    VARCHAR,
      "user_id"   VARCHAR,
      "actor_id"  VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_mangaka_page_contains_panel_src ON edge_mangaka_page_contains_panel (src_vid, panel_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_mangaka_page_contains_panel_dst ON edge_mangaka_page_contains_panel (dst_vid)`.execute(db);

  // ── view_mangaka_episode_flat ──────────────────────────────────────────
  // Convenience view: 1 row per episode with key fields + page count for getEpisode XRPC.
  await sql`
    CREATE VIEW IF NOT EXISTS view_mangaka_episode_flat AS
    SELECT
      w.vertex_id   AS work_uri,
      w.rkey        AS work_rkey,
      w.protagonist_did,
      w.protagonist,
      w.title,
      w.genre,
      w.setting,
      w.page_count,
      w.panel_count,
      w.status,
      w.cover_cid,
      w.created_at,
      w.org_id,
      (SELECT COUNT(*) FROM vertex_mangaka_page p WHERE p.work_uri = w.vertex_id)  AS page_records,
      (SELECT COUNT(*) FROM vertex_mangaka_panel pn JOIN vertex_mangaka_page p
         ON pn.page_uri = p.vertex_id WHERE p.work_uri = w.vertex_id)              AS panel_records
    FROM vertex_mangaka_work w
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_mangaka_episode_flat`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_mangaka_page_contains_panel_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_mangaka_page_contains_panel_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_mangaka_page_contains_panel`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_mangaka_work_contains_page_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_mangaka_work_contains_page_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_mangaka_work_contains_page`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_panel_page_panelnum`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mangaka_panel`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_page_act`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_page_work_pagenum`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mangaka_page`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_work_status_created`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_work_genre`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_work_protagonist`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mangaka_work_repo_rkey`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mangaka_work`.execute(db);
}
