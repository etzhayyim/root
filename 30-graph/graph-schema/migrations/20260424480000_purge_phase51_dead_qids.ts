import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 77 — purge 5 Phase 51 WD QIDs that never produced a row.
 * parliamentBldg (Q35798) / aquariumWd (Q1469) / prisonWd (Q40357) /
 * boardingSchool (Q376199) / gurdwara (Q1174356). These are too abstract
 * or too sparsely coordinated in Wikidata to yield on bbox-rotated
 * SPARQL picks. Deleting reduces advance-pick noise.
 *
 * If data ever becomes meaningful (e.g. Wikidata bulk upload of
 * properties), re-seed with a fresh migration.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const deadSourceDids = [
    "did:web:maps.gftd.ai:registry:wikidata:parliamentBldg",
    "did:web:maps.gftd.ai:registry:wikidata:aquariumWd",
    "did:web:maps.gftd.ai:registry:wikidata:prisonWd",
    "did:web:maps.gftd.ai:registry:wikidata:boardingSchool",
    "did:web:maps.gftd.ai:registry:wikidata:gurdwara",
  ];
  for (const sd of deadSourceDids) {
    await sql`DELETE FROM vertex_maps_coverage_target WHERE source_did = ${sd}`.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: re-seed via 20260424330000 if rolling back.
}
