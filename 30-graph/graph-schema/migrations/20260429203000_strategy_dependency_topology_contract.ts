import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Strategy dependency topology contract for LLM planning.
 *
 * Direction contract:
 *   edge_depends_on.src_vid depends on edge_depends_on.dst_vid.
 *
 * RisingWave streaming materialized views should not own recursive topo
 * sorting. The graph input and cheap quality checks live in SQL; an app/agent
 * worker computes Kahn order, detects full cycles, and writes the snapshot to
 * vertex_dependency_topology_order for stable LLM reads.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_dependency_topology_order (
      graph_scope VARCHAR NOT NULL,
      vertex_id VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      display_name VARCHAR,
      vertex_kind VARCHAR,
      topo_rank BIGINT NOT NULL,
      reverse_topo_rank BIGINT NOT NULL,
      topo_level BIGINT,
      dependency_count BIGINT NOT NULL,
      dependent_count BIGINT NOT NULL,
      unresolved_dependency_count BIGINT NOT NULL,
      cycle_status VARCHAR NOT NULL,
      computed_at VARCHAR NOT NULL,
      algorithm VARCHAR NOT NULL,
      payload_json VARCHAR,
      PRIMARY KEY (graph_scope, vertex_id)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_dep_topology_order_scope_reverse ON vertex_dependency_topology_order (graph_scope, reverse_topo_rank)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dep_topology_order_scope_topo ON vertex_dependency_topology_order (graph_scope, topo_rank)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dep_topology_order_cycle ON vertex_dependency_topology_order (graph_scope, cycle_status)`.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_known_vertex AS
    SELECT vertex_id, 'action' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_action
    UNION ALL
    SELECT vertex_id, 'infra_capability' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_infra_capability
    UNION ALL
    SELECT vertex_id, 'goal' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_goal
    UNION ALL
    SELECT vertex_id, 'milestone' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_milestone
    UNION ALL
    SELECT vertex_id, 'business_case' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_business_case
    UNION ALL
    SELECT vertex_id, 'revenue_stream' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_revenue_stream
    UNION ALL
    SELECT vertex_id, 'cost_center' AS vertex_kind, display_name, category AS status, owner_did, sensitivity_ord
    FROM vertex_cost_center
    UNION ALL
    SELECT vertex_id, 'risk' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_risk
    UNION ALL
    SELECT vertex_id, 'business_entity' AS vertex_kind, legal_name AS display_name, status, owner_did, sensitivity_ord
    FROM vertex_business_entity
    UNION ALL
    SELECT vertex_id, 'business_domain' AS vertex_kind, display_name, status, owner_did, sensitivity_ord
    FROM vertex_business_domain
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_edge_contract AS
    SELECT
      edge_id,
      'strategy' AS graph_scope,
      src_vid AS dependent_vid,
      dst_vid AS prerequisite_vid,
      'src_depends_on_dst' AS direction_contract,
      dep_type,
      label,
      slack_days,
      owner_did,
      sensitivity_ord,
      created_date
    FROM edge_depends_on
    WHERE src_vid IS NOT NULL
      AND dst_vid IS NOT NULL
      AND src_vid <> ''
      AND dst_vid <> ''
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_strategy_dependency_degree AS
    WITH edges AS (
      SELECT dependent_vid, prerequisite_vid
      FROM view_strategy_dependency_edge_contract
    ),
    nodes AS (
      SELECT vertex_id FROM view_strategy_dependency_known_vertex
      UNION
      SELECT dependent_vid AS vertex_id FROM edges
      UNION
      SELECT prerequisite_vid AS vertex_id FROM edges
    ),
    dep_counts AS (
      SELECT dependent_vid AS vertex_id, COUNT(*) AS dependency_count
      FROM edges
      GROUP BY dependent_vid
    ),
    dependent_counts AS (
      SELECT prerequisite_vid AS vertex_id, COUNT(*) AS dependent_count
      FROM edges
      GROUP BY prerequisite_vid
    )
    SELECT
      'strategy' AS graph_scope,
      n.vertex_id,
      kv.vertex_kind,
      kv.display_name,
      kv.status,
      COALESCE(dc.dependency_count, 0) AS dependency_count,
      COALESCE(pc.dependent_count, 0) AS dependent_count,
      a.topo_level AS declared_topo_level,
      kv.owner_did,
      kv.sensitivity_ord
    FROM nodes n
    LEFT JOIN view_strategy_dependency_known_vertex kv ON kv.vertex_id = n.vertex_id
    LEFT JOIN vertex_action a ON a.vertex_id = n.vertex_id
    LEFT JOIN dep_counts dc ON dc.vertex_id = n.vertex_id
    LEFT JOIN dependent_counts pc ON pc.vertex_id = n.vertex_id
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_dangling_edges AS
    SELECT
      e.edge_id,
      e.graph_scope,
      e.dependent_vid,
      e.prerequisite_vid,
      CASE
        WHEN d.vertex_id IS NULL AND p.vertex_id IS NULL THEN 'both_missing'
        WHEN d.vertex_id IS NULL THEN 'dependent_missing'
        WHEN p.vertex_id IS NULL THEN 'prerequisite_missing'
        ELSE 'ok'
      END AS dangling_status,
      e.dep_type,
      e.label,
      e.owner_did,
      e.sensitivity_ord
    FROM view_strategy_dependency_edge_contract e
    LEFT JOIN view_strategy_dependency_known_vertex d ON d.vertex_id = e.dependent_vid
    LEFT JOIN view_strategy_dependency_known_vertex p ON p.vertex_id = e.prerequisite_vid
    WHERE d.vertex_id IS NULL OR p.vertex_id IS NULL
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_self_cycles AS
    SELECT
      edge_id,
      graph_scope,
      dependent_vid AS vertex_id,
      prerequisite_vid,
      'self_cycle' AS cycle_status,
      dep_type,
      label,
      owner_did,
      sensitivity_ord
    FROM view_strategy_dependency_edge_contract
    WHERE dependent_vid = prerequisite_vid
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_two_node_cycles AS
    SELECT
      a.graph_scope,
      a.dependent_vid AS vertex_a,
      a.prerequisite_vid AS vertex_b,
      a.edge_id AS edge_a_to_b,
      b.edge_id AS edge_b_to_a,
      'two_node_cycle' AS cycle_status,
      a.owner_did,
      a.sensitivity_ord
    FROM view_strategy_dependency_edge_contract a
    JOIN view_strategy_dependency_edge_contract b
      ON b.graph_scope = a.graph_scope
     AND b.dependent_vid = a.prerequisite_vid
     AND b.prerequisite_vid = a.dependent_vid
    WHERE a.dependent_vid < a.prerequisite_vid
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_strategy_dependency_llm_payload AS
    SELECT
      COALESCE(o.graph_scope, d.graph_scope) AS graph_scope,
      d.vertex_id,
      d.vertex_kind,
      d.display_name,
      d.status,
      d.dependency_count,
      d.dependent_count,
      d.declared_topo_level,
      o.topo_rank,
      o.reverse_topo_rank,
      o.topo_level,
      COALESCE(o.unresolved_dependency_count, 0) AS unresolved_dependency_count,
      COALESCE(o.cycle_status, 'unknown') AS cycle_status,
      o.computed_at,
      o.algorithm,
      CONCAT(
        '{"graphScope":"', COALESCE(o.graph_scope, d.graph_scope),
        '","vertexId":"', d.vertex_id,
        '","vertexKind":"', COALESCE(d.vertex_kind, 'unknown'),
        '","displayName":"', COALESCE(REPLACE(d.display_name, '"', '\\"'), ''),
        '","dependencyCount":', CAST(d.dependency_count AS VARCHAR),
        ',"dependentCount":', CAST(d.dependent_count AS VARCHAR),
        ',"topoRank":', COALESCE(CAST(o.topo_rank AS VARCHAR), 'null'),
        ',"reverseTopoRank":', COALESCE(CAST(o.reverse_topo_rank AS VARCHAR), 'null'),
        ',"cycleStatus":"', COALESCE(o.cycle_status, 'unknown'),
        '"}'
      ) AS payload_json
    FROM mv_strategy_dependency_degree d
    LEFT JOIN vertex_dependency_topology_order o
      ON o.graph_scope = d.graph_scope
     AND o.vertex_id = d.vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_llm_payload`.execute(db);
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_two_node_cycles`.execute(db);
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_self_cycles`.execute(db);
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_dangling_edges`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_strategy_dependency_degree`.execute(db);
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_edge_contract`.execute(db);
  await sql`DROP VIEW IF EXISTS view_strategy_dependency_known_vertex`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_dep_topology_order_cycle`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_dep_topology_order_scope_topo`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_dep_topology_order_scope_reverse`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_dependency_topology_order`.execute(db);
}
