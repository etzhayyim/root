import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: C
// gov_repo_record_allowlist_cleanup: removes vertex_repo_record from gov BPMN allowlists.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = REPLACE(write_table_allowlist, ',vertex_repo_record', '')
    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')
      AND write_table_allowlist LIKE '%,vertex_repo_record%'
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = REPLACE(write_table_allowlist, 'vertex_repo_record,', '')
    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')
      AND write_table_allowlist LIKE '%vertex_repo_record,%'
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = ''
    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')
      AND write_table_allowlist = 'vertex_repo_record'
  `.execute(db);

  for (const table of ["vertex_gov_org", "vertex_gov_actor_manifest", "edge_gov_org_site_dependency"]) {
    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET write_table_allowlist =
        CASE
          WHEN COALESCE(write_table_allowlist, '') = '' THEN ${table}
          ELSE write_table_allowlist || ',' || ${table}
        END
      WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')
        AND COALESCE(write_table_allowlist, '') NOT LIKE ${`%${table}%`}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist =
      CASE
        WHEN write_table_allowlist LIKE '%vertex_repo_record%' THEN write_table_allowlist
        ELSE write_table_allowlist || ',vertex_repo_record'
      END
    WHERE actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%'
  `.execute(db);
}
