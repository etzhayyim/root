/**
 * Update coverage recipes for entity historical enrichment loops.
 *
 * (a) natural_person: infer → ingest (Wikidata SPARQL P31=Q5 handler now live)
 * (b) org_hierarchy: new ingest recipe (GLEIF parent-subsidiary → edge_depends_on)
 * (c) follows_history: new ingest recipe (PDS getFollows backfill → edge_follows)
 *
 * RisingWave compat: upsert via delete-then-insert (no ON CONFLICT support).
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── (a) Upgrade natural_person: infer → ingest ───────────────────────────
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'natural_person' AND authority_kind = 'world'
  `.execute(db);

  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier,
       langgraph_id, world_total, notes, created_at)
    VALUES (
      'natural_person', 'world', 'ingest',
      'https://query.wikidata.org/sparql',
      '',
      '',
      8000000000,
      'Wikidata SPARQL P31=Q5 (human); batch 500/run; skips existing vertex_ids',
      now()
    )
  `.execute(db);

  // ── (b) org_hierarchy: GLEIF parent-subsidiary → edge_depends_on ─────────
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'org_hierarchy' AND authority_kind = 'world'
  `.execute(db);

  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier,
       langgraph_id, world_total, notes, created_at)
    VALUES (
      'org_hierarchy', 'world', 'ingest',
      'https://api.gleif.org/api/v1/lei-records/{lei}/direct-parent-relationship',
      '',
      '',
      5000000,
      'GLEIF direct-parent relationship per LEI → edge_depends_on(dep_type=parent_org)',
      now()
    )
  `.execute(db);

  // ── (c) follows_history: PDS getFollows backfill → edge_follows ───────────
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'follows_history' AND authority_kind = 'world'
  `.execute(db);

  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier,
       langgraph_id, world_total, notes, created_at)
    VALUES (
      'follows_history', 'world', 'ingest',
      'https://atproto.gftd.ai/xrpc/app.bsky.graph.getFollows',
      '',
      '',
      1000000,
      'PDS getFollows per actor DID → edge_follows backfill; ATPROTO_PDS_URL env overrides',
      now()
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Revert natural_person to infer
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain = 'natural_person' AND authority_kind = 'world'
  `.execute(db);

  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier,
       langgraph_id, world_total, notes, created_at)
    VALUES (
      'natural_person', 'world', 'infer',
      '',
      'fast',
      '',
      8000000000,
      'Infer notable persons from Wikidata P31=Q5 (human) -- partial coverage only',
      now()
    )
  `.execute(db);

  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE domain IN ('org_hierarchy', 'follows_history')
      AND authority_kind = 'world'
  `.execute(db);
}
