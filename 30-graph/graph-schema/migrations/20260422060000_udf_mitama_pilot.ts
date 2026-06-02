import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase B pilot — register 4 mitama UDF entrypoints on RisingWave.
 *
 * Each function maps to a Python handler served by the shared arrow-flight
 * pool (`mitama-udf` namespace, Service `udf-cluster:8815`). RW routes via
 * in-cluster DNS → pymagatama UdfServer → handler executes inside the pod
 * → returns JSON-encoded VARCHAR.
 *
 * Critical syntax note (learned from 20260421170000):
 * External Python UDFs must use `AS 'fn_name' USING LINK 'http://...'` with
 * NO `LANGUAGE` clause. `LANGUAGE python` is reserved for embedded Python
 * UDFs which are disabled cluster-level for security.
 *
 * All handlers take a single JSON-stringified input and return a
 * JSON-stringified output. Callers unpack via `::jsonb` + `jsonb_extract_path_text`.
 *
 * Service path: `http://udf-cluster.mitama-udf.svc:8815` (resolvable from
 * RW compute pod via in-cluster DNS; .cluster.local suffix optional).
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION bpmn_compile_json_to_xml(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.bpmn.compileJsonToXml'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION bpmn_validate_xml(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.bpmn.validateXml'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION playwright_session_open(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.playwright.sessionOpen'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);

  await sql`
    CREATE FUNCTION playwright_session_close(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.playwright.sessionClose'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS playwright_session_close(VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS playwright_session_open(VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS bpmn_validate_xml(VARCHAR)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS bpmn_compile_json_to_xml(VARCHAR)`.execute(db);
}
