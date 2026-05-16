import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2605011500 §Phase-1.2 — vessel ↔ legal_entity edges.
//
// Adds two edge tables that link vertex_vessel (NOAA + aisstream) to a legal
// entity identifier. The LEI column is **nullable** because most Wikidata
// shipping companies (the only free, no-key enrichment source we found) have
// not registered an LEI via P5305. When LEI is absent, `wikidata_qid` +
// `entity_label` carry the identity; `dst_vid` is set to either
// `vertex_legal_entity.vertex_id` (LEI hit) or `'wikidata:Q12345'` (QID-only).
//
// tier: B (long-lived ownership relations)
//
// Edges are populated by the aismarine_wikidata_lei.py worker which SPARQL-
// queries Wikidata for ?ship wdt:P458 ?imo ; wdt:P127 ?owner / wdt:P137
// ?operator and resolves owner/operator to (LEI, QID) pairs. Coverage is
// sparse (~hundreds of mappings) but high-quality. Phase 1.3 follow-on:
// Equasis scrape for the remaining ~80% commercial fleet.
//
// No materialised view: a denormalised LEFT JOIN to vertex_legal_entity
// (millions of GLEIF rows) blew the streaming MV state. The Worker handler
// `getVesselDetail` queries edge tables directly + LEFT JOIN to
// vertex_legal_entity bounded by `mmsi=?` (small N).

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS edge_vessel_owned_by (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      mmsi bigint NOT NULL,
      imo bigint,
      lei varchar,
      wikidata_qid varchar,
      entity_label varchar,
      share_pct real,
      effective_from_ms bigint,
      effective_to_ms bigint,
      source varchar NOT NULL,
      source_record_id varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_vessel_operated_by (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      mmsi bigint NOT NULL,
      imo bigint,
      lei varchar,
      wikidata_qid varchar,
      entity_label varchar,
      role varchar,
      effective_from_ms bigint,
      effective_to_ms bigint,
      source varchar NOT NULL,
      source_record_id varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_mmsi ON edge_vessel_owned_by(mmsi)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_lei  ON edge_vessel_owned_by(lei)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_qid  ON edge_vessel_owned_by(wikidata_qid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_mmsi ON edge_vessel_operated_by(mmsi)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_lei  ON edge_vessel_operated_by(lei)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_qid  ON edge_vessel_operated_by(wikidata_qid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_operated_by_qid`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_operated_by_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_operated_by_mmsi`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_owned_by_qid`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_owned_by_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_vessel_owned_by_mmsi`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_vessel_operated_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_vessel_owned_by`.execute(db);
}
