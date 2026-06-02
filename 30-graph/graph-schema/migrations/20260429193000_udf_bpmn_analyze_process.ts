import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Register Optimize-free BPMN process mining UDF.
 *
 * `com.etzhayyim.apps.bpmn.analyzeProcess` reads OCEL-compatible
 * `vertex_repo_commit` audit rows and returns deterministic process KPIs plus
 * optional LLM diagnosis. It deliberately avoids Camunda Optimize/Operate
 * runtime dependencies.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION bpmn_analyze_process(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.bpmn.analyzeProcess'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS bpmn_analyze_process(VARCHAR)`.execute(db);
}
