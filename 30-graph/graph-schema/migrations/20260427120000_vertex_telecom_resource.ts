import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C (Resource inventory + KPI samples)

/**
 * telecom Phase 2 — Resource domain (TMF634 Catalog / TMF639 Inventory /
 * TMF671 Performance Management). Builds on Phase 1
 * (`vertex_telecom_subscriber/sim/service/cdr/invoice/sla_breach`) by adding
 * spectrum / site / RAN node / asset / incident / maintenance / RMA / KPI
 * tables. Edges connect Resource rows to Phase 1 service rows so a site
 * incident can fan out into per-service SLA breaches.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_telecom_spectrum_license (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      license_id       varchar NOT NULL,
      jurisdiction     varchar NOT NULL,
      band             varchar NOT NULL,
      low_mhz          double precision NOT NULL,
      high_mhz         double precision NOT NULL,
      holder_org_id    varchar NOT NULL,
      region           varchar,
      technology       varchar,
      valid_from       varchar NOT NULL,
      valid_until      varchar NOT NULL,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_cell_site (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      site_id          varchar NOT NULL,
      name             varchar NOT NULL,
      latitude         double precision NOT NULL,
      longitude        double precision NOT NULL,
      jurisdiction     varchar NOT NULL,
      tower_owner_org_id varchar,
      height_meters    double precision,
      power_source     varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_ran_node (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      node_id          varchar NOT NULL,
      site_vid         varchar NOT NULL,
      node_type        varchar NOT NULL,
      generation       varchar NOT NULL,
      vendor           varchar,
      model            varchar,
      spectrum_license_vid varchar,
      plmn_id          varchar,
      status           varchar NOT NULL,
      activated_at     varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_network_asset (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      asset_id         varchar NOT NULL,
      serial_number    varchar NOT NULL,
      asset_kind       varchar NOT NULL,
      vendor           varchar,
      model            varchar,
      installed_site_vid varchar,
      installed_node_vid varchar,
      installed_at     varchar,
      warranty_until   varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_site_incident (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      incident_id      varchar NOT NULL,
      site_vid         varchar NOT NULL,
      node_vid         varchar,
      incident_kind    varchar NOT NULL,
      severity         varchar NOT NULL,
      detected_at      varchar NOT NULL,
      resolved_at      varchar,
      summary          varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_maintenance_window (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      window_id        varchar NOT NULL,
      site_vid         varchar,
      node_vid         varchar,
      asset_vid        varchar,
      maintenance_kind varchar NOT NULL,
      planned_start    varchar NOT NULL,
      planned_end      varchar NOT NULL,
      vendor_org_id    varchar,
      summary          varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_rma_case (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      rma_id           varchar NOT NULL,
      asset_vid        varchar NOT NULL,
      vendor_org_id    varchar NOT NULL,
      fault_category   varchar NOT NULL,
      fault_description varchar,
      opened_at        varchar NOT NULL,
      expected_return_at varchar,
      closed_at        varchar,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_telecom_kpi_sample (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      sample_id        varchar NOT NULL,
      node_vid         varchar NOT NULL,
      metric           varchar NOT NULL,
      value            double precision NOT NULL,
      unit             varchar,
      sampled_at       varchar NOT NULL,
      sla_threshold    double precision,
      breach           boolean NOT NULL,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_telecom_site_hosts_node (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_node_uses_spectrum (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_asset_installed_at (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_service_runs_on_node (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_telecom_incident_affects_service (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_site_health AS
      SELECT s.vertex_id AS site_vid, s.site_id, s.jurisdiction,
             COUNT(DISTINCT r.vertex_id) AS ran_node_count,
             COUNT(DISTINCT i.vertex_id) FILTER (WHERE i.status='open') AS open_incidents,
             COUNT(DISTINCT m.vertex_id) FILTER (WHERE m.status IN ('planned','in_progress')) AS open_maintenance
      FROM vertex_telecom_cell_site s
      LEFT JOIN vertex_telecom_ran_node r ON r.site_vid = s.vertex_id
      LEFT JOIN vertex_telecom_site_incident i ON i.site_vid = s.vertex_id
      LEFT JOIN vertex_telecom_maintenance_window m ON m.site_vid = s.vertex_id
      GROUP BY s.vertex_id, s.site_id, s.jurisdiction;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_spectrum_utilization AS
      SELECT l.vertex_id AS license_vid, l.license_id, l.band, l.jurisdiction,
             COUNT(DISTINCT r.vertex_id) AS bound_node_count
      FROM vertex_telecom_spectrum_license l
      LEFT JOIN vertex_telecom_ran_node r ON r.spectrum_license_vid = l.vertex_id
      WHERE l.status = 'active'
      GROUP BY l.vertex_id, l.license_id, l.band, l.jurisdiction;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_telecom_kpi_breach_rate AS
      SELECT node_vid, metric,
             COUNT(*) AS sample_count,
             COUNT(*) FILTER (WHERE breach) AS breach_count
      FROM vertex_telecom_kpi_sample
      GROUP BY node_vid, metric;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_kpi_breach_rate`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_spectrum_utilization`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_telecom_site_health`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_incident_affects_service`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_service_runs_on_node`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_asset_installed_at`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_node_uses_spectrum`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_telecom_site_hosts_node`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_kpi_sample`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_rma_case`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_maintenance_window`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_site_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_network_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_ran_node`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_cell_site`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_telecom_spectrum_license`.execute(db);
}
