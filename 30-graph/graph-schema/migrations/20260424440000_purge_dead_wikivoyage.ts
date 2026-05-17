import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 72 — purge 12 Wikivoyage langs that never produced a row
 * (wv:ar/cs/da/fi/ja/nl/no/pl/ro/sk/tr/uk). Wikivoyage's total geotagged
 * corpus is ~30K articles, heavily skewed to en/de/fr; most minor langs
 * carry <100 geotagged entries. Pruning these reduces frontier noise
 * without losing meaningful coverage.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const deadLangs = [
    "ar", "cs", "da", "fi", "ja", "nl",
    "no", "pl", "ro", "sk", "tr", "uk",
  ];
  for (const lang of deadLangs) {
    await sql`DELETE FROM vertex_maps_coverage_target WHERE source_did = ${`did:web:maps.etzhayyim.com:wikivoyage:${lang}`}`.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: re-seed via original migrations if needed.
}
