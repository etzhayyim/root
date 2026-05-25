import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0049 Phase B5 — register `mangaka_storyboard_from_prompt` external UDF.
 *
 * Turns a one-line story premise + layout hints into a structured
 * storyboard (pages × panels × shot/description/dialogue/sfx) via
 * `pymagatama.llm.call_tier_json` → Vultr Serverless Devstral.
 *
 * Use from SQL:
 *   SELECT mangaka_storyboard_from_prompt(
 *     '{"story":"a schoolgirl discovers a sentient library",
 *       "pageCount":3,"panelsPerPage":4,"style":"shonen"}'
 *   ) AS result;
 *
 * Handler: `20-actors/magatama/py/src/pymagatama/handlers/mangaka_storyboard.py`.
 *
 * The UDF does not write to `vertex_mangaka`. The mangaka Worker is
 * responsible for materializing the returned pages/panels into rows
 * with correct parent_rkey / page_number / panel_number.
 */

const UDF_LINK = "http://udf-cluster.mitama-udf.svc:8815";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION mangaka_storyboard_from_prompt(VARCHAR)
      RETURNS VARCHAR
      AS 'app.etzhayyim.apps.mangaka.storyboardFromPrompt'
      USING LINK ${sql.lit(UDF_LINK)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS mangaka_storyboard_from_prompt(VARCHAR)`.execute(db);
}
