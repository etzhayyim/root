CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_corp_finance_process_trace AS
    SELECT
      COALESCE(
        value_json::jsonb ->> 'case_id',
        value_json::jsonb ->> 'runId',
        rkey
      )                                                       AS case_id,
      value_json::jsonb ->> 'action'                         AS activity,
      repo                                                    AS actor_did,
      ts_ms,
      created_at                                              AS timestamp,
      NULLIF(value_json::jsonb ->> 'duration_ms', '')::bigint AS duration_ms,
      COALESCE(value_json::jsonb ->> 'status', 'ok')          AS status,
      value_json::jsonb ->> 'sourceId'                        AS source_id,
      value_json::jsonb ->> 'targetDate'                      AS target_date,
      value_json::jsonb ->> 'jcn'                             AS jcn,
      value_json::jsonb ->> 'edinetCode'                      AS edinet_code,
      NULLIF(value_json::jsonb ->> 'recordsPrepared', '')::bigint AS records_prepared,
      NULLIF(value_json::jsonb ->> 'recordsWritten', '')::bigint  AS records_written,
      NULLIF(value_json::jsonb ->> 'recordsVisible', '')::bigint  AS records_visible,
      NULLIF(value_json::jsonb ->> 'invalidCount', '')::bigint    AS invalid_count,
      value_json                                               AS payload_json
    FROM vertex_repo_commit
    WHERE collection = 'com.etzhayyim.bpmn.audit'
      AND (value_json::jsonb ->> 'action') LIKE 'jpCorpFinance.%';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_corp_finance_process_kpi AS
    SELECT
      activity,
      source_id,
      count(*)                                                   AS exec_count,
      avg(duration_ms)::bigint                                   AS avg_duration_ms,
      max(duration_ms)                                           AS max_duration_ms,
      sum(CASE WHEN status IN ('error', 'failed') THEN 1 ELSE 0 END) AS error_count,
      sum(CASE WHEN status = 'ok' THEN 1 ELSE 0 END)             AS success_count,
      sum(COALESCE(records_prepared, 0))                         AS records_prepared,
      sum(COALESCE(records_written, 0))                          AS records_written,
      sum(COALESCE(records_visible, 0))                          AS records_visible,
      sum(COALESCE(invalid_count, 0))                            AS invalid_count
    FROM mv_jp_corp_finance_process_trace
    GROUP BY activity, source_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_corp_finance_process_case_summary AS
    SELECT
      case_id,
      count(*)                                                   AS event_count,
      min(timestamp)                                             AS first_event_at,
      max(timestamp)                                             AS last_event_at,
      max(source_id)                                             AS source_id,
      max(target_date)                                           AS target_date,
      max(jcn)                                                   AS jcn,
      max(edinet_code)                                           AS edinet_code,
      sum(COALESCE(records_prepared, 0))                         AS records_prepared,
      sum(COALESCE(records_written, 0))                          AS records_written,
      sum(COALESCE(records_visible, 0))                          AS records_visible,
      sum(COALESCE(invalid_count, 0))                            AS invalid_count,
      CASE
        WHEN sum(CASE WHEN status IN ('error', 'failed') THEN 1 ELSE 0 END) > 0 THEN 'failed'
        WHEN max(activity) LIKE 'jpCorpFinance.%.completed' THEN 'complete'
        ELSE 'running'
      END                                                       AS status
    FROM mv_jp_corp_finance_process_trace
    GROUP BY case_id;
