DELETE FROM vertex_coverage_recipe
    WHERE domain = 'business_person_lei' AND authority_kind = 'world';

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
    );
