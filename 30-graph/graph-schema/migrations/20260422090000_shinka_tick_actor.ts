import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase C — register `shinka_tick_actor` external Python UDF.
 *
 * Delegates to `com.etzhayyim.apps.shinka.tickActor` on the mitama-udf pool.
 * The underlying LangGraph traversal lives in
 * `20-actors/magatama/py/src/pymagatama/shinka/__init__.py` and implements
 * the per-DID kyumei-shinka-autonomy rule (90-docs/rules/compliance/).
 *
 * Use from SQL:
 *   SELECT shinka_tick_actor('did:web:yoro.etzhayyim.com') AS result;
 *
 * Scheduled via K8s CronJob every 15 min per registered actor — see
 * `50-infra/vultr/mitama-udf-pool/templates/cronjob-shinka.yaml`.
 *
 * No LANGUAGE clause — `LANGUAGE python` is reserved for embedded UDFs
 * (disabled cluster-wide for security). External UDFs use
 * `AS 'fn_name' USING LINK '...'` only (see 20260421170000 comment).
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION shinka_tick_actor(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.shinka.tickActor'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS shinka_tick_actor(VARCHAR)`.execute(db);
}
