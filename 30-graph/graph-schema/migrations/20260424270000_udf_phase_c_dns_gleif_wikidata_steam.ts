import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase C — register the 5 per-row External Python UDFs added
 * for the ingest-scripts-bpmn-consolidation (deps.toml [[migrations]]
 * id=ingest-scripts-bpmn-consolidation-phase1).
 *
 * All handlers live in pymagatama:0.2.32+ and are served from the
 * shared arrow-flight pool at udf-cluster.mitama-udf.svc:8815 — same
 * endpoint the other Phase B UDFs use (see 20260422060000 for the
 * canonical pattern). Each takes VARCHAR input(s) and returns a
 * JSON-stringified VARCHAR that callers unpack via `::jsonb`.
 *
 * Mapped to the legacy scripts they replace (_archive/70-tools/scripts/
 * 260424-udf-migrated/):
 *
 *   dns_resolve / dns_resolve_json   → hourly_collect.py + collect-dns-global.sh
 *   gleif_lei_lookup                 → gleif-reconcile-repo-record.mjs + multi-country-direct-ingest.mjs
 *   wikidata_entity_claims           → media_gamers_enrich_sources.py (wikidata leg)
 *   steam_release_date               → media_gamers_backfill_release_year.py + media_gamers_enrich_sources.py --steam-backfill
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION dns_resolve(VARCHAR, VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.dns.resolve'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION dns_resolve_json(VARCHAR, VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.dns.resolveJson'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION gleif_lei_lookup(VARCHAR, VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.gleif.lookup'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION wikidata_entity_claims(VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.wikidata.entityClaims'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION steam_release_date(VARCHAR)
      RETURNS VARCHAR
      AS 'ai.gftd.apps.steam.releaseDate'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS steam_release_date(VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS wikidata_entity_claims(VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS gleif_lei_lookup(VARCHAR, VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS dns_resolve_json(VARCHAR, VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS dns_resolve(VARCHAR, VARCHAR)`.execute(db);
}
