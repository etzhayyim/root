import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0056 follow-up: enrich `vertex_open_defence_event` with typed
 * columns + cross-actor edges so defence events can be joined against
 * legal-entity (LEI), vessel (IMO), CVE, treaty, country, and aircraft
 * graphs without parsing back the BPMN payload.
 *
 * Add typed columns on the existing event table (LEI / IMO / CVE / treaty
 * / country / commodity / military DID) and 4 narrow edge tables
 * (subject→LEI, subject→vessel, event→CVE, event→treaty). All optional —
 * BPMNs continue to write the core required columns and only populate the
 * typed/edge ones when their FEEL has the field.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. Typed columns on existing event table
  const cols: Array<{ name: string; type: string }> = [
    { name: "subject_lei",       type: "varchar" },     // GLEIF LEI 20-char (supplier / target / counterparty)
    { name: "subject_imo",       type: "varchar" },     // IMO 7-digit vessel ID
    { name: "subject_cve_id",    type: "varchar" },     // CVE-YYYY-NNNN
    { name: "subject_country",   type: "varchar" },     // ISO 3166-1 alpha-2 (originator / destination)
    { name: "treaty_code",       type: "varchar" },     // NPT / CTBT / BWC / CWC / OST / TPNW / Wassenaar
    { name: "commodity_code",    type: "varchar" },     // HS / UNSPSC / ECCN / Mofcom-cat
    { name: "aircraft_did",      type: "varchar" },     // tail number / mil callsign
    { name: "satellite_norad_id", type: "varchar" },    // NORAD satellite catalog id
    { name: "evidence_uri",      type: "varchar" },     // public source / OSINT URL
    { name: "fiscal_year",       type: "varchar" },     // YYYY (procurement / FMS)
    { name: "amount_usd",        type: "double precision" }, // normalized USD value (procurement / sanctions)
    { name: "confidence",        type: "double precision" }, // 0.0..1.0 (LLM / analyst)
  ];
  for (const c of cols) {
    await sql`ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS ${sql.raw(c.name)} ${sql.raw(c.type)}`.execute(db);
  }

  // 2. Indexes for the new high-cardinality columns
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_lei      ON vertex_open_defence_event (subject_lei)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_imo      ON vertex_open_defence_event (subject_imo)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_cve      ON vertex_open_defence_event (subject_cve_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_country  ON vertex_open_defence_event (subject_country)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_treaty   ON vertex_open_defence_event (treaty_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_commodity ON vertex_open_defence_event (commodity_code)`.execute(db);

  // 3. Cross-actor edge tables (GraphAr-native, vertex_id↔vertex_id)
  //    Bridges defence events to legal-entity / vessel / vuln / treaty graphs.

  // 3a. defence event → legal-entity (LEI). Drives "who did it" supply-chain joins.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_defence_subject_to_lei (
      edge_id         varchar PRIMARY KEY,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar NOT NULL,
      sensitivity_ord integer NOT NULL,
      org_id          varchar NOT NULL,
      user_id         varchar NOT NULL,
      actor_id        varchar NOT NULL,
      owner_did       varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_lei_src ON edge_defence_subject_to_lei (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_lei_dst ON edge_defence_subject_to_lei (dst_vid)`.execute(db);

  // 3b. defence event → vessel (IMO). Maritime sanctions / dark-fleet / cable tamper.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_defence_subject_to_vessel (
      edge_id         varchar PRIMARY KEY,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar NOT NULL,
      sensitivity_ord integer NOT NULL,
      org_id          varchar NOT NULL,
      user_id         varchar NOT NULL,
      actor_id        varchar NOT NULL,
      owner_did       varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_vessel_src ON edge_defence_subject_to_vessel (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_vessel_dst ON edge_defence_subject_to_vessel (dst_vid)`.execute(db);

  // 3c. defence event → CVE. Cyber-incident / weaponized-CVE / zero-day chain.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_defence_event_to_cve (
      edge_id         varchar PRIMARY KEY,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar NOT NULL,
      sensitivity_ord integer NOT NULL,
      org_id          varchar NOT NULL,
      user_id         varchar NOT NULL,
      actor_id        varchar NOT NULL,
      owner_did       varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_cve_src ON edge_defence_event_to_cve (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_cve_dst ON edge_defence_event_to_cve (dst_vid)`.execute(db);

  // 3d. defence event → treaty/regime (NPT / CTBT / Wassenaar / OST / TPNW / BWC / CWC / MTCR).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_defence_event_to_treaty (
      edge_id         varchar PRIMARY KEY,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar NOT NULL,
      sensitivity_ord integer NOT NULL,
      org_id          varchar NOT NULL,
      user_id         varchar NOT NULL,
      actor_id        varchar NOT NULL,
      owner_did       varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_treaty_src ON edge_defence_event_to_treaty (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_defence_treaty_dst ON edge_defence_event_to_treaty (dst_vid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_defence_event_to_treaty`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_defence_event_to_cve`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_defence_subject_to_vessel`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_defence_subject_to_lei`.execute(db);
  // Typed columns: leave in place. ADR-0056 events that already use them
  // would lose data on rollback; instead drop the table via the parent
  // migration if you really need to revert.
}
