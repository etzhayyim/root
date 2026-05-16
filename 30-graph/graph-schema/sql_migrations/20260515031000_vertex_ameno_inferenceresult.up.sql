-- ADR-2605111200 — vertex_ameno_inferenceresult.
-- Append-only browser WebGPU inference result, written by ameno-langserver
-- pod after CF Worker → bpmn-dispatcher → AgentGateway MCP → langserver.
-- RisingWave-friendly (varchar/bigint, no JSONB, no soft delete).
-- RLS columns per ADR-0095 (actor_did / org_did / at_did / created_at).
CREATE TABLE IF NOT EXISTS vertex_ameno_inferenceresult (
  vertex_id        VARCHAR PRIMARY KEY,
  result_id        VARCHAR,
  model_id         VARCHAR NOT NULL,
  lora_adapters    VARCHAR,
  prompt           VARCHAR,
  output           VARCHAR,
  prompt_tokens    BIGINT,
  output_tokens    BIGINT,
  elapsed_ms       BIGINT,
  tokens_per_sec   BIGINT,
  webgpu_adapter   VARCHAR,
  rag_context_used BOOLEAN,
  actor_did        VARCHAR NOT NULL,
  org_did          VARCHAR NOT NULL,
  at_did           VARCHAR,
  owner_did        VARCHAR,
  sensitivity_ord  BIGINT,
  created_at       VARCHAR NOT NULL
);
