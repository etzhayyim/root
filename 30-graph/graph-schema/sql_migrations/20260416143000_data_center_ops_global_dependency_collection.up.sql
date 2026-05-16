CREATE TABLE IF NOT EXISTS vertex_data_center_dependency_global (
      vertex_id              VARCHAR PRIMARY KEY,
      actor_did              VARCHAR,
      country_code           VARCHAR,
      country_name           VARCHAR,
      dependency_key         VARCHAR,
      display_name           VARCHAR,
      dependency_domain      VARCHAR,
      dependency_level       BIGINT,
      in_degree              BIGINT,
      out_degree             BIGINT,
      reverse_topology_rank  BIGINT,
      domain_coverage_rate   DOUBLE PRECISION,
      domain_world_total     BIGINT,
      status                 VARCHAR,
      collected_at           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_global_actor_country ON vertex_data_center_dependency_global (actor_did, country_code);

CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_global_domain_level ON vertex_data_center_dependency_global (dependency_domain, dependency_level);

CREATE INDEX IF NOT EXISTS idx_vertex_dc_dep_global_node ON vertex_data_center_dependency_global (dependency_key, reverse_topology_rank);

CREATE TABLE IF NOT EXISTS edge_data_center_dependency_global (
      edge_id            VARCHAR PRIMARY KEY,
      actor_did          VARCHAR,
      country_code       VARCHAR,
      country_name       VARCHAR,
      src_vertex_id      VARCHAR,
      dst_vertex_id      VARCHAR,
      from_node_key      VARCHAR,
      to_node_key        VARCHAR,
      edge_kind          VARCHAR,
      criticality        VARCHAR,
      path_weight        BIGINT,
      status             VARCHAR,
      collected_at       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_global_actor_country ON edge_data_center_dependency_global (actor_did, country_code);

CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_global_path ON edge_data_center_dependency_global (from_node_key, to_node_key);

CREATE INDEX IF NOT EXISTS idx_edge_dc_dep_global_criticality ON edge_data_center_dependency_global (criticality, path_weight);

DELETE FROM edge_data_center_dependency_global WHERE actor_did = 'did:web:data-center-ops.gftd.ai';

DELETE FROM vertex_data_center_dependency_global WHERE actor_did = 'did:web:data-center-ops.gftd.ai';

INSERT INTO vertex_data_center_dependency_global (
      vertex_id,
      actor_did,
      country_code,
      country_name,
      dependency_key,
      display_name,
      dependency_domain,
      dependency_level,
      in_degree,
      out_degree,
      reverse_topology_rank,
      domain_coverage_rate,
      domain_world_total,
      status,
      collected_at
    )
    WITH domain_coverage AS (
      SELECT
        CASE
          WHEN domain = 'isco' THEN 'isco'
          WHEN domain = 'energy' THEN 'power'
          WHEN domain IN ('license_keiyaku', 'oss_license', 'sw_license_key') THEN 'license'
          ELSE NULL
        END AS dependency_domain,
        MAX(COALESCE(coverage_rate, 0)) AS coverage_rate,
        SUM(COALESCE(world_total, 0)) AS world_total
      FROM mv_world_coverage_live
      WHERE domain IN ('isco', 'energy', 'license_keiyaku', 'oss_license', 'sw_license_key')
      GROUP BY 1
    )
    SELECT
      'dcdep-global:' || c.code || ':' || v.dependency_key AS vertex_id,
      v.actor_did,
      c.code AS country_code,
      c.name AS country_name,
      v.dependency_key,
      v.display_name,
      v.dependency_domain,
      v.dependency_level,
      v.in_degree,
      v.out_degree,
      v.reverse_topology_rank,
      COALESCE(d.coverage_rate, 0) AS domain_coverage_rate,
      COALESCE(d.world_total, 0) AS domain_world_total,
      v.status,
      v.updated_at AS collected_at
    FROM mv_data_center_dependency_reverse_topology v
    CROSS JOIN view_iso3166_country c
    LEFT JOIN domain_coverage d
      ON d.dependency_domain = v.dependency_domain
    WHERE c.code IS NOT NULL;

INSERT INTO edge_data_center_dependency_global (
      edge_id,
      actor_did,
      country_code,
      country_name,
      src_vertex_id,
      dst_vertex_id,
      from_node_key,
      to_node_key,
      edge_kind,
      criticality,
      path_weight,
      status,
      collected_at
    )
    SELECT
      'dcdep-global-edge:' || c.code || ':' || e.edge_id AS edge_id,
      e.actor_did,
      c.code AS country_code,
      c.name AS country_name,
      'dcdep-global:' || c.code || ':' || sv.dependency_key AS src_vertex_id,
      'dcdep-global:' || c.code || ':' || dv.dependency_key AS dst_vertex_id,
      sv.dependency_key AS from_node_key,
      dv.dependency_key AS to_node_key,
      e.edge_kind,
      e.criticality,
      e.path_weight,
      e.status,
      e.updated_at AS collected_at
    FROM edge_data_center_dependency e
    JOIN vertex_data_center_dependency sv
      ON sv.vertex_id = e.src_vid
    JOIN vertex_data_center_dependency dv
      ON dv.vertex_id = e.dst_vid
    CROSS JOIN view_iso3166_country c
    WHERE c.code IS NOT NULL;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_data_center_dependency_global_actor AS
    SELECT
      vertex_id AS dependency_vertex_id,
      actor_did,
      country_code,
      country_name,
      dependency_key,
      display_name,
      dependency_domain,
      dependency_level,
      in_degree,
      out_degree,
      reverse_topology_rank,
      domain_coverage_rate,
      domain_world_total,
      status,
      collected_at
    FROM vertex_data_center_dependency_global;

CREATE INDEX IF NOT EXISTS idx_mv_dc_dep_global_actor_country ON mv_data_center_dependency_global_actor (actor_did, country_code);

CREATE INDEX IF NOT EXISTS idx_mv_dc_dep_global_actor_domain ON mv_data_center_dependency_global_actor (dependency_domain, dependency_level);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_data_center_dependency_global_edge AS
    SELECT
      edge_id,
      actor_did,
      country_code,
      country_name,
      src_vertex_id,
      dst_vertex_id,
      from_node_key,
      to_node_key,
      edge_kind,
      criticality,
      path_weight,
      status,
      collected_at
    FROM edge_data_center_dependency_global;

CREATE INDEX IF NOT EXISTS idx_mv_dc_dep_global_edge_country ON mv_data_center_dependency_global_edge (actor_did, country_code);

CREATE INDEX IF NOT EXISTS idx_mv_dc_dep_global_edge_path ON mv_data_center_dependency_global_edge (from_node_key, to_node_key);
