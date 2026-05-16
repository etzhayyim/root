import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0036 Phase C1+ — 復興予算 political lineage + UBO tracing schema.
 *
 * Extends the base `vertex_fukkou_budget_flow` schema with:
 *   - Legislation vertices (法律 / 法案)
 *   - Diet committees (国会委員会)
 *   - Politicians (国会議員)
 *   - Bureaucrats (官僚 drafters)
 *   - Recipient orgs (受領団体・法人)
 *   - UBO chain (受益最終所有者)
 *
 * Edges wire the full lineage:
 *   Taxpayer → TaxCode → Bond → 特別会計 → 復興庁 → 県復興局 → 事業者 → UBO
 *   PoliticalActor → Committee → Legislation → Bureaucrat (drafter)
 *
 * PII tier:
 *   Tier 1 public  : legislation, committee membership, public officials
 *   Tier 2 domain  : civil servant non-public positions (signal:v1 ciphertext)
 *   Tier 3 rare    : UBO natural-person fragments if not public (家族関係等)
 *
 * Spec: 90-docs/adr/0036-fukkou-budget-flow-lineage.md §Political lineage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 法律 / 法案 (Legislation) ──
  await sql`
    CREATE TABLE vertex_fukkou_legislation (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      legislation_id    VARCHAR NOT NULL,
      name              VARCHAR NOT NULL,
      name_en           VARCHAR,
      kind              VARCHAR NOT NULL,
      diet_session      VARCHAR,
      submitted_at      DATE,
      established_at    DATE,
      promulgated_at    DATE,
      effective_from    DATE,
      sunset_at         DATE,
      status            VARCHAR NOT NULL,
      elaws_id          VARCHAR,
      source_url        VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── 国会委員会 (Diet committees) ──
  await sql`
    CREATE TABLE vertex_fukkou_committee (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      committee_id      VARCHAR NOT NULL,
      chamber           VARCHAR NOT NULL,
      name              VARCHAR NOT NULL,
      name_en           VARCHAR,
      kind              VARCHAR NOT NULL,
      diet_session      VARCHAR,
      active_from       DATE,
      active_until      DATE,
      source_url        VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── 政治家 (Politicians) ──
  await sql`
    CREATE TABLE vertex_fukkou_politician (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      politician_id     VARCHAR NOT NULL,
      name              VARCHAR NOT NULL,
      name_en           VARCHAR,
      chamber           VARCHAR,
      party             VARCHAR,
      faction           VARCHAR,
      constituency      VARCHAR,
      terms_served      INTEGER,
      cabinet_post      VARCHAR,
      fukkou_role       VARCHAR,
      bio_url           VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── 官僚 (Bureaucrats / Civil servants) ──
  await sql`
    CREATE TABLE vertex_fukkou_bureaucrat (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      bureaucrat_id     VARCHAR NOT NULL,
      name              VARCHAR NOT NULL,
      name_en           VARCHAR,
      home_ministry     VARCHAR,
      current_agency    VARCHAR,
      rank              VARCHAR,
      role              VARCHAR,
      fukkou_role       VARCHAR,
      tenure_from       DATE,
      tenure_until      DATE,
      bio_url           VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── 受領団体・法人 (Recipient orgs/corps) ──
  await sql`
    CREATE TABLE vertex_fukkou_recipient_org (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      org_id               VARCHAR NOT NULL,
      name                 VARCHAR NOT NULL,
      name_en              VARCHAR,
      kind                 VARCHAR NOT NULL,
      houjin_bango         VARCHAR,
      lei_code             VARCHAR,
      registered_at        DATE,
      dissolved_at         DATE,
      address              VARCHAR,
      representative       VARCHAR,
      status               VARCHAR NOT NULL,
      total_received_jpy   DOUBLE PRECISION,
      flows_received       INTEGER,
      bio_url              VARCHAR,
      created_at           TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── UBO chain (Ultimate Beneficial Owner) ──
  await sql`
    CREATE TABLE vertex_fukkou_ubo (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      ubo_id            VARCHAR NOT NULL,
      leaf_org_id       VARCHAR NOT NULL,
      beneficial_did    VARCHAR NOT NULL,
      beneficial_kind   VARCHAR NOT NULL,
      name              VARCHAR,
      ownership_pct     DOUBLE PRECISION,
      control_type      VARCHAR,
      tier              VARCHAR NOT NULL,
      disclosure_src    VARCHAR,
      verified_at       TIMESTAMPTZ,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Edges ────────────────────────────────────────────────────────────
  // Committee deliberated Legislation
  await sql`
    CREATE TABLE edge_fukkou_committee_deliberated (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      deliberated_at DATE,
      outcome       VARCHAR,
      session       VARCHAR,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // Politician served on Committee
  await sql`
    CREATE TABLE edge_fukkou_politician_served (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      position      VARCHAR,
      tenure_from   DATE,
      tenure_until  DATE,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // Politician sponsored / voted Legislation
  await sql`
    CREATE TABLE edge_fukkou_politician_acted (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      action        VARCHAR NOT NULL,
      acted_at      DATE,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // Bureaucrat drafted Legislation
  await sql`
    CREATE TABLE edge_fukkou_bureaucrat_drafted (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      role          VARCHAR,
      drafted_at    DATE,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // Bureaucrat role at Authority (復興庁, 財務省, etc.)
  await sql`
    CREATE TABLE edge_fukkou_bureaucrat_posted (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      rank          VARCHAR,
      tenure_from   DATE,
      tenure_until  DATE,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // Recipient linked to Legislation (grant program legal basis)
  await sql`
    CREATE TABLE edge_fukkou_recipient_grant (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      program_name      VARCHAR,
      amount_jpy        DOUBLE PRECISION NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // UBO → Recipient Org (chain of control)
  await sql`
    CREATE TABLE edge_fukkou_ubo_controls (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      pct           DOUBLE PRECISION,
      kind          VARCHAR,
      chain_depth   INTEGER,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Indexes ───────────────────────────────────────────────────────────
  await sql`CREATE INDEX idx_fukkou_legislation_status ON vertex_fukkou_legislation (status, established_at)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_committee_chamber ON vertex_fukkou_committee (chamber, kind)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_politician_party ON vertex_fukkou_politician (party, chamber)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_politician_role ON vertex_fukkou_politician (fukkou_role)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_bureaucrat_ministry ON vertex_fukkou_bureaucrat (home_ministry, rank)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_recipient_kind ON vertex_fukkou_recipient_org (kind, status)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_recipient_houjin ON vertex_fukkou_recipient_org (houjin_bango)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_ubo_leaf ON vertex_fukkou_ubo (leaf_org_id)`.execute(db);
  await sql`CREATE INDEX idx_fukkou_ubo_beneficial ON vertex_fukkou_ubo (beneficial_did)`.execute(db);

  // ── Narrow MVs ────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW mv_fukkou_recipient_top AS
    SELECT
      org_id,
      name,
      kind,
      status,
      total_received_jpy,
      flows_received
    FROM vertex_fukkou_recipient_org
    WHERE total_received_jpy IS NOT NULL
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_fukkou_politician_activity AS
    SELECT
      src_vid AS politician_vid,
      action,
      COUNT(*) AS action_count
    FROM edge_fukkou_politician_acted
    GROUP BY src_vid, action
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_fukkou_politician_activity`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_fukkou_recipient_top`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_ubo_controls`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_recipient_grant`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_bureaucrat_posted`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_bureaucrat_drafted`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_politician_acted`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_politician_served`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fukkou_committee_deliberated`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_ubo`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_recipient_org`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_bureaucrat`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_politician`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_committee`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_legislation`.execute(db);
}
