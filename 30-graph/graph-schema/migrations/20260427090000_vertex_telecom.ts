import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (subscriber/sim/service identity, billing) — pii split tier: A
// tier: C (cdr, sla_breach, invoice line items)

/**
 * telecom Phase 1 — eTOM Customer + Service Provisioning core (ADR-0056 BPMN-as-actor).
 *
 * PII split per ADR-0018: customer name / raw MSISDN / IMSI live in
 * vertex_telecom_subscriber_pii (Tier 3). Public AT Repo + main vertex hold
 * stable subscriber_id + hashed identifiers only.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_subscriber (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      subscriber_id    varchar NOT NULL,
      msisdn_hash      varchar NOT NULL,
      imsi_hash        varchar,
      kyc_status       varchar NOT NULL,
      plan_id          varchar NOT NULL,
      status           varchar NOT NULL,
      onboarded_at     varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_subscriber_pii (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      subscriber_vid   varchar NOT NULL,
      customer_name    varchar,
      msisdn           varchar,
      imsi             varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_sim (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      sim_id           varchar NOT NULL,
      iccid_hash       varchar NOT NULL,
      subscriber_vid   varchar NOT NULL,
      sim_type         varchar,
      status           varchar NOT NULL,
      activated_at     varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_service (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      service_id       varchar NOT NULL,
      subscriber_vid   varchar NOT NULL,
      sim_vid          varchar,
      service_type     varchar NOT NULL,
      plan_id          varchar NOT NULL,
      qos_profile      varchar,
      apn              varchar,
      status           varchar NOT NULL,
      provisioned_at   varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_cdr (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      cdr_id           varchar NOT NULL,
      subscriber_vid   varchar NOT NULL,
      service_vid      varchar NOT NULL,
      usage_type       varchar NOT NULL,
      units            double precision NOT NULL,
      unit_of_measure  varchar,
      peer_msisdn_hash varchar,
      started_at       varchar NOT NULL,
      ended_at         varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_invoice (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      invoice_id       varchar NOT NULL,
      cycle_id         varchar,
      subscriber_vid   varchar NOT NULL,
      period_start     varchar NOT NULL,
      period_end       varchar NOT NULL,
      currency         varchar,
      total_amount     double precision NOT NULL,
      voice_units      double precision,
      sms_units        double precision,
      data_units       double precision,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_sla_breach (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      breach_id        varchar NOT NULL,
      service_vid      varchar NOT NULL,
      breach_type      varchar NOT NULL,
      severity         varchar NOT NULL,
      metric           varchar,
      observed_value   double precision,
      sla_threshold    double precision,
      observed_at      varchar NOT NULL,
      ticket_id        varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_subscriber_state AS
      SELECT plan_id, kyc_status, status, COUNT(*) AS subscriber_count
      FROM vertex_telecom_subscriber
      GROUP BY plan_id, kyc_status, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_service_health AS
      SELECT s.service_type, s.plan_id, s.status,
             COUNT(DISTINCT s.vertex_id) AS service_count,
             COUNT(b.vertex_id) AS open_breaches
      FROM vertex_telecom_service s
      LEFT JOIN vertex_telecom_sla_breach b
        ON b.service_vid = s.vertex_id AND b.status = 'open'
      GROUP BY s.service_type, s.plan_id, s.status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_service_health`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_subscriber_state`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sla_breach`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_cdr`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_service`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sim`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_subscriber_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_subscriber`.execute(db);
}
