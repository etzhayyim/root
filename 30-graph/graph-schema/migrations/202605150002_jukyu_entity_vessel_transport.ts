import { Kysely, sql } from 'kysely';

// tier: B

/**
 * Jukyu entity/vessel/transport graph extension.
 *
 * Connects real legal-entity anchors, vessel registry rows, and transport legs
 * to the Jukyu supply dependency graph. The resident LangGraph consumes
 * mv_jukyu_transport_context as additional pressure during Pregel propagation.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_transport_leg (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      leg_id VARCHAR NOT NULL,
      domain VARCHAR NOT NULL,
      supply_edge_id VARCHAR,
      cargo_vid VARCHAR,
      vessel_vid VARCHAR,
      vessel_imo VARCHAR,
      vessel_mmsi VARCHAR,
      origin_node_vid VARCHAR,
      destination_node_vid VARCHAR,
      origin_locode VARCHAR,
      destination_locode VARCHAR,
      carrier_did VARCHAR,
      shipowner_did VARCHAR,
      operator_did VARCHAR,
      charterer_did VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      quantity DOUBLE PRECISION,
      quantity_unit VARCHAR,
      transport_mode VARCHAR,
      status VARCHAR,
      departure_at VARCHAR,
      eta_at VARCHAR,
      observed_at VARCHAR,
      eta_delay_hours DOUBLE PRECISION,
      route_risk_score DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      evidence_json VARCHAR,
      source_table VARCHAR,
      source_vertex_id VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jukyu_entity_controls_node (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      domain VARCHAR,
      role VARCHAR,
      ownership_pct DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      source_table VARCHAR,
      status VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jukyu_transport_moves_product (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      domain VARCHAR NOT NULL,
      relationship VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      quantity DOUBLE PRECISION,
      quantity_unit VARCHAR,
      lead_time_days DOUBLE PRECISION,
      dependency_weight DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      status VARCHAR
    )
  `.execute(db);

  await sql`ALTER TABLE edge_jukyu_supply_dependency ADD COLUMN IF NOT EXISTS transport_mode VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_jukyu_supply_dependency ADD COLUMN IF NOT EXISTS route_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_jukyu_supply_dependency ADD COLUMN IF NOT EXISTS route_risk_score DOUBLE PRECISION`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_transport_leg_domain_route ON vertex_jukyu_transport_leg (domain, origin_locode, destination_locode)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_transport_leg_supply_edge ON vertex_jukyu_transport_leg (supply_edge_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_transport_leg_vessel ON vertex_jukyu_transport_leg (vessel_imo, vessel_mmsi)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_entity_controls_node_src ON edge_jukyu_entity_controls_node (src_vid, role)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_entity_controls_node_dst ON edge_jukyu_entity_controls_node (dst_vid, domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_transport_moves_product_src ON edge_jukyu_transport_moves_product (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_transport_moves_product_dst ON edge_jukyu_transport_moves_product (dst_vid)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_supply_chain_trace`.execute(db);
  await sql`
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
        e.transport_mode,
        e.route_kind,
        e.route_risk_score,
        e.confidence,
        e.status
      FROM edge_jukyu_supply_dependency e
      JOIN vertex_jukyu_supply_node src ON src.vertex_id = e.src_vid
      JOIN vertex_jukyu_supply_node dst ON dst.vertex_id = e.dst_vid

  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_transport_context AS
      SELECT
        tl.vertex_id AS transport_leg_vid,
        tl.leg_id,
        tl.domain,
        tl.supply_edge_id,
        e.src_vid,
        e.dst_vid,
        tl.cargo_vid,
        tl.vessel_vid,
        tl.vessel_imo,
        tl.vessel_mmsi,
                tl.origin_node_vid,
        tl.destination_node_vid,
        tl.origin_locode,
        tl.destination_locode,
        tl.carrier_did,
            tl.shipowner_did,
            tl.operator_did,
            tl.charterer_did,
            tl.product_code,
        tl.product_family,
        tl.quantity,
        tl.quantity_unit,
        tl.transport_mode,
        tl.status,
        tl.departure_at,
        tl.eta_at,
        tl.observed_at,
        tl.eta_delay_hours,
        tl.route_risk_score,
        tl.confidence,
        tl.evidence_json
      FROM vertex_jukyu_transport_leg tl
      LEFT JOIN edge_jukyu_supply_dependency e ON e.edge_id = tl.supply_edge_id
      WHERE tl.status IS NULL OR tl.status <> 'deleted'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_legal_entity_supply_exposure AS
      SELECT
        entity_vid AS legal_entity_vid,
        domain,
        role,
        COUNT(DISTINCT node_vid)::bigint AS node_count,
        COUNT(DISTINCT transport_leg_vid)::bigint AS transport_leg_count,
        MAX(route_risk_score) AS max_route_risk_score,
        AVG(confidence) AS avg_confidence
      FROM (
        SELECT src_vid AS entity_vid, dst_vid AS node_vid, domain, role,
               CAST(NULL AS VARCHAR) AS transport_leg_vid,
               CAST(NULL AS DOUBLE PRECISION) AS route_risk_score,
               confidence
        FROM edge_jukyu_entity_controls_node
        WHERE status IS NULL OR status <> 'deleted'
        UNION ALL
        SELECT carrier_did AS entity_vid, destination_node_vid AS node_vid, domain, 'carrier' AS role,
               vertex_id AS transport_leg_vid, route_risk_score, confidence
        FROM vertex_jukyu_transport_leg
        WHERE carrier_did IS NOT NULL AND (status IS NULL OR status <> 'deleted')
        UNION ALL
        SELECT shipowner_did AS entity_vid, destination_node_vid AS node_vid, domain, 'shipowner' AS role,
               vertex_id AS transport_leg_vid, route_risk_score, confidence
        FROM vertex_jukyu_transport_leg
        WHERE shipowner_did IS NOT NULL AND (status IS NULL OR status <> 'deleted')
        UNION ALL
        SELECT operator_did AS entity_vid, destination_node_vid AS node_vid, domain, 'vessel_operator' AS role,
               vertex_id AS transport_leg_vid, route_risk_score, confidence
        FROM vertex_jukyu_transport_leg
        WHERE operator_did IS NOT NULL AND (status IS NULL OR status <> 'deleted')
        UNION ALL
        SELECT charterer_did AS entity_vid, destination_node_vid AS node_vid, domain, 'charterer' AS role,
               vertex_id AS transport_leg_vid, route_risk_score, confidence
        FROM vertex_jukyu_transport_leg
        WHERE charterer_did IS NOT NULL AND (status IS NULL OR status <> 'deleted')
      ) joined
      WHERE entity_vid IS NOT NULL AND entity_vid <> ''
      GROUP BY entity_vid, domain, role
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_legal_entity_supply_exposure`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_transport_context`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_supply_chain_trace`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jukyu_transport_moves_product_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jukyu_transport_moves_product_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jukyu_entity_controls_node_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jukyu_entity_controls_node_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_vessel`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_supply_edge`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_jukyu_transport_leg_domain_route`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jukyu_transport_moves_product`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jukyu_entity_controls_node`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_transport_leg`.execute(db);
}
