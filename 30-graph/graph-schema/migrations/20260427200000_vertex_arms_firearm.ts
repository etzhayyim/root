// tier: B (firearm registry, permit — operational identity)
// tier: C (custody_event, auth_session — transaction log)
// tier: 3 (firearm_pii, permit_pii — serial/permit number plaintext, ADR-0018)
//
// etzhayyim-project-arms Phase 1 — Firearm ID authentication + chain-of-custody.
//
// 6 vertex tables + 2 edge tables:
//   vertex_arms_firearm         — public registry (serial number hashed)
//   vertex_arms_firearm_pii     — Tier 3 PII (plaintext serial number)
//   vertex_arms_permit          — possession / acquisition / carry permits
//   vertex_arms_permit_pii      — Tier 3 PII (plaintext permit number)
//   vertex_arms_custody_event   — check-out / check-in / transfer / incident log
//   vertex_arms_auth_session    — DID challenge-response authentication sessions
//   edge_arms_firearm_to_holder — current holder relationship
//   edge_arms_firearm_to_permit — permit coverage relationship
//
// Compliance: 銃砲刀剣類所持等取締法 / 防衛装備移転三原則 / ATT / ECCN Cat.0
//
// Apply via:
//   bash 30-graph/graph-schema/scripts/apply-pending.sh \
//     20260427200000_vertex_arms_firearm
import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Tier B: Firearm registry (serial number stored as SHA-256 hash) ─────────
  await sql`
    CREATE TABLE vertex_arms_firearm (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      serial_number_hash   varchar NOT NULL,
      make                 varchar NOT NULL,
      model                varchar NOT NULL,
      caliber              varchar NOT NULL,
      category             varchar NOT NULL,
      status               varchar NOT NULL DEFAULT 'active',
      registered_at        varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_firearm_owner ON vertex_arms_firearm (owner_did)`.execute(db);
  await sql`CREATE INDEX idx_arms_firearm_serial ON vertex_arms_firearm (serial_number_hash)`.execute(db);
  await sql`CREATE INDEX idx_arms_firearm_status ON vertex_arms_firearm (status, category)`.execute(db);

  // ── Tier 3 PII: Actual serial number (restricted access) ────────────────────
  await sql`
    CREATE TABLE vertex_arms_firearm_pii (
      vertex_id            varchar PRIMARY KEY,
      firearm_vid          varchar NOT NULL,
      serial_number        varchar NOT NULL,
      manufacturer_code    varchar,
      country_of_origin    varchar,
      year_of_manufacture  int,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_firearm_pii_vid ON vertex_arms_firearm_pii (firearm_vid)`.execute(db);

  // ── Tier B: Possession / acquisition / carry permits ────────────────────────
  await sql`
    CREATE TABLE vertex_arms_permit (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      holder_did           varchar NOT NULL,
      permit_type          varchar NOT NULL,
      permit_number_hash   varchar NOT NULL,
      category_allowed     varchar NOT NULL,
      issuer_did           varchar NOT NULL,
      issued_at            varchar,
      expires_at           varchar,
      status               varchar NOT NULL DEFAULT 'active',
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_permit_holder ON vertex_arms_permit (holder_did, status)`.execute(db);
  await sql`CREATE INDEX idx_arms_permit_issuer ON vertex_arms_permit (issuer_did)`.execute(db);

  // ── Tier 3 PII: Actual permit number ────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_arms_permit_pii (
      vertex_id            varchar PRIMARY KEY,
      permit_vid           varchar NOT NULL,
      permit_number        varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_permit_pii_vid ON vertex_arms_permit_pii (permit_vid)`.execute(db);

  // ── Tier C: Chain of custody event log ──────────────────────────────────────
  await sql`
    CREATE TABLE vertex_arms_custody_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      firearm_vid          varchar NOT NULL,
      event_type           varchar NOT NULL,
      from_holder_did      varchar,
      to_holder_did        varchar,
      auth_session_vid     varchar,
      permit_vid           varchar,
      location_code        varchar,
      notes                varchar,
      occurred_at          varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_custody_firearm ON vertex_arms_custody_event (firearm_vid, occurred_at)`.execute(db);
  await sql`CREATE INDEX idx_arms_custody_from ON vertex_arms_custody_event (from_holder_did)`.execute(db);
  await sql`CREATE INDEX idx_arms_custody_to ON vertex_arms_custody_event (to_holder_did)`.execute(db);
  await sql`CREATE INDEX idx_arms_custody_type ON vertex_arms_custody_event (event_type, occurred_at)`.execute(db);

  // ── Tier C: DID challenge-response auth sessions ─────────────────────────────
  await sql`
    CREATE TABLE vertex_arms_auth_session (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      firearm_vid          varchar NOT NULL,
      holder_did           varchar NOT NULL,
      challenge            varchar NOT NULL,
      response_hash        varchar,
      auth_status          varchar NOT NULL DEFAULT 'pending',
      initiated_at         varchar,
      completed_at         varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_auth_firearm ON vertex_arms_auth_session (firearm_vid, auth_status)`.execute(db);
  await sql`CREATE INDEX idx_arms_auth_holder ON vertex_arms_auth_session (holder_did, auth_status)`.execute(db);

  // ── Edges ────────────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE edge_arms_firearm_to_holder (
      src        varchar NOT NULL,
      dst        varchar NOT NULL,
      rel        varchar NOT NULL DEFAULT 'held_by',
      since      varchar,
      permit_vid varchar,
      PRIMARY KEY (src, dst)
    )
  `.execute(db);

  await sql`CREATE INDEX idx_arms_f2h_dst ON edge_arms_firearm_to_holder (dst)`.execute(db);

  await sql`
    CREATE TABLE edge_arms_firearm_to_permit (
      src  varchar NOT NULL,
      dst  varchar NOT NULL,
      rel  varchar NOT NULL DEFAULT 'covered_by',
      PRIMARY KEY (src, dst)
    )
  `.execute(db);

  // ── Streaming MV: active firearms by holder ──────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW mv_arms_active_by_holder AS
    SELECT
      e.dst         AS holder_did,
      f.vertex_id   AS firearm_vid,
      f.make,
      f.model,
      f.caliber,
      f.category,
      f.status,
      e.since       AS held_since
    FROM edge_arms_firearm_to_holder e
    JOIN vertex_arms_firearm f ON f.vertex_id = e.src
    WHERE f.status IN ('active', 'checked_out')
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_arms_active_by_holder`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_arms_firearm_to_permit`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_arms_firearm_to_holder`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_auth_session`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_custody_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_permit_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_permit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_firearm_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_firearm`.execute(db);
}
