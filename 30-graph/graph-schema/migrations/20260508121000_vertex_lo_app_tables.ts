import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lo_shipment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      origin VARCHAR,
      destination VARCHAR,
      cargo_type VARCHAR,
      weight_kg DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lo_shipment_status ON vertex_lo_shipment (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lo_shipment_origin ON vertex_lo_shipment (origin)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lo_route (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      origin VARCHAR,
      destination VARCHAR,
      distance_km DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lo_route_status ON vertex_lo_route (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lo_route_origin ON vertex_lo_route (origin)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_lo_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lo_shipment`.execute(db);
}
