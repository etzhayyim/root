-- Seed: LangChain × LangGraph × Pregel feature audit (2026-05-09).
-- Source: in-repo survey performed via Claude Code agent.
-- Owning entity: did:web:amanomibashira.etzhayyim.com (operating entity per CLAUDE.md).
-- Doc: 90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md
--      + 90-docs/adr/2605072000-langgraph-agent-loop-pattern.md

-- Analysis header
INSERT INTO vertex_codebase_analysis (
  vertex_id, slug, title, scope, ecosystem,
  performed_by_did, performed_at, summary, doc_uri,
  created_at, sensitivity_ord, owner_did
) VALUES (
  'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509',
  'langchain-langgraph-pregel-20260509',
  'LangChain × LangGraph × Pregel survey + Shannon/von-Neumann optimization plan',
  'repo:etzhayyimcojp/etzhayyim-apps-etzhayyimcojp',
  'langchain+langgraph',
  'did:web:amanomibashira.etzhayyim.com',
  '2026-05-09T00:00:00Z',
  'LangGraph used as intra-job state machine (Pregel/BSP). LangChain minimal (ChatAnthropic only). Custom RW-native BaseCheckpointSaver + BaseStore. Optimization plan grounded in Shannon (prompt cache, content-hash dedup, delta channels) and von Neumann (stored-program graphs, minimax judge). Pregel features (Send / Subgraph / Streaming / Interrupt) underused.',
  'https://github.com/etzhayyimcojp/etzhayyim-apps-etzhayyimcojp#langchain-langgraph-survey',
  now()::varchar,
  100,
  'did:web:amanomibashira.etzhayyim.com'
);

-- Feature catalog (ecosystem × package × feature_name).
INSERT INTO vertex_codebase_feature (
  vertex_id, ecosystem, package, feature_name, feature_kind, description, upstream_url, created_at, sensitivity_ord, owner_did
) VALUES
  ('feature/langgraph/graph/StateGraph','langgraph','langgraph.graph','StateGraph','class','Vertex-centric state machine (Pregel BSP).','https://langchain-ai.github.io/langgraph/',now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/graph/MessageGraph','langgraph','langgraph.graph','MessageGraph','class','Message-channel graph variant.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/graph.message/add_messages','langgraph','langgraph.graph.message','add_messages','function','Reducer for accumulating chat messages.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/graph/conditional_edges','langgraph','langgraph.graph','add_conditional_edges','function','Branching control flow.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/graph/start_end','langgraph','langgraph.graph','START_END','pattern','START / END sentinels.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/pregel/Send','langgraph','langgraph.types','Send','function','Pregel dynamic fan-out for map-reduce / cohort parallelism.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/graph/Subgraph','langgraph','langgraph.graph','subgraph','pattern','Nested / reusable graphs.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/runtime/streaming','langgraph','langgraph','astream_events_v2','function','Token / event streaming over SSE.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/runtime/interrupt','langgraph','langgraph.types','interrupt','function','Human-in-the-loop checkpoint pause/resume.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/checkpoint/BaseCheckpointSaver','langgraph','langgraph.checkpoint.base','BaseCheckpointSaver','class','Abstract checkpoint persistence.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/store/BaseStore','langgraph','langgraph.store.base','BaseStore','class','Cross-thread memory store.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/prebuilt/create_react_agent','langgraph','langgraph.prebuilt','create_react_agent','function','Prebuilt ReAct loop.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/functional/entrypoint_task','langgraph','langgraph.func','entrypoint_task','pattern','Functional API for linear pipelines.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langgraph/runtime/checkpointer_none','langgraph','langgraph','checkpointer_none','pattern','Intra-job graphs with durability owned by Zeebe.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain_anthropic/ChatAnthropic','langchain','langchain_anthropic','ChatAnthropic','class','Anthropic chat model adapter.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain_core/runnables/RunnableConfig','langchain','langchain_core.runnables','RunnableConfig','class','Config object for runnables.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/prompts/PromptTemplate','langchain','langchain.prompts','PromptTemplate','class','Prompt templating.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/tools/Tool','langchain','langchain.tools','Tool','class','Tool abstraction for LLM function calling.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/agents/AgentExecutor','langchain','langchain.agents','AgentExecutor','class','Agent runtime.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/parsers/OutputParser','langchain','langchain.output_parsers','OutputParser','class','Structured output parsing.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/retrievers/Retriever','langchain','langchain.retrievers','Retriever','class','Retrieval abstraction.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/loaders/DocumentLoader','langchain','langchain.document_loaders','DocumentLoader','class','Document ingestion adapters.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/runnables/LCEL','langchain','langchain_core.runnables','LCEL','pattern','Runnable composition language.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/callbacks/Callback','langchain','langchain_core.callbacks','BaseCallbackHandler','class','Callback / tracing hooks.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/langchain/memory/Memory','langchain','langchain.memory','Memory','class','Conversation memory abstraction.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/anthropic/prompt_caching','langchain','langchain_anthropic','prompt_caching','pattern','cache_control=ephemeral for system-prompt cache.','https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching',now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/internal/RisingWaveCheckpointSaver','internal','pymagatama','RisingWaveCheckpointSaver','class','RW-native BaseCheckpointSaver impl.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/internal/RisingWaveStore','internal','pymagatama','RisingWaveStore','class','RW-native BaseStore impl.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/internal/langgraph_registry','internal','pymagatama.primitives','langgraph_registry','module','Module-level graph registration.',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com'),
  ('feature/internal/resolve_model_id','internal','magatama-host-sdk','resolveModelId','function','LLM Model SSoT resolver (CRITICAL).',NULL,now()::varchar,0,'did:web:amanomibashira.etzhayyim.com');

-- Per-feature usage rows. Composite vertex_id keeps PK unique under multi-analysis use.
INSERT INTO vertex_codebase_feature_usage (
  vertex_id, analysis_vertex_id, feature_vertex_id, status, layer, priority, role,
  occurrence_count, file_paths, evidence_note, replaced_by_feature_id,
  created_at, sensitivity_ord, owner_did
) VALUES
  ('usage/langchain-langgraph-pregel-20260509/StateGraph','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph/StateGraph','used','L3-runtime',NULL,'core intra-job state machine',68,'20-actors/magatama/py/src/pymagatama/*_worker_main.py','50+ workers, all use StateGraph + compile().',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/MessageGraph','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph/MessageGraph','not_used','L3-runtime','P3','superseded by StateGraph',0,NULL,'No occurrences — StateGraph + add_messages reducer covers the use case.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/add_messages','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph.message/add_messages','used','L3-runtime',NULL,'message channel reducer',5,'compintel_worker_main.py;outreach_worker_main.py;newsletter_worker_main.py;webmk_worker_main.py;contentengine_worker_main.py','Annotated[..., add_messages] pattern.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/conditional_edges','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph/conditional_edges','used','L3-runtime',NULL,'quality gate / branching',10,'newsletter_worker_main.py;contentengine_worker_main.py','quality_gate routing in worker graphs.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/start_end','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph/start_end','used','L3-runtime',NULL,'graph control flow',50,'20-actors/magatama/py/src/pymagatama/*_worker_main.py','Standard pattern.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Send','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/pregel/Send','not_used','L3-runtime','P1','cohort/batch fan-out (Pregel super-step parallelism)',0,NULL,'Currently for-loop sequential; Send unlocks N-way parallel barriers.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Subgraph','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/graph/Subgraph','not_used','L3-runtime','P1','reusable sense/plan/act/reflect actors',0,NULL,'Single-level only. ADR-2605080000 6-layer would map naturally to subgraphs.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/streaming','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/runtime/streaming','partial','L3-runtime','P1','SSE / token streaming to L1',0,'20-actors/magatama/py/src/pymagatama/langgraph_server_app.py','/runs/stream endpoint planned (Phase 3); not implemented yet.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/interrupt','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/runtime/interrupt','planned','L3-runtime','P3','HITL replacement for BPMN message-event correlation',0,NULL,'ADR-2605080600 Phase 4+ candidate.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/BaseCheckpointSaver','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/checkpoint/BaseCheckpointSaver','used','persistence',NULL,'extended via RisingWaveCheckpointSaver',1,'20-actors/magatama/py/src/pymagatama/langgraph_checkpoint_rw.py','RW-native subclass. RW constraints (no SKIP LOCKED / no LISTEN/NOTIFY / no ON CONFLICT) handled.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/BaseStore','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/store/BaseStore','used','persistence',NULL,'extended via RisingWaveStore',1,'20-actors/magatama/py/src/pymagatama/langgraph_store_rw.py','actor_did namespace convention.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/create_react_agent','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/prebuilt/create_react_agent','not_used','L3-runtime','P3','prebuilt ReAct loop',0,NULL,'Custom StateGraph nodes preferred (ADR-2605072000 explicit-flow stance).',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/functional','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/functional/entrypoint_task','not_used','L3-runtime','P2','remove StateGraph overhead for linear pipelines',0,NULL,'Candidates: patent_blob_convert.py, tsukuru_isic_pulse.py.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/checkpointer_none','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langgraph/runtime/checkpointer_none','used','L3-runtime',NULL,'Zeebe job owns durability',10,'20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py',NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/ChatAnthropic','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain_anthropic/ChatAnthropic','used','model',NULL,'sole LangChain model in use',5,'compintel/newsletter/webmk/outreach/contentengine workers','model resolved via resolveModelId().',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/RunnableConfig','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain_core/runnables/RunnableConfig','used','model',NULL,'type hint for checkpointer config',1,'20-actors/magatama/py/src/pymagatama/langgraph_checkpoint_rw.py',NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/PromptTemplate','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/prompts/PromptTemplate','not_used','model','P3','f-string in node functions instead',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Tool','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/tools/Tool','not_used','model','P3','direct function calls in nodes',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/AgentExecutor','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/agents/AgentExecutor','replaced','L3-runtime',NULL,'replaced by custom StateGraph nodes',0,NULL,'ADR-2605072000 mandates explicit ≥3-step flow.','feature/langgraph/graph/StateGraph',now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/OutputParser','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/parsers/OutputParser','not_used','model','P3','direct JSON parse',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Retriever','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/retrievers/Retriever','not_used','retrieval','P2','RW IVF vector + post-filter direct',0,NULL,'Aligned with SQL CONTAINS guardrail.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/DocumentLoader','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/loaders/DocumentLoader','not_used','retrieval','P3','Playwright/httpx direct',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/LCEL','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/runnables/LCEL','not_used','L3-runtime','P3','StateGraph nodes preferred',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Callback','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/callbacks/Callback','not_used','observability','P2','RW audit table replaces',0,NULL,NULL,NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/Memory','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/langchain/memory/Memory','replaced','persistence',NULL,'replaced by LangGraph BaseStore (RW)',0,NULL,'sole-DB principle (ADR-0048).','feature/langgraph/store/BaseStore',now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/prompt_caching','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/anthropic/prompt_caching','not_used','model','P0','Shannon source-coding: cache system prompt at 1024-token boundary',0,NULL,'Highest-ROI quick win. Cost reduction 50-90%.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/RisingWaveCheckpointSaver','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/internal/RisingWaveCheckpointSaver','used','persistence',NULL,'sole checkpoint backend',1,'20-actors/magatama/py/src/pymagatama/langgraph_checkpoint_rw.py','vertex_langgraph_checkpoint table.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/RisingWaveStore','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/internal/RisingWaveStore','used','persistence',NULL,'cross-thread memory backend',1,'20-actors/magatama/py/src/pymagatama/langgraph_store_rw.py','vertex_langgraph_store table.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/langgraph_registry','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/internal/langgraph_registry','used','L3-runtime',NULL,'module-level graph dispatch',1,'20-actors/magatama/py/src/pymagatama/primitives/langgraph_registry.py','Candidate for stored-program data-driven loader (P2).',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com'),
  ('usage/langchain-langgraph-pregel-20260509/resolve_model_id','at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509','feature/internal/resolve_model_id','used','model',NULL,'CRITICAL LLM Model SSoT',5,'20-actors/magatama/sdk/magatama-host-sdk/src/llm-model-registry.ts','Hardcoded model ID prohibited by guardrail.',NULL,now()::varchar,100,'did:web:amanomibashira.etzhayyim.com');

-- analysis covers feature_usage edges
INSERT INTO edge_analysis_covers_feature (edge_id, src_vid, dst_vid, edge_kind, created_at, sensitivity_ord, owner_did)
SELECT
  'edge/' || u.analysis_vertex_id || '/' || u.vertex_id AS edge_id,
  u.analysis_vertex_id AS src_vid,
  u.vertex_id          AS dst_vid,
  'covers'             AS edge_kind,
  now()::varchar       AS created_at,
  100                  AS sensitivity_ord,
  'did:web:amanomibashira.etzhayyim.com' AS owner_did
FROM vertex_codebase_feature_usage u
WHERE u.analysis_vertex_id = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509';

-- replaced_by edges
INSERT INTO edge_feature_replaces (edge_id, src_vid, dst_vid, reason, created_at, sensitivity_ord, owner_did)
SELECT
  'edge/replaces/' || u.vertex_id AS edge_id,
  u.feature_vertex_id            AS src_vid,
  u.replaced_by_feature_id       AS dst_vid,
  u.evidence_note                AS reason,
  now()::varchar                 AS created_at,
  100                            AS sensitivity_ord,
  'did:web:amanomibashira.etzhayyim.com'     AS owner_did
FROM vertex_codebase_feature_usage u
WHERE u.replaced_by_feature_id IS NOT NULL
  AND u.analysis_vertex_id = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509';

FLUSH;
