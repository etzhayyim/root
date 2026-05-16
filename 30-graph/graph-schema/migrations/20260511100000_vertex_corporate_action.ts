import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Corporate governance action schema — 法人の登記変更・定款変更・株主総会決議を
 * 追跡するための vertex / edge / mv。
 *
 * テーブル構成:
 *   vertex_corporate_action       — 1アクション = 1行 (定款変更、役員変更、本店移転 等)
 *   vertex_corporate_action_item  — アクション内の個別変更項目 (事業目的変更、任期変更 等)
 *   edge_corporate_action_document — corporate_action → office_document / local_file
 *   mv_corporate_action_status    — アクション別ステータスサマリ (登記完了率)
 *
 * action_type enum:
 *   teikan_henkou   定款変更 (全般)
 *   mokuteki_henkou 事業目的変更 (登記必要)
 *   yakuin_henkou   役員変更 (登記必要)
 *   honten_iten     本店移転 (登記必要)
 *   kikan_henkou    機関設計変更 (取締役会廃止等)
 *   kabushiki       株式関連 (発行・スクイーズアウト等)
 *
 * status enum:
 *   draft       → 草案作成中
 *   approved    → 株主総会/取締役会承認済
 *   filed       → 法務局申請済
 *   registered  → 登記完了 (履歴事項全部証明書取得済)
 *   cancelled   → 中止
 *
 * resolution_type enum:
 *   teiji_sokai    定時株主総会
 *   rinji_sokai    臨時株主総会
 *   shomen_ketsugi 書面決議 (会社法318条)
 *   torishimarikai 取締役会決議
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_corporate_action ──────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_corporate_action (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,

      action_code       VARCHAR NOT NULL,
      action_type       VARCHAR NOT NULL,
      legal_entity_did  VARCHAR NOT NULL,
      title             VARCHAR NOT NULL,
      status            VARCHAR NOT NULL DEFAULT 'draft',

      resolution_type   VARCHAR,
      resolution_date   DATE,
      filing_date       DATE,
      registration_date DATE,
      registration_office VARCHAR,
      registration_tax_jpy BIGINT,

      responsible_did   VARCHAR,
      notes             TEXT,

      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`CREATE UNIQUE INDEX IF NOT EXISTS idx_corporate_action_code
            ON vertex_corporate_action (action_code)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_corporate_action_entity_status
            ON vertex_corporate_action (legal_entity_did, status)`.execute(db);

  // ── vertex_corporate_action_item ─────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_corporate_action_item (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,

      action_vid          VARCHAR NOT NULL,
      item_code           VARCHAR NOT NULL,
      item_type           VARCHAR NOT NULL,
      description         VARCHAR,
      before_text         TEXT,
      after_text          TEXT,
      requires_registration BOOLEAN NOT NULL DEFAULT true,
      registration_tax_jpy  BIGINT,
      status              VARCHAR NOT NULL DEFAULT 'pending',

      created_at          VARCHAR,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_corporate_action_item_action
            ON vertex_corporate_action_item (action_vid, status)`.execute(db);

  // ── edge_corporate_action_document ───────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_corporate_action_document (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,

      action_code       VARCHAR NOT NULL,
      doc_role          VARCHAR NOT NULL,
      file_path         VARCHAR,
      sharepoint_url    VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_corp_action_doc_src
            ON edge_corporate_action_document (src_vid, doc_role)`.execute(db);

  // ── mv_corporate_action_status ───────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_corporate_action_status AS
    SELECT
      a.vertex_id           AS action_vid,
      a.action_code,
      a.action_type,
      a.legal_entity_did,
      a.title,
      a.status              AS action_status,
      a.resolution_date,
      a.filing_date,
      a.registration_date,
      a.registration_tax_jpy,
      COUNT(i.vertex_id)                                          AS total_items,
      COUNT(i.vertex_id) FILTER (WHERE i.status = 'registered')  AS registered_items,
      COUNT(i.vertex_id) FILTER (WHERE i.requires_registration)  AS requires_reg_items,
      SUM(i.registration_tax_jpy)                                AS total_tax_jpy,
      MAX(i.created_at)                                          AS last_updated
    FROM vertex_corporate_action a
    LEFT JOIN vertex_corporate_action_item i ON i.action_vid = a.vertex_id
    GROUP BY
      a.vertex_id, a.action_code, a.action_type, a.legal_entity_did,
      a.title, a.status, a.resolution_date, a.filing_date,
      a.registration_date, a.registration_tax_jpy
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_corporate_action_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corp_action_doc_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_corporate_action_document`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corporate_action_item_action`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_corporate_action_item`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corporate_action_entity_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corporate_action_code`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_corporate_action`.execute(db);
}
