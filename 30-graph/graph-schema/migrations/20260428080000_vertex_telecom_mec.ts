import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (MEC host inventory + EAS lifecycle); C (service call audit)

/**
 * telecom Phase 10 — MEC + 3GPP EAS edge plane.
 *
 * Builds on Phase 2 (RAN node), Phase 3 (interconnect agreements), Phase 4
 * (5G PDU session), Phase 7 (capacity forecast — relocation trigger),
 * Phase 8 (NWDAF SERVICE_EXPERIENCE — relocation trigger), and Phase 9
 * (O-Cloud — MEC host substrate). Edges connect EAS instances to host +
 * app package, EAS service calls to PDU session + EAS, and federations
 * to interconnect partner agreements.
 *
 * App packages, AppD descriptors, EAS state packages, and EAS payloads
 * are persisted only as `sha256:` hashes + `vault://` pointers.
 * UE identifiers are persisted only as `sha256:` hashes (Tier-3 PII).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_mec_host (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      host_id              varchar NOT NULL,
      o_cloud_id           varchar NOT NULL,
      vendor               varchar NOT NULL,
      host_fqdn            varchar NOT NULL,
      latitude             double precision NOT NULL,
      longitude            double precision NOT NULL,
      edge_zone            varchar NOT NULL,
      plmn_id              varchar NOT NULL,
      supported_vims       varchar,
      cpu_capacity         int,
      memory_capacity_gib  double precision,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_app_package (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      app_package_id       varchar NOT NULL,
      vendor               varchar NOT NULL,
      name                 varchar NOT NULL,
      version              varchar NOT NULL,
      app_descriptor       varchar NOT NULL,
      required_eases       varchar,
      latency_class        varchar NOT NULL,
      requested_flavor     varchar,
      package_hash         varchar NOT NULL,
      package_ref          varchar,
      onboarded_at         varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_eas (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      eas_id               varchar NOT NULL,
      app_package_vid      varchar NOT NULL,
      host_vid             varchar NOT NULL,
      eas_provider_id      varchar NOT NULL,
      snssai               varchar,
      dnn                  varchar,
      eas_fqdn             varchar NOT NULL,
      eas_ipv4             varchar,
      requested_flavor     varchar,
      instantiated_at      varchar NOT NULL,
      terminated_at        varchar,
      lifetime_seconds     double precision,
      termination_kind     varchar,
      termination_reason   varchar,
      terminated_by        varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_eas_discovery (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      discovery_id         varchar NOT NULL,
      ees_id               varchar NOT NULL,
      requesting_ac_id     varchar NOT NULL,
      ue_id_hash           varchar NOT NULL,
      ue_location_cell_id  varchar,
      eas_provider_id      varchar NOT NULL,
      requested_app_id     varchar NOT NULL,
      candidate_count      int NOT NULL,
      candidate_eas_ids    varchar,
      selected_eas_vid     varchar NOT NULL,
      selection_strategy   varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_eas_relocation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      relocation_id        varchar NOT NULL,
      eas_vid              varchar NOT NULL,
      from_host_vid        varchar NOT NULL,
      to_host_vid          varchar NOT NULL,
      trigger_kind         varchar NOT NULL,
      trigger_vid          varchar,
      acr_mode             varchar NOT NULL,
      state_package_hash   varchar,
      state_package_ref    varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_service_call (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      call_id              varchar NOT NULL,
      eas_vid              varchar NOT NULL,
      ue_id_hash           varchar NOT NULL,
      session_vid          varchar,
      method_kind          varchar NOT NULL,
      status_code          int NOT NULL,
      latency_ms           double precision,
      payload_in_bytes     bigint,
      payload_out_bytes    bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mec_federation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      federation_id        varchar NOT NULL,
      partner_operator_id  varchar NOT NULL,
      agreement_vid        varchar NOT NULL,
      federation_kind      varchar NOT NULL,
      exposed_zones        varchar,
      exposed_app_catalog  varchar,
      billing_mode         varchar NOT NULL,
      contract_ref         varchar,
      established_at       varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_mec_eas_on_host (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_mec_call_on_session (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_mec_federation_under_agreement (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mec_host_state AS
      SELECT vendor, edge_zone, plmn_id, status, COUNT(*) AS host_count
      FROM vertex_telecom_mec_host
      GROUP BY vendor, edge_zone, plmn_id, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mec_eas_inventory AS
      SELECT eas_provider_id, snssai, dnn, status, COUNT(*) AS eas_count
      FROM vertex_telecom_mec_eas
      GROUP BY eas_provider_id, snssai, dnn, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mec_relocation_summary AS
      SELECT trigger_kind, acr_mode, status, COUNT(*) AS relocation_count
      FROM vertex_telecom_mec_eas_relocation
      GROUP BY trigger_kind, acr_mode, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mec_service_call_health AS
      SELECT eas_vid, method_kind, status_code,
             COUNT(*) AS call_count,
             AVG(latency_ms) AS avg_latency_ms,
             SUM(payload_in_bytes)  AS total_in_bytes,
             SUM(payload_out_bytes) AS total_out_bytes
      FROM vertex_telecom_mec_service_call
      GROUP BY eas_vid, method_kind, status_code;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mec_federation_state AS
      SELECT federation_kind, billing_mode, status, COUNT(*) AS federation_count
      FROM vertex_telecom_mec_federation
      GROUP BY federation_kind, billing_mode, status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mec_federation_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mec_service_call_health`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mec_relocation_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mec_eas_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mec_host_state`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_mec_federation_under_agreement`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_mec_call_on_session`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_mec_eas_on_host`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_federation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_service_call`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_eas_relocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_eas_discovery`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_eas`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_app_package`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mec_host`.execute(db);
}
