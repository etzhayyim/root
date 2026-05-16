import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (organisations + station / koban) / A (contact_person with vault-encrypted PII)

/**
 * malak.surveillance (formerly mehikari) — international LEA organisation graph (Phase 0 draft).
 *
 * Reason: `vertex_gov_org` covers ministries / agencies / prefectures /
 * municipalities only. The Japanese police system is governed by 警察法
 * which sits between the agency tier (警察庁 NPA) and the prefectural
 * tier (都道府県警察本部) but is NOT under the prefectural governor —
 * each 都道府県 has its own 公安委員会 with parallel oversight. So the
 * existing `vertex_gov_org` enum (`ministry`/`agency`/`executive`/
 * `prefecture`/`municipality`) doesn't fit police-station / koban /
 * regional-bureau granularity.
 *
 * This migration creates a parallel schema rooted in police law:
 *
 *   vertex_malak_surveillance_lea_branch  — 警察庁 6 局 + 海保 11 管区 + JC3
 *   vertex_malak_surveillance_prefectural_police — 47 都道府県警本部
 *   vertex_malak_surveillance_police_station     — 約 1,160 警察署
 *   vertex_malak_surveillance_koban              — 約 6,300 交番・駐在所
 *   vertex_malak_surveillance_org_contact        — 担当者 (vault-encrypted addressee)
 *   edge_malak_surveillance_lea_hierarchy — 階層辺
 *   mv_malak_surveillance_jpn_police_coverage    — 47 本部 × ingest 完了率
 *
 * Data ingest is NOT performed by this migration. See
 * `_working/malak/surveillance/ingest/SCRAPE-DESIGN.md` for the seeding plan.
 *
 * CRITICAL: until Kunal CLO + 外部弁護士 sign-off on
 * `_working/malak/surveillance/COMPLIANCE-MEMO.md` blocker items B1-B5,
 * this migration MUST NOT be applied to production RisingWave.
 * Phase 0 = schema review only.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 警察庁 内部局 + 海保管区 + JC3 (gov_org bureau / regional-bureau / public-private-org tier) ──
  await sql`
    CREATE TABLE vertex_malak_surveillance_lea_branch (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      path             varchar NOT NULL,
      parent_path      varchar,
      name             varchar NOT NULL,
      name_en          varchar,
      website          varchar,
      contract         varchar,
      tags             varchar,
      org_tier         varchar NOT NULL,
      did_registered   varchar,
      bpmn_registered  varchar,
      props            varchar,
      created_at       varchar NOT NULL,
      actor_did        varchar NOT NULL,
      org_did          varchar NOT NULL,
      at_did           varchar
    )
  `.execute(db);

  // ── 47 都道府県警察本部 ──
  await sql`
    CREATE TABLE vertex_malak_surveillance_prefectural_police (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint, created_date date, sensitivity_ord int, owner_did varchar,
      path                   varchar NOT NULL,
      jis_code               varchar NOT NULL,
      jurisdiction_pref_path varchar NOT NULL,
      name                   varchar NOT NULL,
      name_en                varchar,
      website                varchar,
      hq_address             varchar,
      hq_phone               varchar,
      public_inquiry_email   varchar,
      cyber_div_url          varchar,
      seian_div_url          varchar,
      keiji_div_url          varchar,
      outreach_tier          varchar,
      did_registered         varchar,
      props                  varchar,
      created_at             varchar NOT NULL,
      actor_did              varchar NOT NULL,
      org_did                varchar NOT NULL,
      at_did                 varchar
    )
  `.execute(db);

  // ── 約 1,160 警察署 ──
  await sql`
    CREATE TABLE vertex_malak_surveillance_police_station (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint, created_date date, sensitivity_ord int, owner_did varchar,
      path                   varchar NOT NULL,
      prefectural_police_path varchar NOT NULL,
      station_code           varchar,
      name                   varchar NOT NULL,
      name_en                varchar,
      address                varchar,
      lat_micro              bigint,
      lon_micro              bigint,
      phone_main             varchar,
      website                varchar,
      jurisdiction_areas     varchar,
      did_registered         varchar,
      props                  varchar,
      created_at             varchar NOT NULL,
      actor_did              varchar NOT NULL,
      org_did                varchar NOT NULL,
      at_did                 varchar
    )
  `.execute(db);

  // ── 約 6,300 交番 + 駐在所 ──
  await sql`
    CREATE TABLE vertex_malak_surveillance_koban (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint, created_date date, sensitivity_ord int, owner_did varchar,
      path                 varchar NOT NULL,
      police_station_path  varchar NOT NULL,
      koban_type           varchar NOT NULL,
      name                 varchar NOT NULL,
      address              varchar,
      lat_micro            bigint,
      lon_micro            bigint,
      phone                varchar,
      did_registered       varchar,
      props                varchar,
      created_at           varchar NOT NULL,
      actor_did            varchar NOT NULL,
      org_did              varchar NOT NULL,
      at_did               varchar
    )
  `.execute(db);

  // ── 担当者 (vault-encrypted) ──
  // CRITICAL: 平文の addressee 名・連絡先は CF Worker / Hyperdrive を通らない。
  // pod 内で AES-256-GCM 暗号化された ciphertext + wrapped_key + kid のみ保管。
  // Sensitivity tier = A (highest, vault-bound).
  await sql`
    CREATE TABLE vertex_malak_surveillance_org_contact (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint, created_date date, sensitivity_ord int, owner_did varchar,
      org_path             varchar NOT NULL,
      role_code            varchar NOT NULL,
      addressee_cipher     varchar NOT NULL,
      wrapped_key          varchar NOT NULL,
      kid                  varchar NOT NULL,
      contact_email_cipher varchar,
      contact_phone_cipher varchar,
      opt_in_source        varchar NOT NULL,
      opt_in_at            varchar NOT NULL,
      opt_in_evidence      varchar,
      lead_status          varchar NOT NULL,
      last_send_at         varchar,
      unsubscribed_at      varchar,
      props                varchar,
      created_at           varchar NOT NULL,
      actor_did            varchar NOT NULL,
      org_did              varchar NOT NULL,
      at_did               varchar
    )
  `.execute(db);

  // ── 階層辺 (npa:cyber → 都道府県警 → 警察署 → 交番) ──
  await sql`
    CREATE TABLE edge_malak_surveillance_lea_hierarchy (
      edge_id      varchar PRIMARY KEY,
      _seq         bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid      varchar NOT NULL,
      dst_vid      varchar NOT NULL,
      role         varchar NOT NULL,
      created_at   varchar NOT NULL,
      actor_did    varchar NOT NULL,
      org_did      varchar NOT NULL,
      at_did       varchar
    )
  `.execute(db);

  // ── Indexes ──
  // `IF NOT EXISTS` を使わない (旧 RW 構文非互換) — DROP は down() 側で対応
  await sql`CREATE INDEX idx_malak_surv_branch_path ON vertex_malak_surveillance_lea_branch (path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_branch_parent ON vertex_malak_surveillance_lea_branch (parent_path)`.execute(db);

  await sql`CREATE INDEX idx_malak_surv_pref_path ON vertex_malak_surveillance_prefectural_police (path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_pref_jis ON vertex_malak_surveillance_prefectural_police (jis_code)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_pref_tier ON vertex_malak_surveillance_prefectural_police (outreach_tier)`.execute(db);

  await sql`CREATE INDEX idx_malak_surv_station_pref ON vertex_malak_surveillance_police_station (prefectural_police_path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_station_path ON vertex_malak_surveillance_police_station (path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_station_code ON vertex_malak_surveillance_police_station (station_code)`.execute(db);

  await sql`CREATE INDEX idx_malak_surv_koban_station ON vertex_malak_surveillance_koban (police_station_path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_koban_type ON vertex_malak_surveillance_koban (koban_type)`.execute(db);

  await sql`CREATE INDEX idx_malak_surv_contact_org ON vertex_malak_surveillance_org_contact (org_path)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_contact_role ON vertex_malak_surveillance_org_contact (role_code)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_contact_status ON vertex_malak_surveillance_org_contact (lead_status)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_contact_opt_in ON vertex_malak_surveillance_org_contact (opt_in_source)`.execute(db);

  await sql`CREATE INDEX idx_malak_surv_hierarchy_src ON edge_malak_surveillance_lea_hierarchy (src_vid)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_hierarchy_dst ON edge_malak_surveillance_lea_hierarchy (dst_vid)`.execute(db);
  await sql`CREATE INDEX idx_malak_surv_hierarchy_role ON edge_malak_surveillance_lea_hierarchy (role)`.execute(db);

  // ── MV: 47 本部 × ingest coverage ──
  await sql`
    CREATE MATERIALIZED VIEW mv_malak_surveillance_jpn_police_coverage AS
    SELECT
      pp.jis_code,
      pp.name AS prefectural_police_name,
      pp.outreach_tier,
      COUNT(DISTINCT ps.vertex_id) AS police_station_count,
      COUNT(DISTINCT kb.vertex_id) AS koban_count,
      COUNT(DISTINCT oc.vertex_id) AS contact_count,
      COUNT(DISTINCT oc.vertex_id) FILTER (
        WHERE oc.lead_status = 'sent' OR oc.lead_status = 'replied'
      ) AS active_lead_count,
      MAX(oc.last_send_at) AS most_recent_send
    FROM vertex_malak_surveillance_prefectural_police pp
    LEFT JOIN vertex_malak_surveillance_police_station ps
      ON ps.prefectural_police_path = pp.path
    LEFT JOIN vertex_malak_surveillance_koban kb
      ON kb.police_station_path = ps.path
    LEFT JOIN vertex_malak_surveillance_org_contact oc
      ON oc.org_path = pp.path
    GROUP BY pp.jis_code, pp.name, pp.outreach_tier
  `.execute(db);

  // ── MV: opt-in source breakdown (audit-friendly) ──
  await sql`
    CREATE MATERIALIZED VIEW mv_malak_surveillance_outreach_funnel AS
    SELECT
      opt_in_source,
      lead_status,
      COUNT(*) AS contact_count
    FROM vertex_malak_surveillance_org_contact
    GROUP BY opt_in_source, lead_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_surveillance_outreach_funnel`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_surveillance_jpn_police_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_malak_surveillance_lea_hierarchy`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_surveillance_org_contact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_surveillance_koban`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_surveillance_police_station`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_surveillance_prefectural_police`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_surveillance_lea_branch`.execute(db);
}
