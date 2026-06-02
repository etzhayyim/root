CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_trace AS
    SELECT
      (value_json::jsonb -> 'case_id')::varchar    AS case_id,
      (value_json::jsonb -> 'action')::varchar     AS activity,
      repo                                         AS actor_did,
      ts_ms                                        AS ts_ms,
      created_at                                   AS timestamp,
      ((value_json::jsonb -> 'duration_ms')::varchar)::bigint   AS duration_ms,
      (value_json::jsonb -> 'status')::varchar     AS status,
      (value_json::jsonb -> 'objectRefs')::varchar AS object_refs_json,
      value_json                                   AS payload_json
    FROM vertex_repo_commit
    WHERE collection = 'com.etzhayyim.bpmn.audit'
      AND (value_json::jsonb -> 'action')::varchar LIKE 'mangaka.%';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_kpi AS
    SELECT
      activity,
      count(*)                                          AS exec_count,
      avg(duration_ms)::bigint                          AS avg_duration_ms,
      max(duration_ms)                                  AS max_duration_ms,
      min(duration_ms)                                  AS min_duration_ms,
      sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
      sum(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) AS partial_count
    FROM mv_mangaka_process_trace
    WHERE duration_ms IS NOT NULL
    GROUP BY activity;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_case_summary AS
    SELECT
      case_id,
      count(*)                                          AS phase_count,
      sum(duration_ms)                                  AS total_duration_ms,
      sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
      max(timestamp)                                    AS last_event_at,
      CASE
        WHEN max(activity) = 'mangaka.episodePublished' THEN 'complete'
        WHEN sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) > 0 THEN 'failed'
        ELSE 'running'
      END                                               AS status
    FROM mv_mangaka_process_trace
    GROUP BY case_id;
