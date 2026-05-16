DELETE FROM vertex_coverage_recipe
    WHERE domain = 'natural_person' AND authority_kind = 'world';

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
    );

DELETE FROM vertex_coverage_recipe
    WHERE domain IN ('org_hierarchy', 'follows_history')
      AND authority_kind = 'world';
