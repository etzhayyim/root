DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_legal_entity_supply_exposure;
DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_transport_context;
DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_supply_chain_trace;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_supply_chain_trace AS
  SELECT
    e.edge_id,
    e.domain,
    e.relationship,
    src.vertex_id AS src_vid,
    src.node_code AS src_node_code,
    src.node_kind AS src_node_kind,
    src.display_name AS src_name,
    src.country_code AS src_country_code,
    src.operator_did AS src_operator_did,
    dst.vertex_id AS dst_vid,
    dst.node_code AS dst_node_code,
    dst.node_kind AS dst_node_kind,
    dst.display_name AS dst_name,
    dst.country_code AS dst_country_code,
    dst.operator_did AS dst_operator_did,
    e.product_code,
    e.product_family,
    e.capacity_quantity,
    e.quantity_unit,
    e.lead_time_days,
    e.substitution_difficulty,
    e.dependency_weight,
    e.confidence,
    e.status
  FROM edge_jukyu_supply_dependency e
  JOIN vertex_jukyu_supply_node src ON src.vertex_id = e.src_vid
  JOIN vertex_jukyu_supply_node dst ON dst.vertex_id = e.dst_vid;

DROP INDEX IF EXISTS idx_edge_jukyu_transport_moves_product_dst;
DROP INDEX IF EXISTS idx_edge_jukyu_transport_moves_product_src;
DROP INDEX IF EXISTS idx_edge_jukyu_entity_controls_node_dst;
DROP INDEX IF EXISTS idx_edge_jukyu_entity_controls_node_src;
DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_vessel;
DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_supply_edge;
DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_domain_route;

DROP TABLE IF EXISTS edge_jukyu_transport_moves_product;
DROP TABLE IF EXISTS edge_jukyu_entity_controls_node;
DROP TABLE IF EXISTS vertex_jukyu_transport_leg;
