-- sqlc schema mirror — keep in sync with Alembic `r_20260511022700_research_gpu_adr`
-- + SQLMesh models (`mv_research_gpu_price_compare.sql`, `mv_research_adr_graph.sql`).
-- sqlc reads this file at codegen time; Alembic/SQLMesh own the live DB.
-- If divergence is suspected, regenerate this file from `pnpm db:gen --sqlc-schema`
-- (TODO: ADR-2605110227 §3.9b).

CREATE TABLE public.vertex_research_gpu_model (
  did_path TEXT PRIMARY KEY,
  vendor TEXT,
  model TEXT,
  vram_gb_full INTEGER,
  generation TEXT,
  fp8_native BOOLEAN,
  fp16_tflops_full INTEGER,
  created_at TIMESTAMPTZ
);

CREATE TABLE public.vertex_research_gpu_plan (
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

CREATE TABLE public.vertex_research_gpu_provider (
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

CREATE TABLE public.edge_research_plan_uses_gpu (
  plan_did_path TEXT,
  model_did_path TEXT,
  PRIMARY KEY (plan_did_path, model_did_path)
);

CREATE TABLE public.edge_research_provider_offers_plan (
  provider_did_path TEXT,
  plan_did_path TEXT,
  PRIMARY KEY (provider_did_path, plan_did_path)
);

CREATE TABLE public.vertex_research_adr (
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

CREATE TABLE public.edge_research_adr_relates (
  from_did TEXT,
  to_did TEXT,
  relation TEXT,
  PRIMARY KEY (from_did, to_did, relation)
);

-- SQLMesh MVs — declared as regular views for sqlc's purposes
-- (sqlc doesn't care about MATERIALIZED; only the column shape matters).
CREATE VIEW public.mv_research_gpu_price_compare AS
SELECT
  m.did_path AS gpu_did,
  m.vendor,
  m.model,
  m.vram_gb_full,
  m.generation,
  m.fp8_native,
  MAX(CASE WHEN p.provider = 'vultr-cloud'   THEN p.hourly_usd_per_gpu END) AS vultr_cloud_hr,
  MAX(CASE WHEN p.provider = 'vultr-bm'      THEN p.hourly_usd_per_gpu END) AS vultr_bm_hr,
  MAX(CASE WHEN p.provider = 'runpod-secure' THEN p.hourly_usd_per_gpu END) AS runpod_secure_hr,
  MIN(CASE WHEN p.provider = 'digitalocean' THEN p.hourly_usd_per_gpu END) AS digitalocean_hr,
  MIN(CASE WHEN p.provider = 'digitalocean' AND p.plan_id LIKE 'res-%' THEN p.hourly_usd_per_gpu END) AS digitalocean_reserved_hr
FROM public.vertex_research_gpu_model m
JOIN public.edge_research_plan_uses_gpu e ON e.model_did_path = m.did_path
JOIN public.vertex_research_gpu_plan   p ON p.did_path        = e.plan_did_path
GROUP BY m.did_path, m.vendor, m.model, m.vram_gb_full, m.generation, m.fp8_native;

CREATE VIEW public.mv_research_adr_graph AS
SELECT
  v.did_path,
  v.adr_id,
  v.title,
  v.status,
  v.topic,
  v.authoritative,
  v.last_verified,
  COUNT(DISTINCT CASE WHEN e.relation = 'related'        THEN e.to_did END)::INTEGER AS related_count,
  COUNT(DISTINCT CASE WHEN e.relation = 'supersedes'     THEN e.to_did END)::INTEGER AS supersedes_count,
  COUNT(DISTINCT CASE WHEN e.relation = 'superseded_by'  THEN e.to_did END)::INTEGER AS superseded_by_count,
  COUNT(DISTINCT CASE WHEN e.relation = 'amends'         THEN e.to_did END)::INTEGER AS amends_count,
  COUNT(DISTINCT CASE WHEN e.relation = 'amended_by'     THEN e.to_did END)::INTEGER AS amended_by_count
FROM public.vertex_research_adr v
LEFT JOIN public.edge_research_adr_relates e ON e.from_did = v.did_path
GROUP BY v.did_path, v.adr_id, v.title, v.status, v.topic, v.authoritative, v.last_verified;
