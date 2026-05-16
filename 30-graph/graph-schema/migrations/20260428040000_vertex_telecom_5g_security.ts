import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (NWDAF analytics + SCP routing); C (SEPP key rotation hashes audit)

/**
 * telecom Phase 8 — 5G Analytics + Service Routing + Roaming Security
 * (NWDAF / SCP / SEPP). Builds on Phase 4 (5G Core SBA) and Phase 3
 * (interconnect agreements / roaming partners). Edges connect analytics
 * subscriptions/results to consumer NF + target, SCP routes to consumer NF,
 * SEPP contexts to remote PLMN partner agreement.
 *
 * Cryptographic material (TLS keys, PRINS keys, JWS signing keys, X.509
 * certificates) never persisted in graph — only sha256 hashes + vault://
 * pointers. SBI request URI / message body never persisted — payloadHash
 * and metadata only.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_nwdaf_subscription (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      subscription_id      varchar NOT NULL,
      consumer_nf_vid      varchar NOT NULL,
      nwdaf_nf_vid         varchar NOT NULL,
      analytics_id         varchar NOT NULL,
      target_of_analytics_kind varchar NOT NULL,
      target_of_analytics_vid varchar NOT NULL,
      snssai               varchar,
      dnn                  varchar,
      reporting_period_seconds int NOT NULL,
      accuracy_requirement varchar,
      expires_at           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_nwdaf_result (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      result_id            varchar NOT NULL,
      subscription_vid     varchar NOT NULL,
      analytics_id         varchar NOT NULL,
      sequence_number      bigint NOT NULL,
      confidence           double precision,
      validity_period_seconds int,
      payload_hash         varchar NOT NULL,
      payload_ref          varchar,
      payload_size         bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_scp_route (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      route_id             varchar NOT NULL,
      scp_nf_vid           varchar NOT NULL,
      source_nf_vid        varchar NOT NULL,
      target_nf_vid        varchar NOT NULL,
      target_service_name  varchar NOT NULL,
      target_api_version   varchar,
      routing_mode         varchar NOT NULL,
      request_uri_hash     varchar,
      method_kind          varchar NOT NULL,
      status_code          int NOT NULL,
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
    CREATE TABLE vertex_telecom_scp_discovery (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      discovery_id         varchar NOT NULL,
      scp_nf_vid           varchar NOT NULL,
      requester_nf_vid     varchar NOT NULL,
      target_nf_type       varchar NOT NULL,
      snssai               varchar,
      dnn                  varchar,
      plmn_id              varchar,
      candidate_count      int NOT NULL,
      candidate_nf_ids     varchar,
      selected_nf_vid      varchar NOT NULL,
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
    CREATE TABLE vertex_telecom_sepp_context (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      context_id           varchar NOT NULL,
      local_sepp_nf_vid    varchar NOT NULL,
      remote_sepp_fqdn     varchar NOT NULL,
      local_plmn_id        varchar NOT NULL,
      remote_plmn_id       varchar NOT NULL,
      agreement_vid        varchar NOT NULL,
      n32_cipher_suite     varchar NOT NULL,
      telescopic_fqdn_enabled boolean,
      certificate_ref      varchar,
      established_at       varchar NOT NULL,
      valid_until          varchar NOT NULL,
      torn_down_at         varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_sepp_message (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      message_id           varchar NOT NULL,
      context_vid          varchar NOT NULL,
      direction            varchar NOT NULL,
      n32_channel          varchar NOT NULL,
      modification_policy_applied boolean,
      payload_hash         varchar NOT NULL,
      payload_size         bigint,
      security_result      varchar NOT NULL,
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
    CREATE TABLE vertex_telecom_sepp_key_rotation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      rotation_id          varchar NOT NULL,
      context_vid          varchar NOT NULL,
      key_kind             varchar NOT NULL,
      old_key_hash         varchar,
      new_key_hash         varchar NOT NULL,
      new_key_ref          varchar,
      rotation_reason      varchar NOT NULL,
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
    CREATE TABLE vertex_telecom_sepp_trust_negotiation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      negotiation_id       varchar NOT NULL,
      context_vid          varchar NOT NULL,
      negotiation_kind     varchar NOT NULL,
      ipx_provider_id      varchar,
      allowed_cipher_suites varchar,
      agreed_cipher_suite  varchar,
      modification_policy  varchar,
      outcome              varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_analytics_for_target (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_scp_routes_to_nf (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_sepp_context_for_partner (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nwdaf_subscription_state AS
      SELECT analytics_id, target_of_analytics_kind, status, COUNT(*) AS subscription_count
      FROM vertex_telecom_nwdaf_subscription
      GROUP BY analytics_id, target_of_analytics_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_scp_routing_health AS
      SELECT target_service_name, routing_mode, status_code,
             COUNT(*) AS request_count,
             AVG(latency_ms) AS avg_latency_ms
      FROM vertex_telecom_scp_route
      GROUP BY target_service_name, routing_mode, status_code;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_scp_discovery_load AS
      SELECT target_nf_type, selection_strategy,
             AVG(candidate_count) AS avg_candidate_count,
             COUNT(*) AS discovery_count
      FROM vertex_telecom_scp_discovery
      GROUP BY target_nf_type, selection_strategy;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_sepp_message_security AS
      SELECT n32_channel, direction, security_result,
             COUNT(*) AS message_count,
             AVG(latency_ms) AS avg_latency_ms
      FROM vertex_telecom_sepp_message
      GROUP BY n32_channel, direction, security_result;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_sepp_key_rotation_summary AS
      SELECT key_kind, rotation_reason, COUNT(*) AS rotation_count
      FROM vertex_telecom_sepp_key_rotation
      GROUP BY key_kind, rotation_reason;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_sepp_key_rotation_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_sepp_message_security`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_scp_discovery_load`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_scp_routing_health`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nwdaf_subscription_state`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_sepp_context_for_partner`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_scp_routes_to_nf`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_analytics_for_target`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sepp_trust_negotiation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sepp_key_rotation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sepp_message`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_sepp_context`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_scp_discovery`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_scp_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nwdaf_result`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nwdaf_subscription`.execute(db);
}
