/**
 * Add coverage recipe for business_person_lei enrichment loop.
 *
 * business_person_lei: reads vertex_business_person rows with null registry_id,
 * searches GLEIF API by exact legalName, and UPDATEs registry_id / registry_type='lei'.
 * This is a prerequisite for org_hierarchy (which needs registry_type='lei' rows).
 *
 * world_total = 460 (current vertex_business_person row count; small domain).
 * RisingWave compat: upsert via delete-then-insert (no ON CONFLICT support).
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'business_person_lei' AND authority_kind = 'world'
  `.execute(db);

  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier,
       langgraph_id, world_total, notes, created_at)
    VALUES (
      'business_person_lei', 'world', 'ingest',
      'https://api.gleif.org/api/v1/lei-records',
      '',
      '',
      460,
      'GLEIF legalName search per vertex_business_person.org_name → UPDATE registry_id/registry_type=lei; prerequisite for org_hierarchy',
      now()
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'business_person_lei' AND authority_kind = 'world'
  `.execute(db);
}
