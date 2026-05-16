DROP MATERIALIZED VIEW IF EXISTS mv_maps_gsplat_job_latest;
DROP INDEX IF EXISTS idx_maps_gsplat_job_kind_status_ts;
DROP INDEX IF EXISTS idx_maps_gsplat_job_tile_ts;
DROP INDEX IF EXISTS idx_maps_gsplat_job_jobid_ts;
DROP TABLE IF EXISTS vertex_maps_gsplat_job;
