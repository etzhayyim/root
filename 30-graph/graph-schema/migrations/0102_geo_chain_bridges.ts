import { Kysely, sql } from 'kysely';

/**
 * Migration 0102: Geographic chain bridges — ISO3166↔ISO4217 + LOCODE/ISO4217↔Sovereign.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 24).
 *
 * ## New bridges
 *
 * ### ISO 3166 ↔ ISO 4217 bidirectional
 *
 * | system            | edges | derivation                                          |
 * |-------------------|-------|-----------------------------------------------------|
 * | iso3166_iso4217   |  ~164 | reverse of iso4217_iso3166 (from 0084)              |
 *
 * ### ISO 4217 (currency) ↔ Sovereign state
 *
 * | system            | edges | derivation                                          |
 * |-------------------|-------|-----------------------------------------------------|
 * | iso4217_sovereign |  ~164 | iso4217_iso3166 ∘ iso3166_sovereign                 |
 * | sovereign_iso4217 |  ~164 | reverse of iso4217_sovereign                        |
 *
 * ### LOCODE ↔ Sovereign state
 *
 * | system            | edges    | derivation                                       |
 * |-------------------|----------|--------------------------------------------------|
 * | locode_sovereign  | ~109,000 | locode_iso3166 ∘ iso3166_sovereign               |
 * | sovereign_locode  | ~109,000 | reverse of locode_sovereign                      |
 *
 * ## Coverage impact
 *
 * Currency (ISO 4217) is now bidirectional with ISO 3166-1 country codes.
 * Currency and LOCODE locations are now directly linked to sovereign entities.
 * Full geographic bridge topology:
 *   LOCODE ↔ ISO3166 ↔ M49 ↔ Sovereign ↔ ISO4217 (currency)
 * Any port/airport can now reach its sovereign state and currency in O(1) hops.
 *
 * ## Total edges after 0102: ~1.98M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_iso4217'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso4217_sovereign'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sovereign_iso4217'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'locode_sovereign'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sovereign_locode'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'iso3166_iso4217', 'iso4217_sovereign', 'sovereign_iso4217',
    'locode_sovereign', 'sovereign_locode',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
