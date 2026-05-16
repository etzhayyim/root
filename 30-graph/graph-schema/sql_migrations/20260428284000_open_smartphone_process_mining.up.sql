CREATE TABLE IF NOT EXISTS edge_open_smartphone_bom_uses_soc (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      bom_id VARCHAR NOT NULL,
      chip_id VARCHAR NOT NULL,
      component_role VARCHAR,
      quantity INTEGER NOT NULL DEFAULT 1,
      created_at VARCHAR NOT NULL
    );

CREATE TABLE IF NOT EXISTS edge_open_smartphone_bom_uses_modem (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      bom_id VARCHAR NOT NULL,
      modem_id VARCHAR NOT NULL,
      rat_required VARCHAR,
      quantity INTEGER NOT NULL DEFAULT 1,
      created_at VARCHAR NOT NULL
    );

CREATE TABLE IF NOT EXISTS edge_open_smartphone_patent_blocks_component (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      patent_no VARCHAR NOT NULL,
      component_type VARCHAR NOT NULL,
      rat VARCHAR,
      blocker_severity VARCHAR NOT NULL DEFAULT 'medium',
      pool_id VARCHAR,
      expiry_date VARCHAR,
      created_at VARCHAR NOT NULL
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_supply_chain_trace AS
    SELECT
      (value_json::jsonb ->> 'case_id')                          AS case_id,
      (value_json::jsonb ->> 'action')                           AS activity,
      (value_json::jsonb ->> 'layer')                            AS layer,
      repo                                                       AS actor_did,
      ts_ms,
      created_at                                                 AS timestamp,
      ((value_json::jsonb ->> 'duration_ms'))::bigint            AS duration_ms,
      (value_json::jsonb ->> 'status')                           AS status,
      (value_json::jsonb ->> 'objectRefs')                       AS object_refs_json,
      value_json                                                 AS payload_json
    FROM vertex_repo_commit
    WHERE collection = 'ai.gftd.bpmn.audit'
      AND (
        (value_json::jsonb ->> 'action') LIKE 'openSmartphone%'
        OR (value_json::jsonb ->> 'action') LIKE 'open-smartphone%'
        OR (value_json::jsonb ->> 'layer') LIKE 'open-smartphone%'
      );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_layer_kpi AS
    SELECT
      layer,
      activity,
      count(*)                                            AS exec_count,
      avg(duration_ms)::bigint                            AS avg_duration_ms,
      max(duration_ms)                                    AS max_duration_ms,
      sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END)  AS error_count,
      sum(CASE WHEN status = 'ok'    THEN 1 ELSE 0 END)  AS success_count
    FROM mv_open_smartphone_supply_chain_trace
    WHERE duration_ms IS NOT NULL
    GROUP BY layer, activity;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_bom_coverage AS
    SELECT
      b.vertex_id                                                        AS bom_vid,
      b.bom_id,
      b.design_name,
      count(bl.vertex_id)                                                AS total_lines,
      sum(CASE WHEN bl.open_source THEN 1 ELSE 0 END)                   AS open_lines,
      sum(CASE WHEN bl.component_type = 'soc'    THEN 1 ELSE 0 END)    AS soc_lines,
      sum(CASE WHEN bl.component_type = 'modem'  THEN 1 ELSE 0 END)    AS modem_lines,
      sum(CASE WHEN bl.component_type = 'sensor' THEN 1 ELSE 0 END)    AS sensor_lines,
      sum(CASE WHEN bl.component_type = 'os'     THEN 1 ELSE 0 END)    AS os_lines,
      sum(CASE WHEN bl.component_type = 'ems'    THEN 1 ELSE 0 END)    AS ems_lines,
      sum(CASE WHEN bl.component_type = 'patent' THEN 1 ELSE 0 END)    AS patent_lines,
      CASE
        WHEN count(bl.vertex_id) = 0 THEN 0.0
        ELSE (sum(CASE WHEN bl.open_source THEN 1 ELSE 0 END)::double precision
              / count(bl.vertex_id)::double precision * 100.0)
      END                                                                AS open_score_pct,
      b.open_score_pct                                                   AS llm_open_score_pct
    FROM vertex_open_smartphone_bom b
    LEFT JOIN vertex_open_smartphone_bom_line bl ON bl.bom_did = b.bom_id
    GROUP BY b.vertex_id, b.bom_id, b.design_name, b.open_score_pct;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_sep_risk_summary AS
    SELECT
      ps.rat,
      ps.standard,
      count(ps.vertex_id)                                          AS total_seps,
      sum(CASE WHEN ps.frand_declared THEN 1 ELSE 0 END)          AS frand_count,
      sum(CASE WHEN ps.pool_id IS NOT NULL THEN 1 ELSE 0 END)     AS pooled_count,
      sum(CASE WHEN ps.expiry_date IS NOT NULL
                AND ps.expiry_date < '2028-04-28'
               THEN 1 ELSE 0 END)                                 AS expiring_24m,
      sum(CASE WHEN ms.blocker_status = 'active' THEN 1 ELSE 0 END) AS active_blockers,
      count(DISTINCT pp.pool_id)                                   AS pool_count,
      min(pp.license_fee_usd_per_unit)                             AS min_pool_fee_usd,
      max(pp.license_fee_usd_per_unit)                             AS max_pool_fee_usd
    FROM vertex_open_smartphone_patent_sep ps
    LEFT JOIN vertex_open_smartphone_modem_sep_dep ms
           ON ms.patent_no = ps.patent_no
    LEFT JOIN vertex_open_smartphone_patent_pool pp
           ON pp.pool_id = ps.pool_id
    GROUP BY ps.rat, ps.standard;
