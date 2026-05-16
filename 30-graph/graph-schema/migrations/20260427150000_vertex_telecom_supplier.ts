import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C (interconnect / roaming / MNP wholesale records)

/**
 * telecom Phase 3 — Supplier/Partner domain (Interconnect + Roaming +
 * Number Portability). Builds on Phase 1 (subscriber/service/CDR) and
 * Phase 2 (Resource). Edges connect Phase 3 partners back to subscriber
 * (MNP) and to interconnect agreements.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_interconnect_agreement (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      agreement_id         varchar NOT NULL,
      peer_org_id          varchar NOT NULL,
      peer_kind            varchar NOT NULL,
      jurisdiction         varchar NOT NULL,
      settlement_currency  varchar NOT NULL,
      rate_card_ref        varchar,
      valid_from           varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_roaming_partner (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      partner_id         varchar NOT NULL,
      peer_org_id        varchar NOT NULL,
      tadig_code         varchar NOT NULL,
      plmn_id            varchar,
      sccp_gt_prefix     varchar,
      imsi_prefix        varchar,
      agreement_vid      varchar NOT NULL,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_tap_file (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      tap_file_id      varchar NOT NULL,
      partner_vid      varchar NOT NULL,
      file_type        varchar NOT NULL,
      file_sequence    bigint NOT NULL,
      transfer_date    varchar NOT NULL,
      voice_units      double precision,
      sms_units        double precision,
      data_units       double precision,
      total_charge     double precision NOT NULL,
      currency         varchar NOT NULL,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_roaming_invoice (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      invoice_id       varchar NOT NULL,
      partner_vid      varchar NOT NULL,
      period_start     varchar NOT NULL,
      period_end       varchar NOT NULL,
      direction        varchar NOT NULL,
      currency         varchar NOT NULL,
      receivable_amount double precision NOT NULL,
      payable_amount   double precision NOT NULL,
      net_amount       double precision NOT NULL,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_interconnect_cdr (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      cdr_id               varchar NOT NULL,
      agreement_vid        varchar NOT NULL,
      partner_vid          varchar NOT NULL,
      direction            varchar NOT NULL,
      usage_type           varchar NOT NULL,
      units                double precision NOT NULL,
      unit_of_measure      varchar,
      originating_msisdn_hash varchar,
      terminating_msisdn_hash varchar,
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
    CREATE TABLE vertex_telecom_number_range (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      range_id               varchar NOT NULL,
      jurisdiction           varchar NOT NULL,
      country_code           varchar NOT NULL,
      start_msisdn           varchar NOT NULL,
      end_msisdn             varchar NOT NULL,
      regulator_allocation_id varchar,
      allocated_at           varchar NOT NULL,
      plmn_id                varchar,
      status                 varchar NOT NULL,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_mnp_request (
      vertex_id           varchar PRIMARY KEY,
      _seq                bigint,
      created_date        date,
      sensitivity_ord     int,
      owner_did           varchar,
      request_id          varchar NOT NULL,
      direction           varchar NOT NULL,
      msisdn_hash         varchar NOT NULL,
      subscriber_vid      varchar NOT NULL,
      counterpart_partner_vid varchar NOT NULL,
      requested_at        varchar NOT NULL,
      scheduled_cutover_at varchar,
      completed_at        varchar,
      auth_code_hash      varchar,
      status              varchar NOT NULL,
      created_at          varchar,
      org_id              varchar,
      user_id             varchar,
      actor_id            varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_partner_under_agreement (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_tap_for_partner (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_subscriber_ported (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_roaming_settlement_balance AS
      SELECT partner_vid, currency,
             SUM(receivable_amount) AS total_receivable,
             SUM(payable_amount)    AS total_payable,
             SUM(net_amount)        AS net_balance,
             COUNT(*)               AS invoice_count
      FROM vertex_telecom_roaming_invoice
      WHERE status IN ('issued','settled')
      GROUP BY partner_vid, currency;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_mnp_pipeline AS
      SELECT direction, status, COUNT(*) AS request_count
      FROM vertex_telecom_mnp_request
      GROUP BY direction, status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_mnp_pipeline`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_roaming_settlement_balance`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_subscriber_ported`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_tap_for_partner`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_partner_under_agreement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_mnp_request`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_number_range`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_interconnect_cdr`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_roaming_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_tap_file`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_roaming_partner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_interconnect_agreement`.execute(db);
}
