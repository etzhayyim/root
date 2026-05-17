import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Data Center Ops dependency graph spine (RisingWave physical schema).
 *
 * Scope:
 * - vertex_data_center_dependency (land/facility/permit/isco/apqc/power/rack/server/license/...)
 * - edge_data_center_dependency (DEPENDS_ON edges)
 * - indexes for actor/read path
 * - materialized views for reverse-topology display and domain summary
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_data_center_dependency (
      vertex_id          VARCHAR PRIMARY KEY,
      actor_did          VARCHAR,
      dependency_key     VARCHAR,
      display_name       VARCHAR,
      dependency_domain  VARCHAR,
      dependency_level   BIGINT,
      source             VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_actor_key ON vertex_data_center_dependency (actor_did, dependency_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_domain_level ON vertex_data_center_dependency (dependency_domain, dependency_level)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_level ON vertex_data_center_dependency (dependency_level)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_data_center_dependency (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      actor_did          VARCHAR,
      edge_kind          VARCHAR,
      criticality        VARCHAR,
      path_weight        BIGINT,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_src ON edge_data_center_dependency (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_dst ON edge_data_center_dependency (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_actor_kind ON edge_data_center_dependency (actor_did, edge_kind)`.execute(db);

  await sql`
    INSERT INTO vertex_data_center_dependency (
      vertex_id,
      actor_did,
      dependency_key,
      display_name,
      dependency_domain,
      dependency_level,
      source,
      status,
      created_at,
      updated_at,
      props
    ) VALUES
      ('dcdep:dc-operations', 'did:web:data-center-ops.etzhayyim.com', 'dc-operations', 'Data Center Operations', 'operations', 0, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:apqc-operations-framework', 'did:web:data-center-ops.etzhayyim.com', 'apqc-operations-framework', 'APQC Operations Process', 'apqc', 1, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:isco-workforce', 'did:web:data-center-ops.etzhayyim.com', 'isco-workforce', 'ISCO Workforce', 'isco', 1, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:sla-governance', 'did:web:data-center-ops.etzhayyim.com', 'sla-governance', 'SLA Governance', 'governance', 1, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:license-compliance', 'did:web:data-center-ops.etzhayyim.com', 'license-compliance', 'License and Compliance', 'license', 2, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:server-fleet', 'did:web:data-center-ops.etzhayyim.com', 'server-fleet', 'Server Fleet', 'server', 2, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:rack-capacity', 'did:web:data-center-ops.etzhayyim.com', 'rack-capacity', 'Rack Capacity', 'rack', 3, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:power-grid', 'did:web:data-center-ops.etzhayyim.com', 'power-grid', 'Power Distribution', 'power', 3, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:facility-site', 'did:web:data-center-ops.etzhayyim.com', 'facility-site', 'Facility Site', 'facility', 4, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:permit-approval', 'did:web:data-center-ops.etzhayyim.com', 'permit-approval', 'Permits and Approvals', 'permit', 5, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep:land-plot', 'did:web:data-center-ops.etzhayyim.com', 'land-plot', 'Land Plot', 'land', 6, 'migration:20260416124000', 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}')
  `.execute(db);

  await sql`
    INSERT INTO edge_data_center_dependency (
      edge_id,
      src_vid,
      dst_vid,
      actor_did,
      edge_kind,
      criticality,
      path_weight,
      status,
      created_at,
      updated_at,
      props
    ) VALUES
      ('dcdep-edge:dc-operations->apqc-operations-framework', 'dcdep:dc-operations', 'dcdep:apqc-operations-framework', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:dc-operations->isco-workforce', 'dcdep:dc-operations', 'dcdep:isco-workforce', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:dc-operations->sla-governance', 'dcdep:dc-operations', 'dcdep:sla-governance', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:apqc-operations-framework->license-compliance', 'dcdep:apqc-operations-framework', 'dcdep:license-compliance', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:apqc-operations-framework->server-fleet', 'dcdep:apqc-operations-framework', 'dcdep:server-fleet', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:isco-workforce->server-fleet', 'dcdep:isco-workforce', 'dcdep:server-fleet', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'medium', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:sla-governance->license-compliance', 'dcdep:sla-governance', 'dcdep:license-compliance', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'medium', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:server-fleet->rack-capacity', 'dcdep:server-fleet', 'dcdep:rack-capacity', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:rack-capacity->power-grid', 'dcdep:rack-capacity', 'dcdep:power-grid', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:rack-capacity->facility-site', 'dcdep:rack-capacity', 'dcdep:facility-site', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:power-grid->facility-site', 'dcdep:power-grid', 'dcdep:facility-site', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:license-compliance->permit-approval', 'dcdep:license-compliance', 'dcdep:permit-approval', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:facility-site->permit-approval', 'dcdep:facility-site', 'dcdep:permit-approval', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}'),
      ('dcdep-edge:permit-approval->land-plot', 'dcdep:permit-approval', 'dcdep:land-plot', 'did:web:data-center-ops.etzhayyim.com', 'depends_on', 'high', 1, 'active', CAST(NOW() AS VARCHAR), CAST(NOW() AS VARCHAR), '{}')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_data_center_dependency_reverse_topology AS
    WITH in_deg AS (
      SELECT dst_vid, COUNT(*) AS in_degree
      FROM edge_data_center_dependency
      GROUP BY dst_vid
    ),
    out_deg AS (
      SELECT src_vid, COUNT(*) AS out_degree
      FROM edge_data_center_dependency
      GROUP BY src_vid
    )
    SELECT
      v.vertex_id,
      v.actor_did,
      v.dependency_key,
      v.display_name,
      v.dependency_domain,
      v.dependency_level,
      COALESCE(i.in_degree, 0) AS in_degree,
      COALESCE(o.out_degree, 0) AS out_degree,
      (v.dependency_level * 100 + COALESCE(i.in_degree, 0)) AS reverse_topology_rank,
      v.status,
      v.updated_at
    FROM vertex_data_center_dependency v
    LEFT JOIN in_deg i ON i.dst_vid = v.vertex_id
    LEFT JOIN out_deg o ON o.src_vid = v.vertex_id
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_dc_reverse_actor_level ON mv_data_center_dependency_reverse_topology (actor_did, dependency_level)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_mv_dc_reverse_domain_rank ON mv_data_center_dependency_reverse_topology (dependency_domain, reverse_topology_rank)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_data_center_dependency_domain_summary AS
    SELECT
      v.actor_did,
      v.dependency_domain,
      COUNT(*) AS node_count,
      MIN(v.dependency_level) AS min_level,
      MAX(v.dependency_level) AS max_level,
      SUM(CASE WHEN e.criticality = 'high' THEN 1 ELSE 0 END) AS high_critical_edges,
      SUM(CASE WHEN e.criticality = 'medium' THEN 1 ELSE 0 END) AS medium_critical_edges
    FROM vertex_data_center_dependency v
    LEFT JOIN edge_data_center_dependency e
      ON e.dst_vid = v.vertex_id
    GROUP BY v.actor_did, v.dependency_domain
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_dc_domain_summary_actor_domain ON mv_data_center_dependency_domain_summary (actor_did, dependency_domain)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_data_center_dependency_domain_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_data_center_dependency_reverse_topology`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_data_center_dependency`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_data_center_dependency`.execute(db);
}
