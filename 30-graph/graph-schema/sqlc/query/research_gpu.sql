-- name: GpuPriceCompareList :many
-- Cross-provider GPU $/hr comparison from the SQLMesh MV.
-- Used by etzhayyim.research.gpuPriceCompare (mcp-adapter.ts).
SELECT
  gpu_did,
  vendor,
  model,
  vram_gb_full,
  generation,
  fp8_native,
  vultr_cloud_hr,
  vultr_bm_hr,
  runpod_secure_hr,
  digitalocean_hr,
  digitalocean_reserved_hr
FROM public.mv_research_gpu_price_compare
WHERE (sqlc.narg('model_substr')::text IS NULL OR model ILIKE '%' || sqlc.narg('model_substr')::text || '%')
  AND (sqlc.narg('vendor')::text IS NULL OR vendor = sqlc.narg('vendor')::text)
  AND (sqlc.narg('vram_min_gb')::integer IS NULL OR vram_gb_full >= sqlc.narg('vram_min_gb')::integer)
  AND (sqlc.narg('fp8_native')::boolean IS NULL OR fp8_native = sqlc.narg('fp8_native')::boolean)
  AND (sqlc.narg('generation')::text IS NULL OR generation = sqlc.narg('generation')::text)
ORDER BY runpod_secure_hr NULLS LAST, vultr_cloud_hr NULLS LAST
LIMIT sqlc.arg('row_limit')::integer;

-- name: GpuPlanListByGpu :many
-- Detail plans for one GPU model (drill-down from compare view).
SELECT
  p.did_path,
  p.provider,
  p.plan_id,
  p.vcpu,
  p.ram_gb,
  p.disk_gb,
  p.gpu_count,
  p.vram_gb_total,
  p.monthly_usd,
  p.hourly_usd,
  p.hourly_usd_per_gpu,
  p.bandwidth_alliance_b2,
  p.k8s_capable
FROM public.vertex_research_gpu_plan p
JOIN public.edge_research_plan_uses_gpu e ON e.plan_did_path = p.did_path
WHERE e.model_did_path = sqlc.arg('model_did')::text
ORDER BY p.hourly_usd_per_gpu NULLS LAST;
