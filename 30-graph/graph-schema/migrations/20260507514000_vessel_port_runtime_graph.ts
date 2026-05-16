import type { Kysely } from "kysely";
import { sql } from "kysely";

async function createVesselBase(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      label VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      props TEXT,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_created_date`)} ON ${sql.table(table)} (created_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
}

async function createEdgeBase(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      status VARCHAR,
      props TEXT,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createVesselBase(db, "vertex_vessel_ship");
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS ship_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS mmsi VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS vessel_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS flag_state VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION`.execute(db);

  await createVesselBase(db, "vertex_vessel_shipowner");
  await sql`ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS owner_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_shipowner ADD COLUMN IF NOT EXISTS country VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_vessel_ship_registry");
  await sql`ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS registry_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS flag_state VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_ship_registry ADD COLUMN IF NOT EXISTS authority_name VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_vessel_position");
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS position_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS mmsi VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS course DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS speed_knots DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS heading DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS navigation_status VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS destination VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS eta VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS received_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_position ADD COLUMN IF NOT EXISTS source_did VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_vessel_voyage");
  await sql`ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS voyage_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_voyage ADD COLUMN IF NOT EXISTS port_locode VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_vessel_port_call");
  await sql`ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS call_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_port_call ADD COLUMN IF NOT EXISTS port_locode VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_vessel_owner_link");
  await sql`ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS link_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS entity_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS link_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_vessel_owner_link ADD COLUMN IF NOT EXISTS linked_at VARCHAR`.execute(db);

  await createVesselBase(db, "vertex_port_berth");
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS berth_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS port_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS berth_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS length_m DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_port_berth ADD COLUMN IF NOT EXISTS depth_m DOUBLE PRECISION`.execute(db);

  await createVesselBase(db, "vertex_port_terminal");
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS terminal_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS port_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS terminal_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS operator VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_terminal ADD COLUMN IF NOT EXISTS capacity DOUBLE PRECISION`.execute(db);

  await createVesselBase(db, "vertex_port_call_event");
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS call_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS port_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS imo_number VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS event_timestamp VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_port_call_event ADD COLUMN IF NOT EXISTS berth_id VARCHAR`.execute(db);

  await createEdgeBase(db, "edge_vessel_owner_link");
  await createEdgeBase(db, "edge_vessel_port_call_endpoint");
  await createEdgeBase(db, "edge_port_infrastructure");
  await createEdgeBase(db, "edge_port_call_event");

  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_ship_ship_id ON vertex_vessel_ship (ship_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_ship_imo ON vertex_vessel_ship (imo_number)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_ship_mmsi ON vertex_vessel_ship (mmsi)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_ship_flag ON vertex_vessel_ship (flag_state)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_position_imo_received ON vertex_vessel_position (imo_number, received_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_position_mmsi_received ON vertex_vessel_position (mmsi, received_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_position_lat_lng ON vertex_vessel_position (latitude, longitude)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_port_call_imo ON vertex_vessel_port_call (imo_number)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vessel_port_call_port ON vertex_vessel_port_call (port_locode)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_port_berth_port ON vertex_port_berth (port_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_port_terminal_port ON vertex_port_terminal (port_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_port_call_event_port_type ON vertex_port_call_event (port_id, event_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_port_call_event_call ON vertex_port_call_event (call_id)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vessel_latest_position AS
    SELECT imo_number, max(received_at) AS latest_received_at, count(*) AS position_count
    FROM vertex_vessel_position
    GROUP BY imo_number
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vessel_flag_counts AS
    SELECT flag_state, count(*) AS vessel_count
    FROM vertex_vessel_ship
    GROUP BY flag_state
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_port_occupancy_event_counts AS
    SELECT port_id, event_type, count(*) AS event_count
    FROM vertex_port_call_event
    GROUP BY port_id, event_type
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_port_occupancy_event_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vessel_flag_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vessel_latest_position`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_port_call_event`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_port_infrastructure`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_vessel_port_call_endpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_vessel_owner_link`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_port_call_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_port_terminal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_port_berth`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_owner_link`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_port_call`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_voyage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_position`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_ship_registry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_shipowner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_ship`.execute(db);
}
