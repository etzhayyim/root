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
    );

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
    );

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
    );

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
    );

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
    );

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
    );

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
    );

CREATE MATERIALIZED VIEW mv_telecom_subscriber_state AS
      SELECT plan_id, kyc_status, status, COUNT(*) AS subscriber_count
      FROM vertex_telecom_subscriber
      GROUP BY plan_id, kyc_status, status;

CREATE MATERIALIZED VIEW mv_telecom_service_health AS
      SELECT s.service_type, s.plan_id, s.status,
             COUNT(DISTINCT s.vertex_id) AS service_count,
             COUNT(b.vertex_id) AS open_breaches
      FROM vertex_telecom_service s
      LEFT JOIN vertex_telecom_sla_breach b
        ON b.service_vid = s.vertex_id AND b.status = 'open'
      GROUP BY s.service_type, s.plan_id, s.status;
