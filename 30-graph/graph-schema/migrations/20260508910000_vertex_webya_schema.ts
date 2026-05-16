import { Kysely, sql } from "kysely";

/**
 * webya.gftd.ai — ホームページ生成 actor スキーマ (ADR-0036 Hyperdrive direct)
 *
 * Tables:
 *   vertex_webya_client           — 外部顧客 (企業/士業)
 *   vertex_webya_site             — サイトプロジェクト
 *   vertex_webya_template         — Jinja2 テンプレート定義 (profession_kind × version)
 *   vertex_webya_page             — ページ (rendered HTML + slot values)
 *   vertex_webya_legal_disclosure — 法定開示値 (弁護士登録番号等)
 *   vertex_webya_domain           — CF Custom Hostname プロビジョニング状態
 *   vertex_webya_generation_job   — LangGraph run tracking
 *   edge_webya_client_site        — client → site
 *   edge_webya_site_page          — site  → page
 *
 * Streaming MVs:
 *   mv_webya_sites_by_status
 *   mv_webya_domain_ssl_pending
 *   mv_webya_generation_queue
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Client ────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_client (
      vertex_id        VARCHAR PRIMARY KEY,
      client_id        VARCHAR NOT NULL,
      client_name      VARCHAR NOT NULL,
      profession_kind  VARCHAR NOT NULL,
      contact_email    VARCHAR,
      contact_phone    VARCHAR,
      org_did          VARCHAR,
      created_at       VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Site ──────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_site (
      vertex_id              VARCHAR PRIMARY KEY,
      site_id                VARCHAR NOT NULL,
      client_id              VARCHAR NOT NULL,
      template_id            VARCHAR NOT NULL,
      site_name              VARCHAR NOT NULL,
      custom_domain          VARCHAR,
      subdomain              VARCHAR NOT NULL,
      cf_custom_hostname_id  VARCHAR,
      ssl_status             VARCHAR NOT NULL DEFAULT 'none',
      "status"               VARCHAR NOT NULL DEFAULT 'draft',
      published_at           VARCHAR,
      created_at             VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Template ──────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_template (
      vertex_id        VARCHAR PRIMARY KEY,
      template_id      VARCHAR NOT NULL,
      profession_kind  VARCHAR NOT NULL,
      pages_json       VARCHAR NOT NULL,
      html_skeleton    VARCHAR NOT NULL,
      slot_schema_json VARCHAR NOT NULL,
      "version"        INT NOT NULL DEFAULT 1,
      active           BOOLEAN NOT NULL DEFAULT TRUE,
      created_at       VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Page ──────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_page (
      vertex_id        VARCHAR PRIMARY KEY,
      page_id          VARCHAR NOT NULL,
      site_id          VARCHAR NOT NULL,
      slug             VARCHAR NOT NULL,
      title            VARCHAR NOT NULL,
      meta_description VARCHAR,
      slots_json       VARCHAR,
      html_content     VARCHAR,
      json_ld          VARCHAR,
      "status"         VARCHAR NOT NULL DEFAULT 'draft',
      updated_at       VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Legal Disclosure ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_legal_disclosure (
      vertex_id         VARCHAR PRIMARY KEY,
      disclosure_id     VARCHAR NOT NULL,
      site_id           VARCHAR NOT NULL,
      profession_kind   VARCHAR NOT NULL,
      disclosure_type   VARCHAR NOT NULL,
      disclosure_value  VARCHAR NOT NULL,
      verified_at       VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Domain (CF Custom Hostname) ───────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_domain (
      vertex_id              VARCHAR PRIMARY KEY,
      domain_id              VARCHAR NOT NULL,
      site_id                VARCHAR NOT NULL,
      domain                 VARCHAR NOT NULL,
      cf_hostname_id         VARCHAR,
      ssl_status             VARCHAR NOT NULL DEFAULT 'pending',
      ownership_verified     BOOLEAN NOT NULL DEFAULT FALSE,
      dns_cname_target       VARCHAR NOT NULL DEFAULT 'proxy-webya.gftd.ai',
      verification_txt_name  VARCHAR,
      verification_txt_value VARCHAR,
      provisioned_at         VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Generation Job ────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webya_generation_job (
      vertex_id         VARCHAR PRIMARY KEY,
      job_id            VARCHAR NOT NULL,
      site_id           VARCHAR NOT NULL,
      langgraph_run_id  VARCHAR,
      "status"          VARCHAR NOT NULL DEFAULT 'pending',
      llm_calls_count   INT NOT NULL DEFAULT 0,
      revision_count    INT NOT NULL DEFAULT 0,
      started_at        VARCHAR NOT NULL,
      completed_at      VARCHAR,
      error_message     VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Edges ─────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS edge_webya_client_site (
      vertex_id  VARCHAR PRIMARY KEY,
      src        VARCHAR NOT NULL,
      dst        VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_webya_site_page (
      vertex_id  VARCHAR PRIMARY KEY,
      src        VARCHAR NOT NULL,
      dst        VARCHAR NOT NULL,
      slug       VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Streaming MVs ─────────────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_sites_by_status AS
    SELECT
      status,
      COUNT(*) AS site_count
    FROM vertex_webya_site
    GROUP BY status
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_domain_ssl_pending AS
    SELECT
      d.vertex_id,
      d.site_id,
      d.domain,
      d.ssl_status,
      d.ownership_verified,
      d.dns_cname_target,
      d.verification_txt_name,
      d.verification_txt_value,
      d.provisioned_at
    FROM vertex_webya_domain d
    WHERE d.ssl_status <> 'active'
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_webya_generation_queue AS
    SELECT
      j.vertex_id,
      j.job_id,
      j.site_id,
      j.status,
      j.langgraph_run_id,
      j.llm_calls_count,
      j.started_at
    FROM vertex_webya_generation_job j
    WHERE j.status IN ('pending', 'running')
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_webya_generation_queue`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_webya_domain_ssl_pending`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_webya_sites_by_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_webya_site_page`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_webya_client_site`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_generation_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_domain`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_legal_disclosure`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_page`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_template`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_site`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webya_client`.execute(db);
}
