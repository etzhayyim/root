import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations.
// tier: B (briefing root/section)  tier: A (briefing entity = inferred PII)

/**
 * malak.surveillance briefing graph (Phase 0 draft).
 *
 * Goal: briefing/dossier 一次資料 (e.g. 警察庁照会 15ページ PDF + FAQ) を
 * markdown だけでなく graph-native で RW に保管する。本文 / リンク / 推論
 * された依存関係 / 人物 / 日時 / ADR / 法律 / case-fact など、全 entity を
 * vertex 化し、edge で関係 (mentions / cites / depends_on / scheduled_for /
 * authored_by / for_agency) を表現する。markdown は graph state からの
 * render に過ぎず、graph を rebuild すれば markdown も再生成可能。
 *
 *   vertex_malak_briefing            briefing doc root
 *   vertex_malak_briefing_section    section (numbered, hierarchical)
 *   vertex_malak_briefing_entity     person/project/ADR/external-URL/concept
 *   vertex_malak_briefing_date_event 日時付きマイルストーン (期限/会議/通達公開)
 *
 *   edge_briefing_has_section        briefing root → section
 *   edge_briefing_mentions_entity    briefing/section → entity
 *   edge_briefing_mentions_org       briefing/section → vertex_gov_org (or LEA)
 *   edge_briefing_cites_record       briefing/section → vertex_repo_record / external URL
 *   edge_briefing_depends_on         briefing → briefing (X requires Y to be GREEN first)
 *   edge_briefing_event              briefing → date_event
 *
 *   mv_malak_briefing_entity_summary 各 briefing の entity 数 / category 別 count
 *   mv_malak_briefing_dependency_graph briefing 間 depends_on の closure
 *
 * Phase 0: schema review only. Live apply blocked by COMPLIANCE-MEMO §1 B1-B5
 * + Kunal CLO triage (G1) per `_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md`.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── briefing root ───────────────────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_malak_briefing (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint, created_date date, sensitivity_ord int, owner_did varchar,
      briefing_id        varchar NOT NULL,
      briefing_type      varchar NOT NULL,
      target_agency_path varchar,
      target_agency_did  varchar,
      title              varchar NOT NULL,
      version            int NOT NULL,
      language           varchar NOT NULL,
      tlp                varchar NOT NULL,
      doc_sha256         varchar,
      file_path          varchar,
      generated_at       varchar NOT NULL,
      generated_by_did   varchar NOT NULL,
      approver_did       varchar,
      approved_at        varchar,
      status             varchar NOT NULL,
      props              varchar,
      created_at         varchar NOT NULL,
      actor_did          varchar NOT NULL,
      org_did            varchar NOT NULL,
      at_did             varchar
    )
  `.execute(db);

  // ── briefing section ────────────────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_malak_briefing_section (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      briefing_id    varchar NOT NULL,
      section_no     varchar NOT NULL,
      section_title  varchar NOT NULL,
      section_order  int NOT NULL,
      parent_section varchar,
      body_md        varchar,
      body_sha256    varchar,
      word_count     int,
      props          varchar,
      created_at     varchar NOT NULL,
      actor_did      varchar NOT NULL,
      org_did        varchar NOT NULL,
      at_did         varchar
    )
  `.execute(db);

  // ── briefing entity (person / project / ADR / URL / concept / law) ───
  // sensitivity_ord: 100 (person) / 50 (project/ADR) / 20 (URL/concept/law)
  await sql`
    CREATE TABLE vertex_malak_briefing_entity (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      entity_id      varchar NOT NULL,
      entity_kind    varchar NOT NULL,
      display_name   varchar NOT NULL,
      identifier     varchar,
      resolved_did   varchar,
      external_url   varchar,
      confidence     double precision,
      extraction_source varchar,
      first_seen_in  varchar,
      props          varchar,
      created_at     varchar NOT NULL,
      actor_did      varchar NOT NULL,
      org_did        varchar NOT NULL,
      at_did         varchar
    )
  `.execute(db);

  // ── briefing date event (期限 / 会議日 / 通達公開日 / Phase milestone) ───
  await sql`
    CREATE TABLE vertex_malak_briefing_date_event (
      vertex_id     varchar PRIMARY KEY,
      _seq          bigint, created_date date, sensitivity_ord int, owner_did varchar,
      event_id      varchar NOT NULL,
      event_kind    varchar NOT NULL,
      event_label   varchar NOT NULL,
      event_date    varchar NOT NULL,
      iso_date      varchar NOT NULL,
      precision     varchar NOT NULL,
      confidence    double precision,
      props         varchar,
      created_at    varchar NOT NULL,
      actor_did     varchar NOT NULL,
      org_did       varchar NOT NULL,
      at_did        varchar
    )
  `.execute(db);

  // ── edges ──────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE edge_briefing_has_section (
      edge_id   varchar PRIMARY KEY,
      _seq      bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid   varchar NOT NULL,
      dst_vid   varchar NOT NULL,
      ord       int NOT NULL,
      created_at varchar NOT NULL,
      actor_did varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_briefing_mentions_entity (
      edge_id        varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid        varchar NOT NULL,
      dst_vid        varchar NOT NULL,
      mention_kind   varchar NOT NULL,
      mention_count  int NOT NULL,
      first_offset   int,
      created_at     varchar NOT NULL,
      actor_did      varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_briefing_mentions_org (
      edge_id       varchar PRIMARY KEY,
      _seq          bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid       varchar NOT NULL,
      dst_vid       varchar NOT NULL,
      mention_kind  varchar NOT NULL,
      role          varchar,
      created_at    varchar NOT NULL,
      actor_did     varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_briefing_cites_record (
      edge_id      varchar PRIMARY KEY,
      _seq         bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid      varchar NOT NULL,
      dst_vid      varchar,
      cite_kind    varchar NOT NULL,
      external_url varchar,
      label        varchar,
      ord          int,
      created_at   varchar NOT NULL,
      actor_did    varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_briefing_depends_on (
      edge_id        varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid        varchar NOT NULL,
      dst_vid        varchar NOT NULL,
      dep_kind       varchar NOT NULL,
      required_status varchar,
      created_at     varchar NOT NULL,
      actor_did      varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_briefing_event (
      edge_id    varchar PRIMARY KEY,
      _seq       bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid    varchar NOT NULL,
      dst_vid    varchar NOT NULL,
      role       varchar NOT NULL,
      created_at varchar NOT NULL,
      actor_did  varchar NOT NULL, org_did varchar NOT NULL, at_did varchar
    )
  `.execute(db);

  // ── indexes ────────────────────────────────────────────────────────────
  await sql`CREATE INDEX idx_malak_briefing_type ON vertex_malak_briefing (briefing_type)`.execute(db);
  await sql`CREATE INDEX idx_malak_briefing_agency ON vertex_malak_briefing (target_agency_path)`.execute(db);
  await sql`CREATE INDEX idx_malak_briefing_status ON vertex_malak_briefing (status)`.execute(db);
  await sql`CREATE INDEX idx_malak_briefing_generated ON vertex_malak_briefing (generated_at)`.execute(db);

  await sql`CREATE INDEX idx_malak_briefing_section_doc ON vertex_malak_briefing_section (briefing_id, section_order)`.execute(db);

  await sql`CREATE INDEX idx_malak_briefing_entity_kind ON vertex_malak_briefing_entity (entity_kind, identifier)`.execute(db);
  await sql`CREATE INDEX idx_malak_briefing_entity_did ON vertex_malak_briefing_entity (resolved_did)`.execute(db);

  await sql`CREATE INDEX idx_malak_briefing_date_kind ON vertex_malak_briefing_date_event (event_kind, iso_date)`.execute(db);

  await sql`CREATE INDEX idx_brf_has_section_src ON edge_briefing_has_section (src_vid, ord)`.execute(db);
  await sql`CREATE INDEX idx_brf_mentions_entity_src ON edge_briefing_mentions_entity (src_vid, mention_kind)`.execute(db);
  await sql`CREATE INDEX idx_brf_mentions_entity_dst ON edge_briefing_mentions_entity (dst_vid)`.execute(db);
  await sql`CREATE INDEX idx_brf_mentions_org_src ON edge_briefing_mentions_org (src_vid)`.execute(db);
  await sql`CREATE INDEX idx_brf_mentions_org_dst ON edge_briefing_mentions_org (dst_vid)`.execute(db);
  await sql`CREATE INDEX idx_brf_cites_record_src ON edge_briefing_cites_record (src_vid, cite_kind)`.execute(db);
  await sql`CREATE INDEX idx_brf_depends_on_src ON edge_briefing_depends_on (src_vid)`.execute(db);
  await sql`CREATE INDEX idx_brf_depends_on_dst ON edge_briefing_depends_on (dst_vid)`.execute(db);
  await sql`CREATE INDEX idx_brf_event_src ON edge_briefing_event (src_vid, role)`.execute(db);
  await sql`CREATE INDEX idx_brf_event_dst ON edge_briefing_event (dst_vid)`.execute(db);

  // ── MV ─────────────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW mv_malak_briefing_entity_summary AS
    SELECT
      b.briefing_id,
      b.briefing_type,
      b.target_agency_path,
      b.status,
      COUNT(DISTINCT em.dst_vid)                                   AS entity_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'person')  AS person_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'project') AS project_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'adr')     AS adr_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'url')     AS url_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'law')     AS law_count,
      COUNT(DISTINCT em.dst_vid) FILTER (WHERE e.entity_kind = 'concept') AS concept_count,
      COUNT(DISTINCT mo.dst_vid)                                   AS org_mention_count,
      COUNT(DISTINCT ev.dst_vid)                                   AS event_count
    FROM vertex_malak_briefing b
    LEFT JOIN edge_briefing_mentions_entity em
      ON em.src_vid LIKE b.briefing_id || '%'
    LEFT JOIN vertex_malak_briefing_entity e
      ON e.vertex_id = em.dst_vid
    LEFT JOIN edge_briefing_mentions_org mo
      ON mo.src_vid LIKE b.briefing_id || '%'
    LEFT JOIN edge_briefing_event ev
      ON ev.src_vid LIKE b.briefing_id || '%'
    GROUP BY b.briefing_id, b.briefing_type, b.target_agency_path, b.status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_malak_briefing_dependency_graph AS
    SELECT
      d.src_vid AS upstream_briefing_id,
      d.dst_vid AS downstream_briefing_id,
      d.dep_kind,
      d.required_status,
      u.briefing_type AS upstream_type,
      v.briefing_type AS downstream_type,
      u.status        AS upstream_status,
      v.status        AS downstream_status
    FROM edge_briefing_depends_on d
    LEFT JOIN vertex_malak_briefing u ON u.vertex_id = d.src_vid
    LEFT JOIN vertex_malak_briefing v ON v.vertex_id = d.dst_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_briefing_dependency_graph`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_malak_briefing_entity_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_event`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_depends_on`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_cites_record`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_mentions_org`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_mentions_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_briefing_has_section`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_briefing_date_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_briefing_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_briefing_section`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_briefing`.execute(db);
}
