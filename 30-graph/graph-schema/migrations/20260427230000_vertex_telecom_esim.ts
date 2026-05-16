import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (eUICC device registry / SM-DS event / ownership transfer)
// tier: C (profile state log / audit snapshot)
// PII note: eid stored sha256: hashed; iccid stored sha256: hashed (quasi-PII, device-bound)

/**
 * telecom Phase 18 — eSIM / eUICC Lifecycle (GSMA SGP.22 Consumer + SGP.02 M2M).
 * Covers eUICC provisioning, profile download/enable/disable/delete via SM-DP+,
 * SM-DS event registration, state auditing, and MNO-to-MNO ownership transfer.
 *
 * Builds on Phase 1 (subscription), Phase 4 (SUPI/AKA), Phase 17 (TMF product order
 * — downloadEsimProfile is typically triggered by a TMF622 product order).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // eUICC device registry (one row per physical eUICC)
  await sql`
    CREATE TABLE vertex_telecom_esim_euicc (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      eid                  varchar NOT NULL,
      device_kind          varchar NOT NULL,
      manufacturer_name    varchar,
      platform_version     varchar,
      smdp_address         varchar,
      smds_address         varchar,
      profile_slots        int,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // eSIM profile instance state log (one row per profile state change)
  await sql`
    CREATE TABLE vertex_telecom_esim_profile (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      download_id          varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      matching_id          varchar,
      smdp_address         varchar NOT NULL,
      profile_type         varchar,
      mno                  varchar,
      profile_state        varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // Profile state operation log (enable / disable / delete)
  await sql`
    CREATE TABLE vertex_telecom_esim_profile_op (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      operation_id         varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      op_kind              varchar NOT NULL,
      reason               varchar,
      refresh_flag         boolean,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // SM-DS pending event registry
  await sql`
    CREATE TABLE vertex_telecom_esim_smds_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      event_id             varchar NOT NULL,
      eid                  varchar NOT NULL,
      smdp_address         varchar NOT NULL,
      smds_address         varchar,
      event_type           varchar NOT NULL,
      iccid                varchar,
      expires_at           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // eUICC state audit snapshot
  await sql`
    CREATE TABLE vertex_telecom_esim_audit (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      audit_id             varchar NOT NULL,
      eid                  varchar NOT NULL,
      profile_count        int,
      active_iccid         varchar,
      free_memory_bytes    bigint,
      last_contact_at      varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // MNO-to-MNO ownership transfer record
  await sql`
    CREATE TABLE vertex_telecom_esim_ownership_transfer (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      transfer_id          varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      source_mno           varchar NOT NULL,
      target_mno           varchar NOT NULL,
      target_smdp_address  varchar NOT NULL,
      porting_ref          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  // Edges
  await sql`
    CREATE TABLE edge_telecom_esim_profile_on_euicc (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_esim_smds_event_for_profile (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    )
  `.execute(db);

  // Materialized views
  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_esim_active_profiles AS
    SELECT eid, iccid, mno, smdp_address, profile_state, observed_at, org_id
    FROM vertex_telecom_esim_profile
    WHERE profile_state = 'enabled'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_esim_pending_smds_events AS
    SELECT event_id, eid, smdp_address, event_type, expires_at, status, org_id
    FROM vertex_telecom_esim_smds_event
    WHERE status = 'pending'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_esim_audit_recent AS
    SELECT audit_id, eid, profile_count, active_iccid, free_memory_bytes, last_contact_at, observed_at, org_id
    FROM vertex_telecom_esim_audit
    ORDER BY observed_at DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_audit_recent`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_pending_smds_events`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_active_profiles`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_esim_smds_event_for_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_esim_profile_on_euicc`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_ownership_transfer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_audit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_smds_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_profile_op`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_esim_euicc`.execute(db);
}
