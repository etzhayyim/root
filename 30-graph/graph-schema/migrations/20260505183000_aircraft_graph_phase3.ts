// Aircraft graph integration Phase 3 (2026-05-05).
//
// Wires the live tracker (vertex_aircraft_state / vertex_aircraft_track) into
// the existing entity graph: registered aircraft master → operator/owner LEI
// (existing vertex_aircraft + edge_aircraft_operated_by/_owned_by),
// + parts (new vertex_aircraft_part + 2 edges)
// + purpose / mission output (new vertex_flight_purpose + 1 edge)
// + ISO 3166-1 alpha-2 normalization (column on vertex_aircraft).
//
// Also adds the linker columns + edges to bridge the live snapshot tables
// to the registered master so XRPC enrichment can JOIN cheaply.
//
// RW DDL only (CREATE TABLE / CREATE INDEX / INSERT WHERE NOT EXISTS).
// No ON CONFLICT, no transactions.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. Bridge live → registered ────────────────────────────────────────
  // vertex_aircraft_state already has icao24; add aircraft_did for typed
  // join to vertex_aircraft.did. Backfill is BPMN-driven (next migration).
  await sql`ALTER TABLE vertex_aircraft_state ADD COLUMN IF NOT EXISTS aircraft_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_aircraft_track ADD COLUMN IF NOT EXISTS aircraft_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_aircraft ADD COLUMN IF NOT EXISTS registration_country_iso2 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_aircraft ADD COLUMN IF NOT EXISTS purpose_code VARCHAR`.execute(db);

  // ── 2. Aircraft parts ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_aircraft_part (
      vertex_id            VARCHAR PRIMARY KEY,
      part_kind            VARCHAR,
      manufacturer_did     VARCHAR,
      manufacturer_lei     VARCHAR,
      model_number         VARCHAR,
      serial_number        VARCHAR,
      certification_authority VARCHAR,
      certification_id     VARCHAR,
      installed_at         VARCHAR,
      removed_at           VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      actor_did            VARCHAR DEFAULT 'did:web:maps.etzhayyim.com:flightradar',
      org_did              VARCHAR DEFAULT 'anon',
      sensitivity_ord      INTEGER DEFAULT 1,
      owner_did            VARCHAR DEFAULT 'did:web:maps.etzhayyim.com',
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_part_kind ON vertex_aircraft_part (part_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_part_manufacturer_lei ON vertex_aircraft_part (manufacturer_lei)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_aircraft_has_part (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     VARCHAR,
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR,
      effective_from   VARCHAR,
      effective_to     VARCHAR,
      role             VARCHAR,
      source_url       VARCHAR,
      source_license   VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_has_part_src ON edge_aircraft_has_part (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_has_part_dst ON edge_aircraft_has_part (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_aircraft_part_made_by (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     VARCHAR,
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR,
      effective_from   VARCHAR,
      effective_to     VARCHAR,
      source_url       VARCHAR,
      source_license   VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_part_made_by_src ON edge_aircraft_part_made_by (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_part_made_by_dst ON edge_aircraft_part_made_by (dst_vid)`.execute(db);

  // ── 3. Flight purpose / mission output ────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_purpose (
      vertex_id            VARCHAR PRIMARY KEY,
      purpose_code         VARCHAR,
      label_en             VARCHAR,
      label_ja             VARCHAR,
      description          VARCHAR,
      regulated_under      VARCHAR,
      actor_did            VARCHAR DEFAULT 'did:web:maps.etzhayyim.com:flightradar',
      org_did              VARCHAR DEFAULT 'anon',
      sensitivity_ord      INTEGER DEFAULT 1,
      owner_did            VARCHAR DEFAULT 'did:web:maps.etzhayyim.com',
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_flight_purpose_code ON vertex_flight_purpose (purpose_code)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_flight_serves_purpose (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     VARCHAR,
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR,
      effective_from   VARCHAR,
      effective_to     VARCHAR,
      passenger_count  INTEGER,
      cargo_kg         DOUBLE PRECISION,
      source_url       VARCHAR,
      source_license   VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_flight_serves_purpose_src ON edge_flight_serves_purpose (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_flight_serves_purpose_dst ON edge_flight_serves_purpose (dst_vid)`.execute(db);

  // ── 4. Live snapshot ↔ registered aircraft edge (cheap join) ──────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_aircraft_state_for_aircraft (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     VARCHAR,
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR DEFAULT 'did:web:maps.etzhayyim.com',
      ts_ms            BIGINT
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_state_for_aircraft_src ON edge_aircraft_state_for_aircraft (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_state_for_aircraft_dst ON edge_aircraft_state_for_aircraft (dst_vid)`.execute(db);

  // ── 5. Seed canonical flight purposes (8 codes, ICAO Annex 6 + military) ─
  const purposes: Array<[string, string, string, string]> = [
    ["passenger", "Passenger transport", "旅客輸送", "Scheduled or charter passenger flight (ICAO Annex 6 Part I)"],
    ["cargo", "Cargo transport", "貨物輸送", "Dedicated freight or mail transport"],
    ["military", "Military operation", "軍用機", "State aircraft per Chicago Convention Art. 3"],
    ["medevac", "Medical evacuation", "救急医療搬送", "Emergency or scheduled HEMS / air ambulance"],
    ["training", "Flight training", "訓練", "Type rating / instructional flight"],
    ["test", "Test / ferry", "試験飛行", "Production test, post-maintenance, ferry"],
    ["private", "Private / general aviation", "一般航空", "Non-commercial private operation (Part 91)"],
    ["government", "Government / state", "政府専用", "Head-of-state, customs, law-enforcement, SAR (non-military)"],
  ];

  const createdAt = "2026-05-05T18:30:00Z";
  for (const [code, en, ja, desc] of purposes) {
    const vid = `at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.flightPurpose/${code}`;
    await sql`
      INSERT INTO vertex_flight_purpose (
        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, created_at
      )
      SELECT ${vid}, ${code}, ${en}, ${ja}, ${desc}, 'ICAO Annex 6 + Chicago Convention Art. 3', ${createdAt}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = ${vid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_aircraft_state_for_aircraft`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_flight_serves_purpose`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_flight_purpose`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_aircraft_part_made_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_aircraft_has_part`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_aircraft_part`.execute(db);
  // ALTER ADD COLUMN is reversible via DROP COLUMN, but RW supports it.
  await sql`ALTER TABLE vertex_aircraft DROP COLUMN IF EXISTS purpose_code`.execute(db);
  await sql`ALTER TABLE vertex_aircraft DROP COLUMN IF EXISTS registration_country_iso2`.execute(db);
  await sql`ALTER TABLE vertex_aircraft_track DROP COLUMN IF EXISTS aircraft_did`.execute(db);
  await sql`ALTER TABLE vertex_aircraft_state DROP COLUMN IF EXISTS aircraft_did`.execute(db);
}
