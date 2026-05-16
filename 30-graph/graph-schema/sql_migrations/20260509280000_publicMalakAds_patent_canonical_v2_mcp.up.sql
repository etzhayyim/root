-- ADR-2605082000 Phase A — publicMalakAds + patent canonical batch.
--
-- bulk-51 specs:
--   public_malak_crawl_ads:    queue_seed_runs → process_queue → END  (2 nodes)
--   patent_ingest_uspto_weekly: ingest_patent → ingest_citation → END (2 nodes)
--
-- The canonical actors register more tools than the bulk-51 assistant uses
-- (5 publicMalakAds, 3 patent) — shelf-stocking pattern from agentEconomy
-- (iter29) so future flows can compose them via data INSERT only.

-- publicMalakAds: 5 tools (only 2 are nodes in v2)
INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:public-malak-ads.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-publicMalakAds-queueSeedRuns',
   0, 0, 'ai.gftd.apps.publicMalakAds.queueSeedRuns', 'did:web:public-malak-ads.gftd.ai', 'public-malak-ads.gftd.ai', 'procedure',
   'Queue public malak ads seed crawl runs.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/publicMalakAds/queueSeedRuns.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:public-malak-ads.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-publicMalakAds-processQueue',
   0, 0, 'ai.gftd.apps.publicMalakAds.processQueue', 'did:web:public-malak-ads.gftd.ai', 'public-malak-ads.gftd.ai', 'procedure',
   'Process the public malak ads crawl queue.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/publicMalakAds/processQueue.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:public-malak-ads.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-publicMalakAds-analyzeCreative',
   0, 0, 'ai.gftd.apps.publicMalakAds.analyzeCreative', 'did:web:public-malak-ads.gftd.ai', 'public-malak-ads.gftd.ai', 'procedure',
   'Analyze a single creative.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/publicMalakAds/analyzeCreative.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:public-malak-ads.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-publicMalakAds-analyzeRecent',
   0, 0, 'ai.gftd.apps.publicMalakAds.analyzeRecent', 'did:web:public-malak-ads.gftd.ai', 'public-malak-ads.gftd.ai', 'procedure',
   'Analyze recent creatives in a time window.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/publicMalakAds/analyzeRecent.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:public-malak-ads.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-publicMalakAds-clusterRecent',
   0, 0, 'ai.gftd.apps.publicMalakAds.clusterRecent', 'did:web:public-malak-ads.gftd.ai', 'public-malak-ads.gftd.ai', 'procedure',
   'Cluster recent creatives by similarity.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/publicMalakAds/clusterRecent.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

-- patent: 3 tools (2 are nodes in v2)
INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:patent.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-patent-usptoPatentsviewIngestPatent',
   0, 0, 'ai.gftd.apps.patent.usptoPatentsviewIngestPatent', 'did:web:patent.gftd.ai', 'patent.gftd.ai', 'procedure',
   'Ingest USPTO PatentsView weekly patent rows.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/patent/usptoPatentsviewIngestPatent.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:patent.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-patent-usptoPatentsviewIngestCitation',
   0, 0, 'ai.gftd.apps.patent.usptoPatentsviewIngestCitation', 'did:web:patent.gftd.ai', 'patent.gftd.ai', 'procedure',
   'Ingest USPTO PatentsView weekly citation rows.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/patent/usptoPatentsviewIngestCitation.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:patent.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-patent-epoOpsFillCitations',
   0, 0, 'ai.gftd.apps.patent.epoOpsFillCitations', 'did:web:patent.gftd.ai', 'patent.gftd.ai', 'procedure',
   'Fill citations from EPO OPS where USPTO data is incomplete.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/ai/gftd/apps/patent/epoOpsFillCitations.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('public_malak_crawl_ads.v2', 0, 0, 'public_malak_crawl_ads.v2', 2, 'topology', NULL,
   '{"state_keys":["queueOut","processOut","ok","error"],"entry":"queue_seed_runs","edges":[{"from":"queue_seed_runs","to":"process_queue"},{"from":"process_queue","to":"END"}]}',
   'public malak ads crawl (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.public-malak-ads.gftd.ai'),
  ('patent_ingest_uspto_weekly.v2', 0, 0, 'patent_ingest_uspto_weekly.v2', 2, 'topology', NULL,
   '{"state_keys":["patentOut","citationOut","ok","error"],"entry":"ingest_patent","edges":[{"from":"ingest_patent","to":"ingest_citation"},{"from":"ingest_citation","to":"END"}]}',
   'patent USPTO weekly ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.patent.gftd.ai');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('public_malak_crawl_ads.v2:queue_seed_runs', 0, 0, 'public_malak_crawl_ads.v2', 'queue_seed_runs',
   'mcp_tool', 'mcp://ai.gftd.apps.publicMalakAds.queueSeedRuns',
   '{"input_keys":[],"result_key":"queueOut","args":{"name":"ai.gftd.apps.publicMalakAds.queueSeedRuns"}}',
   '2026-05-09T00:00:00Z'),
  ('public_malak_crawl_ads.v2:process_queue', 0, 0, 'public_malak_crawl_ads.v2', 'process_queue',
   'mcp_tool', 'mcp://ai.gftd.apps.publicMalakAds.processQueue',
   '{"input_keys":[],"result_key":"processOut","args":{"name":"ai.gftd.apps.publicMalakAds.processQueue"}}',
   '2026-05-09T00:00:00Z'),
  ('patent_ingest_uspto_weekly.v2:ingest_patent', 0, 0, 'patent_ingest_uspto_weekly.v2', 'ingest_patent',
   'mcp_tool', 'mcp://ai.gftd.apps.patent.usptoPatentsviewIngestPatent',
   '{"input_keys":["maxRows"],"result_key":"patentOut","args":{"name":"ai.gftd.apps.patent.usptoPatentsviewIngestPatent"}}',
   '2026-05-09T00:00:00Z'),
  ('patent_ingest_uspto_weekly.v2:ingest_citation', 0, 0, 'patent_ingest_uspto_weekly.v2', 'ingest_citation',
   'mcp_tool', 'mcp://ai.gftd.apps.patent.usptoPatentsviewIngestCitation',
   '{"input_keys":["maxRows"],"result_key":"citationOut","args":{"name":"ai.gftd.apps.patent.usptoPatentsviewIngestCitation"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'public_malak_crawl_ads.v2'
 WHERE assistant_id = 'public_malak_crawl_ads';
UPDATE vertex_langgraph_assistant SET superseded_by = 'patent_ingest_uspto_weekly.v2'
 WHERE assistant_id = 'patent_ingest_uspto_weekly';

FLUSH;
