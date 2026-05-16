import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B (NSD/VNFD catalog + NS/VNF lifecycle); C (scale/heal/sdn flow audit)

/**
 * telecom Phase 12 — SDN-NFV (ETSI MANO + ONAP). NSD/VNFD/CNFD onboard,
 * NS/VNF lifecycle, scaling/healing, SDN southbound flow provisioning.
 *
 * Builds on Phase 4 (5G NF instances — VNF can implement them via
 * `mappedNfInstanceId`), Phase 7 (alarm + capacity_forecast — heal/scale
 * triggers), Phase 8 (NWDAF NF_LOAD — scale trigger), Phase 9 (O-RAN
 * O-Cloud — VIM substrate), and Phase 10 (MEC host — edge VIM).
 *
 * Descriptor / package bodies persist only as `sha256:` hashes + `vault://`
 * pointers. SDN flow match/action bodies persist only as hashes.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_nfv_nsd (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      nsd_id               varchar NOT NULL,
      vendor               varchar NOT NULL,
      name                 varchar NOT NULL,
      version              varchar NOT NULL,
      descriptor_format    varchar NOT NULL,
      constituent_vnfd_ids varchar,
      virtual_links        varchar,
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
    CREATE TABLE vertex_telecom_nfv_vnfd (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      vnfd_id              varchar NOT NULL,
      vendor               varchar NOT NULL,
      name                 varchar NOT NULL,
      version              varchar NOT NULL,
      vnf_kind             varchar NOT NULL,
      descriptor_format    varchar NOT NULL,
      deployment_flavors   varchar,
      required_vims        varchar,
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
    CREATE TABLE vertex_telecom_nfv_ns (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ns_id                varchar NOT NULL,
      nsd_vid              varchar NOT NULL,
      nfvo_nf_vid          varchar NOT NULL,
      vim_ids              varchar,
      snssai               varchar,
      dnn                  varchar,
      deployment_flavor    varchar NOT NULL,
      parameters           varchar,
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
    CREATE TABLE vertex_telecom_nfv_vnf (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      vnf_id               varchar NOT NULL,
      ns_vid               varchar NOT NULL,
      vnfd_vid             varchar NOT NULL,
      vnfm_nf_vid          varchar NOT NULL,
      vim_id               varchar NOT NULL,
      deployment_flavor    varchar NOT NULL,
      requested_vcpus      int,
      requested_memory_gib double precision,
      mapped_nf_instance_vid varchar,
      instantiated_at      varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_nfv_scale_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      scale_event_id       varchar NOT NULL,
      vnf_vid              varchar NOT NULL,
      scale_kind           varchar NOT NULL,
      scale_direction      varchar NOT NULL,
      aspect_id            varchar,
      from_instance_count  int NOT NULL,
      to_instance_count    int NOT NULL,
      delta                int NOT NULL,
      trigger_kind         varchar NOT NULL,
      trigger_vid          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_nfv_heal_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      heal_event_id        varchar NOT NULL,
      vnf_vid              varchar NOT NULL,
      heal_cause           varchar NOT NULL,
      heal_kind            varchar NOT NULL,
      alarm_vid            varchar,
      recreate_affected_instances boolean,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_nfv_sdn_flow (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      flow_id              varchar NOT NULL,
      sdn_controller_id    varchar NOT NULL,
      southbound_protocol  varchar NOT NULL,
      switch_dpid          varchar NOT NULL,
      table_id             int NOT NULL,
      priority             int NOT NULL,
      match_hash           varchar NOT NULL,
      action_hash          varchar NOT NULL,
      action               varchar NOT NULL,
      vnf_vid              varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_nfv_vnf_under_ns (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_nfv_vnf_implements_nf (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_nfv_sdn_flow_for_vnf (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_catalog_state AS
      SELECT 'nsd' AS desc_kind, vendor, descriptor_format, status, COUNT(*) AS desc_count
      FROM vertex_telecom_nfv_nsd
      GROUP BY vendor, descriptor_format, status
      UNION ALL
      SELECT 'vnfd' AS desc_kind, vendor, descriptor_format, status, COUNT(*) AS desc_count
      FROM vertex_telecom_nfv_vnfd
      GROUP BY vendor, descriptor_format, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_ns_inventory AS
      SELECT deployment_flavor, snssai, status, COUNT(*) AS ns_count
      FROM vertex_telecom_nfv_ns
      GROUP BY deployment_flavor, snssai, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_vnf_inventory AS
      SELECT vim_id, deployment_flavor, status, COUNT(*) AS vnf_count
      FROM vertex_telecom_nfv_vnf
      GROUP BY vim_id, deployment_flavor, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_scale_summary AS
      SELECT scale_kind, scale_direction, trigger_kind, COUNT(*) AS event_count, SUM(delta) AS total_delta
      FROM vertex_telecom_nfv_scale_event
      GROUP BY scale_kind, scale_direction, trigger_kind;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_heal_summary AS
      SELECT heal_cause, heal_kind, status, COUNT(*) AS event_count
      FROM vertex_telecom_nfv_heal_event
      GROUP BY heal_cause, heal_kind, status;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_nfv_sdn_flow_state AS
      SELECT sdn_controller_id, southbound_protocol, action, status, COUNT(*) AS flow_count
      FROM vertex_telecom_nfv_sdn_flow
      GROUP BY sdn_controller_id, southbound_protocol, action, status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_sdn_flow_state`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_heal_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_scale_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_vnf_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_ns_inventory`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nfv_catalog_state`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_nfv_sdn_flow_for_vnf`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_nfv_vnf_implements_nf`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_nfv_vnf_under_ns`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_sdn_flow`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_heal_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_scale_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_vnf`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_ns`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_vnfd`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_nfv_nsd`.execute(db);
}
