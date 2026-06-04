-- Register com.etzhayyim.apps.openIsicA.* MCP primitives.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-openisica-classifycrop',
   0, 0, 'com.etzhayyim.apps.openIsicA.classifyCrop', 'did:web:open-isic.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Classify crop production entities (ISIC 011-013).',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"isicClassCode":{"type":"string"},"entityDid":{"type":"string"}},"required":["vertexId","isicClassCode","entityDid"]}',
   '{"type":"object"}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/openisica/classifyCrop.json',
   'anon', 'anon', '', '2026-05-14T00:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-openisica-classifylivestock',
   0, 0, 'com.etzhayyim.apps.openIsicA.classifyLivestock', 'did:web:open-isic.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Classify animal production entities (ISIC 014).',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"isicClassCode":{"type":"string"},"entityDid":{"type":"string"}},"required":["vertexId","isicClassCode","entityDid"]}',
   '{"type":"object"}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/openisica/classifyLivestock.json',
   'anon', 'anon', '', '2026-05-14T00:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-openisica-classifyforestry',
   0, 0, 'com.etzhayyim.apps.openIsicA.classifyForestry', 'did:web:open-isic.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Classify forestry and logging entities (ISIC 02).',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"isicClassCode":{"type":"string"},"entityDid":{"type":"string"}},"required":["vertexId","isicClassCode","entityDid"]}',
   '{"type":"object"}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/openisica/classifyForestry.json',
   'anon', 'anon', '', '2026-05-14T00:00:00Z'),

  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-openisica-classifyfishing',
   0, 0, 'com.etzhayyim.apps.openIsicA.classifyFishing', 'did:web:open-isic.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Classify fishing and aquaculture entities (ISIC 03).',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"isicClassCode":{"type":"string"},"entityDid":{"type":"string"}},"required":["vertexId","isicClassCode","entityDid"]}',
   '{"type":"object"}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/openisica/classifyFishing.json',
   'anon', 'anon', '', '2026-05-14T00:00:00Z');

FLUSH;
