import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (SMO + RIC + xApp/rApp registration); C (E2 indication audit)

/**
 * telecom Phase 9 — Open RAN (O-RAN Alliance: SMO / Non-RT RIC /
 * Near-RT RIC / A1 / E2 / O1 / O2). Builds on Phase 2 (RAN node
 * inventory), Phase 4 (5G Core SBA), and Phase 8 (NWDAF analytics).
 *
 * rApp and xApp packages, A1 policy statements, O1 YANG configs, and O2
 * deployment packages are persisted only as `sha256:` hashes + `vault://`
 * pointers — raw bodies never enter the graph. E2 ASN.1 PER messages
 * are also hash-only (header + message hashes).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_oran_smo (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      smo_id               varchar NOT NULL,
      vendor               varchar NOT NULL,
      release_version      varchar NOT NULL,
      plmn_id              varchar NOT NULL,
      non_rt_ric_endpoint  varchar NOT NULL,
      o1_endpoint          varchar NOT NULL,
      o2_endpoint          varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_rapp (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      rapp_id              varchar NOT NULL,
      smo_vid              varchar NOT NULL,
      vendor               varchar NOT NULL,
      name                 varchar NOT NULL,
      version              varchar NOT NULL,
      use_cases            varchar,
      required_a1_policy_types varchar,
      required_r1_services varchar,
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
    CREATE TABLE vertex_telecom_oran_xapp (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      xapp_id              varchar NOT NULL,
      near_rt_ric_vid      varchar NOT NULL,
      vendor               varchar NOT NULL,
      name                 varchar NOT NULL,
      version              varchar NOT NULL,
      use_cases            varchar,
      e2_node_vids         varchar,
      supported_ran_functions varchar,
      package_hash         varchar NOT NULL,
      package_ref          varchar,
      deployed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_a1_policy (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      policy_instance_id   varchar NOT NULL,
      rapp_vid             varchar NOT NULL,
      near_rt_ric_vid      varchar NOT NULL,
      policy_type_id       varchar NOT NULL,
      use_case             varchar NOT NULL,
      scope_kind           varchar NOT NULL,
      scope_vid            varchar NOT NULL,
      statement_hash       varchar NOT NULL,
      statement_ref        varchar,
      action               varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_e2_subscription (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      subscription_id      varchar NOT NULL,
      xapp_vid             varchar NOT NULL,
      e2_node_vid          varchar NOT NULL,
      ran_function_id      varchar NOT NULL,
      service_model        varchar NOT NULL,
      event_trigger_kind   varchar NOT NULL,
      action_kind          varchar NOT NULL,
      reporting_period_ms  int,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_e2_indication (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      indication_id        varchar NOT NULL,
      subscription_vid     varchar NOT NULL,
      sequence_number      bigint NOT NULL,
      indication_type      varchar NOT NULL,
      header_hash          varchar NOT NULL,
      message_hash         varchar NOT NULL,
      message_size         bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_o1_config (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      config_id            varchar NOT NULL,
      smo_vid              varchar NOT NULL,
      target_kind          varchar NOT NULL,
      target_vid           varchar NOT NULL,
      interface_transport  varchar NOT NULL,
      operation            varchar NOT NULL,
      yang_module_set      varchar,
      config_hash          varchar NOT NULL,
      config_ref           varchar,
      config_size          bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_oran_o2_resource (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      resource_id          varchar NOT NULL,
      smo_vid              varchar NOT NULL,
      o_cloud_id           varchar NOT NULL,
      interface_kind       varchar NOT NULL,
      resource_kind        varchar NOT NULL,
      deployment_manager   varchar NOT NULL,
      package_ref          varchar,
      package_hash         varchar NOT NULL,
      requested_flavor     varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_oran_a1_targets_policy (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_oran_e2_for_node (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_oran_o1_targets_nf (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_oran_app_inventory AS
      SELECT 'rapp' AS app_kind, vendor, status, COUNT(*) AS app_count
      FROM vertex_telecom_oran_rapp
      GROUP BY vendor, status
      UNION ALL
      SELECT 'xapp' AS app_kind, vendor, status, COUNT(*) AS app_count
      FROM vertex_telecom_oran_xapp
      GROUP BY vendor, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_oran_a1_policy_state AS
      SELECT use_case, scope_kind, action, status, COUNT(*) AS policy_count
      FROM vertex_telecom_oran_a1_policy
      GROUP BY use_case, scope_kind, action, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_oran_e2_subscription_state AS
      SELECT service_model, event_trigger_kind, action_kind, status, COUNT(*) AS subscription_count
      FROM vertex_telecom_oran_e2_subscription
      GROUP BY service_model, event_trigger_kind, action_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_oran_o1_config_state AS
      SELECT target_kind, interface_transport, operation, status, COUNT(*) AS config_count
      FROM vertex_telecom_oran_o1_config
      GROUP BY target_kind, interface_transport, operation, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_oran_o2_resource_state AS
      SELECT interface_kind, resource_kind, deployment_manager, status, COUNT(*) AS resource_count
      FROM vertex_telecom_oran_o2_resource
      GROUP BY interface_kind, resource_kind, deployment_manager, status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_oran_o2_resource_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_oran_o1_config_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_oran_e2_subscription_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_oran_a1_policy_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_oran_app_inventory`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_oran_o1_targets_nf`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_oran_e2_for_node`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_oran_a1_targets_policy`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_o2_resource`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_o1_config`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_e2_indication`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_e2_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_a1_policy`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_xapp`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_rapp`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_oran_smo`.execute(db);
}
