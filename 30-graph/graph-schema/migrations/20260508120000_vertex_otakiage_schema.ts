import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (item / handover / ritual / certificate are public-by-design;
//          donor/recipient PII lives in T3 Preferences, not in these tables)

/**
 * otakiage.etzhayyim.com Phase 1 — Reuse & Ritual Platform schema
 * (ADR-2605081700 + ADR-0036 Worker-direct Hyperdrive +
 *  ADR-0056 BPMN-as-actor + ADR-2604282300 T2 = pymagatama + Zeebe).
 *
 * Tables (6 vertex + 4 edge):
 *   vertex_otakiage_item            物品 (category, story, photo[], h3_cell, mode, state)
 *   vertex_otakiage_reuse_request   引取希望
 *   vertex_otakiage_handover        譲渡完了 (terminal)
 *   vertex_otakiage_ritual          供養記録
 *   vertex_otakiage_matsuri         季節祭 (calendar 駆動)
 *   vertex_otakiage_certificate     永続証跡 (Phase 1 = AT Record JSON)
 *   edge_otakiage_item_owner        item → owner DID
 *   edge_otakiage_item_handover     item → handover (reuse 経路)
 *   edge_otakiage_item_ritual       item → ritual (供養経路)
 *   edge_otakiage_ritual_certificate ritual → certificate
 *
 * Streaming MVs (4):
 *   mv_otakiage_reuse_match_by_h3     reuse_open item を H3 cell 別に集計
 *   mv_otakiage_matsuri_upcoming      直近 90 日 + 申込状況
 *   mv_otakiage_items_by_state        state 別件数 (coverage 表示)
 *   mv_otakiage_donor_lifetime_count  寄贈者 DID 別累積件数
 *
 * State machine (item.state):
 *   submitted → reuse_open (TTL 30d, 自動遷移)
 *     ├─ reuse_matched → handed_over (terminal, T1 social derive)
 *     └─ reuse_expired
 *          └─ ritual_pending (家具/家電は遷移しない、reuse_only モード)
 *               └─ ritualized (terminal, certificate 発行)
 *
 * Mode (item.mode) — category から auto-derive:
 *   ehon/jidousho/nuigurumi/ningyo/omocha → reuse_then_ritual
 *   kagu/kaden                            → reuse_only
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex tables ──────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_item (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      item_id varchar NOT NULL,
      category varchar NOT NULL,
      title varchar NOT NULL,
      story_text varchar,
      photo_blob_keys varchar,
      h3_cell varchar,
      h3_res int,
      lat double precision,
      lng double precision,
      weight_kg_class varchar,
      mode varchar NOT NULL,
      state varchar NOT NULL,
      donor_did varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_reuse_request (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      request_id varchar NOT NULL,
      item_uri varchar NOT NULL,
      requester_did varchar NOT NULL,
      message varchar,
      h3_cell varchar,
      lat double precision,
      lng double precision,
      distance_km double precision,
      preferred_handover_date date,
      state varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_handover (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      handover_id varchar NOT NULL,
      item_uri varchar NOT NULL,
      reuse_request_uri varchar,
      donor_did varchar NOT NULL,
      recipient_did varchar NOT NULL,
      handover_at varchar NOT NULL,
      handover_photo_blob_key varchar,
      gratitude_text varchar,
      social_announce_uri varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_ritual (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      ritual_id varchar NOT NULL,
      matsuri_uri varchar NOT NULL,
      item_uris varchar,
      item_count int,
      ceremony_date varchar NOT NULL,
      ceremony_photo_blob_key varchar,
      certificate_uri varchar,
      state varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_matsuri (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      matsuri_id varchar NOT NULL,
      name varchar NOT NULL,
      category_scope varchar NOT NULL,
      scheduled_date date NOT NULL,
      capacity int,
      registered_count int,
      location_h3 varchar,
      description varchar,
      state varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_certificate (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      certificate_id varchar NOT NULL,
      ritual_uri varchar NOT NULL,
      matsuri_uri varchar,
      item_uris varchar,
      item_count int,
      donor_dids varchar,
      issued_at varchar NOT NULL,
      issuer_did varchar NOT NULL,
      issuer_name varchar,
      display_text varchar,
      category_breakdown varchar,
      photo_blob_key varchar,
      certificate_json varchar,
      anchor_token_id varchar,
      version varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Edge tables ────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS edge_otakiage_item_owner (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_otakiage_item_handover (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_otakiage_item_ritual (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_otakiage_ritual_certificate (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────
  // Note: GROUP BY cardinality は意図的に低く保つ (h3 cell ~ 10K + state 7 + category 7)。
  // distinct h3_cell × category < 100K で MV memory safety guardrails 内。

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_reuse_match_by_h3 AS
      SELECT
        h3_cell,
        category,
        weight_kg_class,
        COUNT(*) AS open_count,
        MIN(created_at) AS earliest_listed_at
      FROM vertex_otakiage_item
      WHERE state = 'reuse_open' AND h3_cell IS NOT NULL
      GROUP BY h3_cell, category, weight_kg_class;
  `.execute(db);

  // RW does not accept CURRENT_DATE in VIEW/MV WHERE; consumer applies date window at query time.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_matsuri_upcoming AS
      SELECT
        vertex_id,
        matsuri_id,
        name,
        category_scope,
        scheduled_date,
        capacity,
        registered_count,
        location_h3,
        state
      FROM vertex_otakiage_matsuri
      WHERE state IN ('open', 'preparing');
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_items_by_state AS
      SELECT
        state,
        category,
        COUNT(*) AS item_count
      FROM vertex_otakiage_item
      GROUP BY state, category;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_donor_lifetime_count AS
      SELECT
        donor_did,
        COUNT(*) AS submitted_count,
        SUM(CASE WHEN state = 'handed_over' THEN 1 ELSE 0 END) AS handed_over_count,
        SUM(CASE WHEN state = 'ritualized'  THEN 1 ELSE 0 END) AS ritualized_count
      FROM vertex_otakiage_item
      GROUP BY donor_did;
  `.execute(db);

  // ── Grants ─────────────────────────────────────────────────────────
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_item             TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_item             TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_reuse_request    TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_reuse_request    TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_handover         TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_handover         TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_ritual           TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_ritual           TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_matsuri          TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_matsuri          TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_certificate      TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_certificate      TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_owner         TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_owner         TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_handover      TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_handover      TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_ritual        TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_item_ritual        TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_ritual_certificate TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_otakiage_ritual_certificate TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_donor_lifetime_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_items_by_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_matsuri_upcoming`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_reuse_match_by_h3`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_otakiage_ritual_certificate`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_otakiage_item_ritual`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_otakiage_item_handover`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_otakiage_item_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_certificate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_matsuri`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_ritual`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_handover`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_reuse_request`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_item`.execute(db);
}
