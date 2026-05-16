import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (optical domain / OLS / ROADM / fiber catalog);
// tier: C (DWDM channel / OTN connection / alarm / PM)

/**
 * telecom Phase 16 — TIP Phoenix Open Optical (TIP MUST). Optical
 * transport plane: domain controller / OLS / ROADM / fiber span +
 * DWDM channel + OTN connection + alarm + PM event.
 *
 * Builds on Phase 2 (cellSite / networkAsset — ROADM siting + asset
 * linkage), Phase 1 (service), Phase 4 (PDU session), Phase 9 (O-RAN
 * xHaul), Phase 14 (NTN feeder link). Cross-phase: any client service
 * can ride an OTN connection via `clientServiceVid`.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_optical_domain (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      domain_id            varchar NOT NULL,
      owner_org_id         varchar NOT NULL,
      display_name         varchar NOT NULL,
      controller_kind      varchar NOT NULL,
      controller_endpoint  varchar,
      southbound_protocols varchar,
      jurisdiction         varchar NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_ols (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ols_id               varchar NOT NULL,
      domain_vid           varchar NOT NULL,
      vendor               varchar NOT NULL,
      model                varchar NOT NULL,
      must_spec_version    varchar NOT NULL,
      transponder_profile  varchar,
      total_spectrum_ghz   double precision NOT NULL,
      channel_grid_ghz     double precision NOT NULL,
      supported_modulations varchar NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_roadm (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      roadm_id             varchar NOT NULL,
      ols_vid              varchar NOT NULL,
      display_name         varchar NOT NULL,
      site_vid             varchar,
      roadm_kind           varchar NOT NULL,
      degree_count         int NOT NULL,
      add_drop_port_count  int NOT NULL,
      wss_vendor           varchar NOT NULL,
      attached_asset_vid   varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_fiber_span (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      span_id              varchar NOT NULL,
      ols_vid              varchar NOT NULL,
      source_roadm_vid     varchar NOT NULL,
      target_roadm_vid     varchar NOT NULL,
      fiber_type           varchar NOT NULL,
      length_km            double precision NOT NULL,
      attenuation_db       double precision NOT NULL,
      dispersion_ps_nm_km  double precision,
      amplifier_kind       varchar,
      amplifier_gain_db    double precision,
      owner_org_id         varchar NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_dwdm_channel (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      channel_id           varchar NOT NULL,
      ols_vid              varchar NOT NULL,
      source_roadm_vid     varchar NOT NULL,
      target_roadm_vid     varchar NOT NULL,
      path_span_vids       varchar,
      center_frequency_ghz double precision NOT NULL,
      bandwidth_ghz        double precision NOT NULL,
      modulation           varchar NOT NULL,
      line_rate_gbps       double precision NOT NULL,
      fec                  varchar,
      o_transparent_to     varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_otn_connection (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      otn_id               varchar NOT NULL,
      channel_vid          varchar NOT NULL,
      odu_kind             varchar NOT NULL,
      odu_rate             varchar NOT NULL,
      source_roadm_vid     varchar NOT NULL,
      target_roadm_vid     varchar NOT NULL,
      client_service_kind  varchar NOT NULL,
      client_service_vid   varchar,
      protection_kind      varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_alarm (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      alarm_id             varchar NOT NULL,
      source_kind          varchar NOT NULL,
      source_vid           varchar NOT NULL,
      alarm_kind           varchar NOT NULL,
      severity             varchar NOT NULL,
      observed_value       double precision,
      observed_unit        varchar,
      ticket_id            varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_optical_pm_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      pm_id                varchar NOT NULL,
      source_kind          varchar NOT NULL,
      source_vid           varchar NOT NULL,
      metric               varchar NOT NULL,
      value                double precision NOT NULL,
      unit                 varchar NOT NULL,
      bin_interval_seconds int,
      sla_threshold        double precision,
      breach               boolean NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_optical_ols_in_domain (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_optical_span_between_roadms (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_optical_otn_carries_service (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_domain_state AS
      SELECT controller_kind, jurisdiction, status, COUNT(*) AS domain_count
      FROM vertex_telecom_optical_domain
      GROUP BY controller_kind, jurisdiction, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_inventory AS
      SELECT 'ols' AS kind, vendor, status, COUNT(*) AS count_value FROM vertex_telecom_optical_ols GROUP BY vendor, status
      UNION ALL
      SELECT 'roadm' AS kind, wss_vendor AS vendor, status, COUNT(*) AS count_value FROM vertex_telecom_optical_roadm GROUP BY wss_vendor, status
      UNION ALL
      SELECT 'fiber_span' AS kind, owner_org_id AS vendor, status, COUNT(*) AS count_value FROM vertex_telecom_optical_fiber_span GROUP BY owner_org_id, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_channel_state AS
      SELECT modulation, fec, status,
             COUNT(*) AS channel_count,
             SUM(line_rate_gbps) AS total_line_rate_gbps
      FROM vertex_telecom_optical_dwdm_channel
      GROUP BY modulation, fec, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_otn_state AS
      SELECT odu_kind, client_service_kind, protection_kind, status, COUNT(*) AS otn_count
      FROM vertex_telecom_optical_otn_connection
      GROUP BY odu_kind, client_service_kind, protection_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_alarm_state AS
      SELECT source_kind, alarm_kind, severity, status, COUNT(*) AS alarm_count
      FROM vertex_telecom_optical_alarm
      GROUP BY source_kind, alarm_kind, severity, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_optical_pm_summary AS
      SELECT source_kind, metric, breach,
             COUNT(*) AS event_count,
             AVG(value) AS avg_value,
             MIN(value) AS min_value,
             MAX(value) AS max_value
      FROM vertex_telecom_optical_pm_event
      GROUP BY source_kind, metric, breach;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_pm_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_alarm_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_otn_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_channel_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_optical_domain_state`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_optical_otn_carries_service`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_optical_span_between_roadms`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_optical_ols_in_domain`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_pm_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_alarm`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_otn_connection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_dwdm_channel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_fiber_span`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_roadm`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_ols`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_optical_domain`.execute(db);
}
