import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Register deterministic topology dependency hint UDF.
 *
 * The resident intel topology worker owns the full graph scan and Kahn sort.
 * This UDF keeps the edge-table classification rule available inside
 * RisingWave for ad-hoc SQL, validation views, and future streaming prefilters.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION topology_dependency_hint(VARCHAR, VARCHAR, VARCHAR, VARCHAR)
      RETURNS VARCHAR
      AS 'topology_dependency_hint'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS topology_dependency_hint(VARCHAR, VARCHAR, VARCHAR, VARCHAR)`.execute(db);
}
