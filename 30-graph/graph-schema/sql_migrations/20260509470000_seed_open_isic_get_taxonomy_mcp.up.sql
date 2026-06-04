-- Register com.etzhayyim.apps.openIsic.getTaxonomy MCP primitive.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-openisic-gettaxonomy',
   0, 0, 'com.etzhayyim.apps.openIsic.getTaxonomy', 'did:web:open-isic.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Retrieve ISIC taxonomy hierarchy (section, division, group, class) dynamically.',
   '{"type":"object","properties":{"level":{"type":"string","enum":["section","division","group","class"]},"parentCode":{"type":"string"}},"required":["level"]}',
   '{"type":"object"}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/openisic/getTaxonomy.json',
   'anon', 'anon', '', '2026-05-14T00:00:00Z');

FLUSH;
