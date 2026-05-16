DELETE FROM vertex_coverage_recipe
    WHERE domain = 'natural_person' AND authority_kind = 'world';

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
    );

DELETE FROM vertex_coverage_recipe
    WHERE domain = 'org_hierarchy' AND authority_kind = 'world';

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
    );

DELETE FROM vertex_coverage_recipe
    WHERE domain = 'follows_history' AND authority_kind = 'world';

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
    );
