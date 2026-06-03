import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0074 alignment for yadoya + resource-flow phase 1-10 tables.
// tier: B (yadoya); A (resource-flow cluster projection)
//
// ADR-0074 (active 2026-04-26, 2026-04-27 operational correction) makes
// `did:erc725:etzhayyim:260425:<contract>` the canonical actor vector key for
// RisingWave projections. `did:web:*.etzhayyim.com` may stay as facade lookup
// input + profile/display key, but it must NOT be the only key on
// canonical actor projections. This migration adds the same column set
// that `20260426233000_erc725_root_identity_projection.ts` added to
// vertex_etzhayyim_identity / vertex_claim_stake / vertex_claim_challenge
// to the yadoya + resource-flow tables shipped during the 2026-04-28
// hospitality bootstrap.
//
// Columns are nullable. Backfill is performed by
// `30-graph/graph-schema/scripts/migrate-rw-erc725-root.mjs --did
// did:web:yadoya.etzhayyim.com` (and resource-flow) once the corresponding
// `etzhayyimRootIdentity` contracts are deployed and registered in
// `etzhayyimRootIdentityRegistry`. Until then, callers continue to use
// the facade DID columns and observe NULL on the root columns.

const TABLES = [
  // yadoya phase 1-2 (20260428120000)
  "vertex_yadoya_hotel",
  "vertex_yadoya_reservation",
  // yadoya phase 9 (20260428150000)
  "vertex_yadoya_flow_event",
  // resource-flow phase 10 (20260428160000)
  "vertex_resource_flow_currency",
  "vertex_resource_flow_service",
  "vertex_resource_flow_personnel",
];

const COUNTERPARTY_TABLES = [
  // tables where counterparty_did is a canonical key, not just a label
  "vertex_yadoya_flow_event",
  "vertex_resource_flow_currency",
  "vertex_resource_flow_service",
  "vertex_resource_flow_personnel",
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const t of TABLES) {
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN root_did             VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN root_did_hash        VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN root_identity_addr   VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN facade_did           VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN facade_did_hash      VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN identity_method      VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN migration_status     VARCHAR`.execute(db);
  }
  for (const t of COUNTERPARTY_TABLES) {
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN counterparty_root_did      VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} ADD COLUMN counterparty_root_did_hash VARCHAR`.execute(db);
  }
  await sql`FLUSH`.execute(db);

  // Indexes on the canonical actor vector key. Facade hash index is
  // additionally created for the 4 flow-projection tables because the
  // sankey AppView often filters by facade DID (display layer).
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_yadoya_hotel_root_hash         ON vertex_yadoya_hotel (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_yadoya_reservation_root_hash   ON vertex_yadoya_reservation (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_yadoya_flow_event_root_hash    ON vertex_yadoya_flow_event (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_yadoya_flow_event_cp_root_hash ON vertex_yadoya_flow_event (counterparty_root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_currency_root_hash    ON vertex_resource_flow_currency (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_currency_cp_root_hash ON vertex_resource_flow_currency (counterparty_root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_service_root_hash     ON vertex_resource_flow_service (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_service_cp_root_hash  ON vertex_resource_flow_service (counterparty_root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_personnel_root_hash    ON vertex_resource_flow_personnel (root_did_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_resource_flow_personnel_cp_root_hash ON vertex_resource_flow_personnel (counterparty_root_did_hash)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_personnel_cp_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_personnel_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_service_cp_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_service_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_currency_cp_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_resource_flow_currency_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_yadoya_flow_event_cp_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_yadoya_flow_event_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_yadoya_reservation_root_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_yadoya_hotel_root_hash`.execute(db);

  const COUNTERPARTY_DROP = [...COUNTERPARTY_TABLES].reverse();
  for (const t of COUNTERPARTY_DROP) {
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN counterparty_root_did_hash`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN counterparty_root_did`.execute(db);
  }
  const TABLES_DROP = [...TABLES].reverse();
  for (const t of TABLES_DROP) {
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN migration_status`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN identity_method`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN facade_did_hash`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN facade_did`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN root_identity_addr`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN root_did_hash`.execute(db);
    await sql`ALTER TABLE ${sql.raw(t)} DROP COLUMN root_did`.execute(db);
  }
  await sql`FLUSH`.execute(db);
}
