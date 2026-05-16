import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0035 Phase 1.1 — Tier 3 PII storage + authority audit log.
 *
 * Why a dedicated vertex table instead of `app.bsky.actor.putPreferences`:
 *   Bluesky preferences is account-scoped (single union blob), unsuitable for
 *   N per-debtor PII rows. Tier 3 spec ("PII / 金融 / user config" not in Repo)
 *   is satisfied by a server-side-only vertex table that is NEVER projected
 *   from PDS commits — it is INSERT-ed directly by the worker handler after
 *   authority Service Auth verification, and is owner_did-restricted so
 *   federation cannot read it.
 *
 * Schema:
 *   vertex_sashiosae_case_pii  — debtor identity + exact monetary fields
 *                                joined to vertex_atrecord_sashiosae_choushuu_case via case_id
 *   vertex_sashiosae_notice_property_pii — sashiosae notice property detail
 *                                          (口座番号 / 不動産登記番号 / 動産詳細)
 *   vertex_sashiosae_kanka_winner_pii    — kanka result winner DID + cleared amount
 *   vertex_sashiosae_authority_audit     — every authority write op (who/when/what NSID/case_id)
 *
 * Spec: 90-docs/adr/0035-jpn-seizure-cluster-topology.md §PII Tier Placement
 *       90-docs/adr/0018-pii-tier3-cohort-first.md
 *       国税通則法 §126 / 地方税法 §22 守秘義務
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── case PII (debtor identity + exact amount, 1:1 with choushuuCase) ──
  await sql`
    CREATE TABLE vertex_sashiosae_case_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      case_id            VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      debtor_did         VARCHAR NOT NULL,
      debtor_handle      VARCHAR,
      debtor_name        VARCHAR,
      amount             DOUBLE PRECISION NOT NULL,
      currency           VARCHAR NOT NULL DEFAULT 'JPY',
      tax_kind           VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL,
      updated_at         TIMESTAMPTZ
    )
  `.execute(db);

  // ── notice property PII (口座番号 / 不動産登記番号 / 動産詳細) ──
  await sql`
    CREATE TABLE vertex_sashiosae_notice_property_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      notice_id          VARCHAR NOT NULL,
      case_id            VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      property_type      VARCHAR NOT NULL,
      property_detail    VARCHAR NOT NULL,
      bank_account       VARCHAR,
      real_estate_id     VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── kanka winner PII (落札者 + 正確落札額) ──
  await sql`
    CREATE TABLE vertex_sashiosae_kanka_winner_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      kanka_id           VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      winner_did         VARCHAR,
      winner_handle      VARCHAR,
      cleared_amount     DOUBLE PRECISION,
      currency           VARCHAR NOT NULL DEFAULT 'JPY',
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── authority audit log (国税通則法 §126 守秘義務監査) ──
  await sql`
    CREATE TABLE vertex_sashiosae_authority_audit (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      audit_id           VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      method_nsid        VARCHAR NOT NULL,
      case_id            VARCHAR,
      target_did         VARCHAR,
      action             VARCHAR NOT NULL,
      lxm_scope          VARCHAR,
      ip_address         VARCHAR,
      user_agent         VARCHAR,
      result             VARCHAR NOT NULL,
      error_code         VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── Indexes (case_id is most common JOIN key) ──
  await sql`CREATE INDEX idx_sashiosae_case_pii_case_id ON vertex_sashiosae_case_pii (case_id)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_case_pii_debtor ON vertex_sashiosae_case_pii (debtor_did)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_notice_property_notice ON vertex_sashiosae_notice_property_pii (notice_id)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_kanka_winner_kanka ON vertex_sashiosae_kanka_winner_pii (kanka_id)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_audit_authority ON vertex_sashiosae_authority_audit (authority_did, created_at)`.execute(db);
  await sql`CREATE INDEX idx_sashiosae_audit_method ON vertex_sashiosae_authority_audit (method_nsid, created_at)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_sashiosae_authority_audit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sashiosae_kanka_winner_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sashiosae_notice_property_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sashiosae_case_pii`.execute(db);
}
