import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0032 / ADR-0050 — add LLM-verdict columns to vertex_gmail_phishing_alert.
 *
 * Extends the existing phishing alert projection with the T3 gray-zone
 * classifier output. The gmail Worker now runs `classify_t1` (SQL UDF,
 * plan-time inline) AND `classify_t3_phishing` (Python UDF → Vultr
 * Serverless Inference) in a single INSERT..SELECT; these columns hold
 * the T3 result when the T1 score is in the 60..84 gray zone, or NULL
 * otherwise (short-circuit).
 *
 * - llm_score:     0-100 integer estimate from the LLM, independent of T1.
 * - llm_verdict:   "phishing" | "legitimate" | "ambiguous" (enum not used —
 *                  VARCHAR keeps future verdict values additive).
 * - llm_rationale: <=300 chars natural-language explanation.
 *
 * NULL discrimination:
 *   - t1_score < 60  → classifier skipped, no LLM call, llm_* = NULL
 *   - 60 <= t1 < 85  → LLM called, llm_* populated (or error string on upstream fail)
 *   - t1_score >= 85 → T1 already confident, llm_* = NULL (cost gate)
 *
 * See `60-apps/etzhayyim-project-gmail/appview/etzhayyim-wasm-gmail-gm4il0x1/src/app.ts`
 * writePhishingAlertViaUdf for the INSERT site.
 */

// RisingWave only accepts one column per ALTER TABLE (tested 2026-04-22 on
// RW 2.8.1). Each ADD/DROP lives in its own statement. PG-standard multi-
// column ADD parses fine in vanilla Postgres but fails with
// `sql parser error: expected end of statement, found: ,` against RW.
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_score INTEGER`.execute(db);
  await sql`ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_verdict VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_rationale VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_rationale`.execute(db);
  await sql`ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_verdict`.execute(db);
  await sql`ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_score`.execute(db);
}
