import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase B4 — register `news_translate` external Python UDF.
 *
 * Delegates to `com.etzhayyim.apps.news.translate` on the mitama-udf pool.
 * 3-arg signature: (text, source_lang, target_lang) → translated text.
 *
 * Replaces the RunPod gemma4:26b round-trip in
 * `60-apps/etzhayyim-project-news/appview/news-core-component/src/app.ts`
 * `translateText()` with Vultr Serverless Devstral through the shared
 * `pymagatama.llm` tier abstraction.
 *
 * Use from SQL:
 *   SELECT news_translate(title, lang, 'ja') AS title_ja
 *   FROM vertex_news_article WHERE lang <> 'ja';
 *
 * Streaming MV (future):
 *   CREATE MATERIALIZED VIEW mv_news_article_ja AS
 *   SELECT id, news_translate(title, lang, 'ja') AS title_ja, ...
 *   FROM vertex_news_article WHERE lang <> 'ja';
 *
 * Handler: `20-actors/magatama/py/src/pymagatama/handlers/news_translate.py`.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION news_translate(VARCHAR, VARCHAR, VARCHAR)
      RETURNS VARCHAR
      AS 'com.etzhayyim.apps.news.translate'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS news_translate(VARCHAR, VARCHAR, VARCHAR)`.execute(db);
}
