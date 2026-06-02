import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0032 / ADR-0050 — register `classify_t3_phishing` external Python UDF.
 *
 * Gray-zone phishing classifier sitting on top of the existing
 * `classify_t1` SQL UDF (see 20260421160000). The Python handler only
 * contacts Vultr Serverless Inference when the caller's t1Score falls
 * in the 60..84 band; outside that range it returns `{"skipped": true, ...}`
 * without an HTTP call, so the LLM cost stays bounded.
 *
 * Expected INSERT pattern (thin-Worker, ADR-0036 amendment):
 *
 *   INSERT INTO vertex_gmail_phishing_alert (..., llm_score, verdict, rationale, ...)
 *   SELECT
 *     ...,
 *     classify_t3_phishing(JSON_BUILD_OBJECT(
 *       't1Score', classify_t1(spf, dkim, dmarc, reply_to, from_addr, subject, body_urls_json),
 *       'fromAddr', from_addr,
 *       'subject',  subject,
 *       'replyTo',  reply_to,
 *       'spf', spf, 'dkim', dkim, 'dmarc', dmarc,
 *       'bodyUrls', body_urls_json::jsonb
 *     )::varchar) AS verdict_json,
 *     ...
 *
 * Caller parses `verdict_json` (JSON varchar) to extract llmScore /
 * verdict / rationale. T1 score threshold for gray-zone gating is inside
 * the Python handler (`_GRAY_LOW=60`, `_GRAY_HIGH=85`).
 *
 * Handler source: `20-actors/magatama/py/src/pymagatama/handlers/classify_t3.py`.
 *
 * No LANGUAGE clause — external UDFs use `AS 'nsid' USING LINK '...'` only.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION classify_t3_phishing(VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.yabaiClassifier.phishingT3'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS classify_t3_phishing(VARCHAR)`.execute(db);
}
