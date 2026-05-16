import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C (5G control-plane state — auth events kept short retention; CDR is C)

/**
 * telecom Phase 4 — 5G Core SBA control plane (AMF / SMF / UDM / UDR /
 * AUSF / PCF / NRF / NSSF / CHF). Builds on Phase 1 (subscriber/service),
 * Phase 2 (RAN node), Phase 3 (interconnect/MNP). SUPI persisted as
 * sha256 hash; AKA K never persisted (akaCredentialRef is a vault://
 * pointer).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_nf_instance (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      nf_instance_id       varchar NOT NULL,
      nf_type              varchar NOT NULL,
      plmn_id              varchar NOT NULL,
      s_nssai_list         varchar,
      fqdn                 varchar,
      ipv4_address         varchar,
      capacity             int,
      priority             int,
      heartbeat_interval   int,
      registered_at        varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_subscriber_profile_5g (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      profile_id           varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      supi_hash            varchar NOT NULL,
      suci_scheme_id       varchar,
      slice_subscription_list varchar,
      dnn_list             varchar NOT NULL,
      ambr_uplink_kbps     int,
      ambr_downlink_kbps   int,
      aka_credential_ref   varchar,
      status               varchar NOT NULL,
      provisioned_at       varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_auth_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      auth_event_id        varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      supi_hash            varchar NOT NULL,
      serving_network      varchar,
      auth_method          varchar NOT NULL,
      result               varchar NOT NULL,
      success              boolean NOT NULL,
      rand_hash            varchar,
      ausf_nf_vid          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_amf_registration (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      registration_id      varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      supi_hash            varchar,
      registration_type    varchar NOT NULL,
      ran_node_vid         varchar NOT NULL,
      amf_nf_vid           varchar NOT NULL,
      tai_plmn_id          varchar,
      tai_tac              varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_slice_selection (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      selection_id         varchar NOT NULL,
      registration_vid     varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      requested_nssai_list varchar,
      allowed_nssai_list   varchar,
      selected_snssai      varchar NOT NULL,
      nssf_nf_vid          varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_policy_decision (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      decision_id          varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      session_vid          varchar,
      snssai               varchar NOT NULL,
      dnn                  varchar NOT NULL,
      qos_flow_list        varchar,
      charging_method      varchar NOT NULL,
      rating_group         varchar,
      sponsor_id           varchar,
      pcf_nf_vid           varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_pdu_session (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      session_id           varchar NOT NULL,
      registration_vid     varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      snssai               varchar NOT NULL,
      dnn                  varchar NOT NULL,
      session_type         varchar NOT NULL,
      smf_nf_vid           varchar NOT NULL,
      upf_nf_vid           varchar,
      ran_node_vid         varchar,
      policy_decision_vid  varchar,
      ue_ipv4              varchar,
      ue_ipv6_prefix       varchar,
      established_at       varchar NOT NULL,
      released_at          varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_charging_record (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      charging_id          varchar NOT NULL,
      session_vid          varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      rating_group         varchar NOT NULL,
      units                double precision NOT NULL,
      unit_of_measure      varchar,
      currency             varchar NOT NULL,
      amount               double precision NOT NULL,
      charging_method      varchar NOT NULL,
      chf_nf_vid           varchar,
      started_at           varchar NOT NULL,
      ended_at             varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_session_uses_slice (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_session_under_policy (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_session_on_node (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_charging_for_session (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_charging_to_subscriber (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nf_topology AS
      SELECT nf_type, plmn_id, status, COUNT(*) AS instance_count
      FROM vertex_telecom_nf_instance
      GROUP BY nf_type, plmn_id, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_active_sessions AS
      SELECT snssai, dnn, session_type, COUNT(*) AS active_session_count
      FROM vertex_telecom_pdu_session
      WHERE status = 'active'
      GROUP BY snssai, dnn, session_type;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_5g_charging_summary AS
      SELECT subscriber_vid, currency, charging_method,
             SUM(amount) AS total_amount,
             SUM(units) AS total_units,
             COUNT(*)   AS record_count
      FROM vertex_telecom_charging_record
      GROUP BY subscriber_vid, currency, charging_method;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_auth_failure_rate AS
      SELECT auth_method, result, COUNT(*) AS event_count
      FROM vertex_telecom_auth_event
      GROUP BY auth_method, result;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_auth_failure_rate`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_5g_charging_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_active_sessions`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nf_topology`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_charging_to_subscriber`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_charging_for_session`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_session_on_node`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_session_under_policy`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_session_uses_slice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_charging_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_pdu_session`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_policy_decision`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_slice_selection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_amf_registration`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_auth_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_subscriber_profile_5g`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nf_instance`.execute(db);
}
