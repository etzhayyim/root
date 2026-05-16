-- ADR-2605110227 — research datasets (base tables only).
-- MVs are owned by SQLMesh (30-graph/graph-schema/sqlmesh/models/), NOT here.
-- Persistence convention: root CLAUDE.md "Record-log semantics" — no UPDATE,
-- no ON CONFLICT; PK re-INSERT = implicit upsert.

-- ── GPU pricing research (Vultr / RunPod / DO / etc.) ──

CREATE TABLE IF NOT EXISTS public.vertex_research_gpu_model (
  did_path TEXT PRIMARY KEY,
  vendor TEXT,
  model TEXT,
  vram_gb_full INTEGER,
  generation TEXT,
  fp8_native BOOLEAN,
  fp16_tflops_full INTEGER,
  created_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.vertex_research_gpu_plan (
  did_path TEXT PRIMARY KEY,
  provider TEXT,
  plan_id TEXT,
  vcpu INTEGER,
  ram_gb INTEGER,
  disk_gb INTEGER,
  gpu_count INTEGER,
  vram_gb_total INTEGER,
  monthly_usd NUMERIC,
  hourly_usd NUMERIC,
  hourly_usd_per_gpu NUMERIC,
  bandwidth_alliance_b2 BOOLEAN,
  k8s_capable BOOLEAN,
  source_url TEXT,
  fetched_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.vertex_research_gpu_provider (
  did_path TEXT PRIMARY KEY,
  name TEXT,
  category TEXT,
  bandwidth_alliance_b2 BOOLEAN,
  k8s_native BOOLEAN,
  k8s_managed_service TEXT,
  soc2 BOOLEAN,
  billing_min_unit TEXT,
  fetched_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.edge_research_plan_uses_gpu (
  plan_did_path TEXT,
  model_did_path TEXT,
  PRIMARY KEY (plan_did_path, model_did_path)
);

CREATE TABLE IF NOT EXISTS public.edge_research_provider_offers_plan (
  provider_did_path TEXT,
  plan_did_path TEXT,
  PRIMARY KEY (provider_did_path, plan_did_path)
);

-- ── ADR frontmatter graph ──

CREATE TABLE IF NOT EXISTS public.vertex_research_adr (
  did_path TEXT PRIMARY KEY,
  adr_id TEXT,
  title TEXT,
  status TEXT,
  doc_type TEXT,
  topic TEXT,
  authoritative BOOLEAN,
  last_verified TEXT,
  body_path TEXT,
  authoritative_for_count INTEGER,
  fetched_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.edge_research_adr_relates (
  from_did TEXT,
  to_did TEXT,
  relation TEXT,
  PRIMARY KEY (from_did, to_did, relation)
);

-- ── Lookup indexes (base-table layer only; MV indexes live with SQLMesh) ──

CREATE INDEX IF NOT EXISTS idx_research_gpu_plan_provider
  ON public.vertex_research_gpu_plan (provider);

CREATE INDEX IF NOT EXISTS idx_research_gpu_plan_hourly_per_gpu
  ON public.vertex_research_gpu_plan (hourly_usd_per_gpu);

CREATE INDEX IF NOT EXISTS idx_research_gpu_model_generation
  ON public.vertex_research_gpu_model (generation);

CREATE INDEX IF NOT EXISTS idx_research_adr_status
  ON public.vertex_research_adr (status);

CREATE INDEX IF NOT EXISTS idx_research_adr_topic
  ON public.vertex_research_adr (topic);

CREATE INDEX IF NOT EXISTS idx_research_adr_relates_to
  ON public.edge_research_adr_relates (to_did);
