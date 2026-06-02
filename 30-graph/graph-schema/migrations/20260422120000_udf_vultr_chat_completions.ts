import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0050 — register `vultr_chat_completions` external Python UDF.
 *
 * Delegates to `com.etzhayyim.apps.vultrInference.chatCompletions` on the
 * mitama-udf pool. The handler wraps `api.vultrinference.com/v1/chat/completions`
 * (OpenAI-compatible) behind a SQL function so streaming MVs can enrich
 * rows with LLM output in the RisingWave dataflow.
 *
 * Inference stays entirely on Vultr: mitama-udf pod (VKE LAX) →
 * api.vultrinference.com (same provider, Bandwidth Alliance internal).
 * No CF Worker hop.
 *
 * Use from SQL:
 *   SELECT vultr_chat_completions(
 *     '{"model":"Qwen/Qwen3.5-397B-A17B-FP8",
 *       "messages":[{"role":"user","content":"say hi"}],
 *       "maxTokens":20}'
 *   ) AS result;
 *
 * Handler source: `20-actors/magatama/py/src/pymagatama/handlers/vultr_inference.py`.
 *
 * No LANGUAGE clause — `LANGUAGE python` is reserved for embedded UDFs
 * (disabled cluster-wide for security). External UDFs use
 * `AS 'nsid' USING LINK '...'` only.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION vultr_chat_completions(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.vultrInference.chatCompletions'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS vultr_chat_completions(VARCHAR)`.execute(db);
}
