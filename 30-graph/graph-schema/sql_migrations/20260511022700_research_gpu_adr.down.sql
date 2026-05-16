-- ADR-2605110227 — drop research base tables.
DROP INDEX IF EXISTS public.idx_research_adr_relates_to;
DROP INDEX IF EXISTS public.idx_research_adr_topic;
DROP INDEX IF EXISTS public.idx_research_adr_status;
DROP INDEX IF EXISTS public.idx_research_gpu_model_generation;
DROP INDEX IF EXISTS public.idx_research_gpu_plan_hourly_per_gpu;
DROP INDEX IF EXISTS public.idx_research_gpu_plan_provider;

DROP TABLE IF EXISTS public.edge_research_adr_relates;
DROP TABLE IF EXISTS public.vertex_research_adr;
DROP TABLE IF EXISTS public.edge_research_provider_offers_plan;
DROP TABLE IF EXISTS public.edge_research_plan_uses_gpu;
DROP TABLE IF EXISTS public.vertex_research_gpu_provider;
DROP TABLE IF EXISTS public.vertex_research_gpu_plan;
DROP TABLE IF EXISTS public.vertex_research_gpu_model;
