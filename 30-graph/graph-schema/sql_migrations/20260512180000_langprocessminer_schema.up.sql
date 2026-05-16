CREATE TABLE IF NOT EXISTS vertex_langprocessminer_trace (
    vertex_id      VARCHAR PRIMARY KEY,
    rkey           VARCHAR NOT NULL,
    repo           VARCHAR NOT NULL,
    trace_id       VARCHAR NOT NULL,
    agent_role     VARCHAR NOT NULL,
    run_name       VARCHAR NOT NULL,
    input_json     VARCHAR,
    output_json    VARCHAR,
    start_time     TIMESTAMPTZ NOT NULL,
    end_time       TIMESTAMPTZ,
    status         VARCHAR NOT NULL,
    total_tokens   INT DEFAULT 0,
    created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_date   DATE,
    owner_did      VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS vertex_langprocessminer_span (
    vertex_id      VARCHAR PRIMARY KEY,
    rkey           VARCHAR NOT NULL,
    repo           VARCHAR NOT NULL,
    span_id        VARCHAR NOT NULL,
    trace_id       VARCHAR NOT NULL,
    node_name      VARCHAR NOT NULL,
    span_kind      VARCHAR NOT NULL,
    input_json     VARCHAR,
    output_json    VARCHAR,
    error_msg      VARCHAR,
    start_time     TIMESTAMPTZ NOT NULL,
    end_time       TIMESTAMPTZ,
    prompt_tokens  INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_date   DATE,
    owner_did      VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_langprocessminer_span_hierarchy (
    edge_id        VARCHAR PRIMARY KEY,
    rkey           VARCHAR NOT NULL,
    repo           VARCHAR NOT NULL,
    src_vid        VARCHAR NOT NULL, -- parent trace or span
    dst_vid        VARCHAR NOT NULL, -- child span
    created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_date   DATE,
    owner_did      VARCHAR NOT NULL
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_lpm_trace_by_agent 
    ON vertex_langprocessminer_trace (agent_role, start_time DESC);

CREATE INDEX IF NOT EXISTS idx_lpm_span_by_trace 
    ON vertex_langprocessminer_span (trace_id, start_time ASC);

-- MV for real-time agent performance analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lpm_agent_performance_summary AS
SELECT
    agent_role,
    created_date,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE status = 'error') AS error_count,
    AVG(EXTRACT(EPOCH FROM (end_time - start_time))) AS avg_duration_sec,
    SUM(total_tokens) AS total_tokens_used
FROM
    vertex_langprocessminer_trace
GROUP BY
    agent_role,
    created_date;

FLUSH;
