import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (RCOI / venue / PPS-MO catalog); C (ANQP query, AAA exchange, sessions)

/**
 * telecom Phase 13 — WBA OpenRoaming + Hotspot 2.0 (Wi-Fi convergence).
 *
 * Builds on Phase 1 (subscriber), Phase 3 (interconnect/roaming partners),
 * Phase 4 (5G subscriber profile + PDU session — ATSSS bridge target),
 * Phase 11 (NPN — enterprise Wi-Fi), Phase 5 (VoWiFi voice ↔ WLAN session).
 *
 * UE MAC / IP / EAP credentials persisted as `sha256:` hashes only.
 * PPS-MO XML body, ANDSP policy, EAP credentials persist via vault://+sha256.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_wlan_rcoi (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      rcoi_id              varchar NOT NULL,
      oi_hex               varchar NOT NULL,
      federation           varchar NOT NULL,
      identity_provider_org_id varchar NOT NULL,
      agreement_vid        varchar,
      profile_kind         varchar NOT NULL,
      valid_from           varchar NOT NULL,
      valid_until          varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_venue (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      venue_id             varchar NOT NULL,
      venue_name           varchar NOT NULL,
      venue_group          varchar NOT NULL,
      venue_type           varchar NOT NULL,
      jurisdiction         varchar NOT NULL,
      latitude             double precision,
      longitude            double precision,
      hessid               varchar,
      ssid                 varchar NOT NULL,
      advertised_rcoi_vids varchar NOT NULL,
      osu_kind             varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_pps_mo (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      pps_mo_id            varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      profile_vid          varchar,
      identity_provider_org_id varchar NOT NULL,
      eap_method           varchar NOT NULL,
      credential_kind      varchar NOT NULL,
      credential_ref       varchar,
      advertised_rcoi_vids varchar NOT NULL,
      pps_mo_hash          varchar NOT NULL,
      pps_mo_ref           varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_anqp_query (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      query_id             varchar NOT NULL,
      venue_vid            varchar NOT NULL,
      ue_mac_hash          varchar NOT NULL,
      gas_protocol         varchar NOT NULL,
      query_element        varchar NOT NULL,
      response_hash        varchar NOT NULL,
      response_size        bigint,
      latency_ms           double precision,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_session (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      session_id           varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      pps_mo_vid           varchar NOT NULL,
      venue_vid            varchar NOT NULL,
      rcoi_vid             varchar NOT NULL,
      ue_mac_hash          varchar NOT NULL,
      eap_method           varchar NOT NULL,
      ip_assignment        varchar,
      attached_at          varchar NOT NULL,
      released_at          varchar,
      duration_seconds     double precision,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_roaming_exchange (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      exchange_id          varchar NOT NULL,
      session_vid          varchar NOT NULL,
      transport_kind       varchar NOT NULL,
      peer_kind            varchar NOT NULL,
      partner_org_id       varchar NOT NULL,
      drr_instance_id      varchar,
      message_kind         varchar NOT NULL,
      result_code          int NOT NULL,
      session_time_seconds bigint,
      ingress_bytes        bigint,
      egress_bytes         bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_andsp_bridge (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      bridge_id            varchar NOT NULL,
      session_vid          varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      atsss_mode           varchar NOT NULL,
      andsp_policy_hash    varchar,
      andsp_policy_ref     varchar,
      target_snssai        varchar,
      target_dnn           varchar,
      target_pdu_session_vid varchar,
      transition_kind      varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_wlan_roaming_invoice (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      invoice_id           varchar NOT NULL,
      partner_org_id       varchar NOT NULL,
      period_start         varchar NOT NULL,
      period_end           varchar NOT NULL,
      currency             varchar NOT NULL,
      receivable_amount    double precision NOT NULL,
      payable_amount       double precision NOT NULL,
      net_amount           double precision NOT NULL,
      session_count        bigint,
      total_session_time_seconds bigint,
      total_ingress_bytes  bigint,
      total_egress_bytes   bigint,
      issued_at            varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_wlan_session_under_rcoi (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_wlan_session_at_venue (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_wlan_bridge_to_pdu (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_rcoi_state AS
      SELECT federation, profile_kind, status, COUNT(*) AS rcoi_count
      FROM vertex_telecom_wlan_rcoi
      GROUP BY federation, profile_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_venue_inventory AS
      SELECT venue_group, jurisdiction, osu_kind, status, COUNT(*) AS venue_count
      FROM vertex_telecom_wlan_venue
      GROUP BY venue_group, jurisdiction, osu_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_session_volume AS
      SELECT venue_vid, eap_method, ip_assignment, status,
             COUNT(*) AS session_count,
             SUM(duration_seconds) AS total_duration_seconds
      FROM vertex_telecom_wlan_session
      GROUP BY venue_vid, eap_method, ip_assignment, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_roaming_aaa_health AS
      SELECT transport_kind, peer_kind, message_kind, result_code, COUNT(*) AS exchange_count
      FROM vertex_telecom_wlan_roaming_exchange
      GROUP BY transport_kind, peer_kind, message_kind, result_code;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_andsp_handoff AS
      SELECT atsss_mode, transition_kind, status, COUNT(*) AS bridge_count
      FROM vertex_telecom_wlan_andsp_bridge
      GROUP BY atsss_mode, transition_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_wlan_settlement_balance AS
      SELECT partner_org_id, currency,
             SUM(receivable_amount) AS total_receivable,
             SUM(payable_amount)    AS total_payable,
             SUM(net_amount)        AS net_balance,
             COUNT(*)               AS invoice_count
      FROM vertex_telecom_wlan_roaming_invoice
      WHERE status IN ('issued','settled')
      GROUP BY partner_org_id, currency;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_settlement_balance`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_andsp_handoff`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_roaming_aaa_health`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_session_volume`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_venue_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_rcoi_state`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_wlan_bridge_to_pdu`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_wlan_session_at_venue`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_wlan_session_under_rcoi`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_roaming_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_andsp_bridge`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_roaming_exchange`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_session`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_anqp_query`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_pps_mo`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_venue`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_wlan_rcoi`.execute(db);
}
