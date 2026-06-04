-- ADR-2605082000 PoC seed (ki) — register the 4 ki tools in vertex_mcp_tool_def.
--
-- Mirror of saikin seed (r_20260509160000); same convention. The ki dispatcher
-- handlers are auto-resolved via mcp_dispatch._DEFAULT_ACTORS = [..., ("ki", [...])].
-- Note: ki has 5 graph nodes (absorb / synthesize / bloom / skip_bloom / ring),
-- but only 4 are tool calls. `skip_bloom` is a constant-return identity node
-- (no I/O, returns {"bloomSkipped": true, "bloomId": null}) and is NOT seeded
-- here — the v2 topology keeps it as py_primitive with lint-py-primitive-ok
-- until a generic `com.etzhayyim.tools.const.echo` MCP tool is introduced.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-absorb',
   0, 0,
   'com.etzhayyim.apps.ki.absorb', 'did:web:ki.etzhayyim.com', 'ki.etzhayyim.com', 'procedure',
   'Absorb a source vertex into ki for vertical synthesis.',
   '{"type":"object","properties":{"sourceVertexId":{"type":"string"},"inputKind":{"type":"string"},"contentSnippet":{"type":"string"}}}',
   '{"type":"object","properties":{"absorbId":{"type":"string"},"status":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/ki/absorb.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-synthesize',
   0, 0,
   'com.etzhayyim.apps.ki.synthesize', 'did:web:ki.etzhayyim.com', 'ki.etzhayyim.com', 'procedure',
   'Synthesize an absorbed input into a structured artifact.',
   '{"type":"object","properties":{"absorbId":{"type":"string"}}}',
   '{"type":"object","properties":{"artifactId":{"type":"string"},"synthesis":{"type":"string"},"confidence":{"type":"number"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/ki/synthesize.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-bloom',
   0, 0,
   'com.etzhayyim.apps.ki.bloom', 'did:web:ki.etzhayyim.com', 'ki.etzhayyim.com', 'procedure',
   'Publish a synthesized artifact (bloom).',
   '{"type":"object","properties":{"artifactId":{"type":"string"}}}',
   '{"type":"object","properties":{"bloomId":{"type":"string"},"publishedAt":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/ki/bloom.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-ring',
   0, 0,
   'com.etzhayyim.apps.ki.ring', 'did:web:ki.etzhayyim.com', 'ki.etzhayyim.com', 'procedure',
   'Snapshot a ring (periodic aggregation marker) at the end of the cycle.',
   '{"type":"object","properties":{"period":{"type":"string"}}}',
   '{"type":"object","properties":{"ringId":{"type":"string"},"snapshotCount":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/ki/ring.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
