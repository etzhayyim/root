-- Migration: SES 案件・状況 graph tables (ADR-2605120000)
-- Project: etzhayyim-project-ses (ses.etzhayyim.com)
-- Apply: phased psycopg2 — tables → settle → indexes → MVs
-- RisingWave: no VARCHAR(N), no DEFAULT CURRENT_DATE, no ON CONFLICT,
--   no ILIKE, no DISTINCT ON (use ROW_NUMBER window for MV)

-- ── Vertex tables ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_ses_anken (
    vertex_id       VARCHAR     PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord INT,
    owner_did       VARCHAR,
    actor_did       VARCHAR,
    org_did         VARCHAR,
    at_did          VARCHAR,
    client_name     VARCHAR,
    client_company  VARCHAR,
    skill_reqs_json VARCHAR,
    start_month     VARCHAR,
    end_month       VARCHAR,
    rate_lower_yen  INT,
    rate_upper_yen  INT,
    work_location   VARCHAR,
    remote_ok       BOOLEAN,
    engineer_name   VARCHAR,
    notes           VARCHAR,
    source_kind     VARCHAR,
    created_at      VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_ses_jokyo (
    vertex_id       VARCHAR     PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord INT,
    owner_did       VARCHAR,
    actor_did       VARCHAR,
    org_did         VARCHAR,
    at_did          VARCHAR,
    anken_vertex_id VARCHAR,
    jokyo           VARCHAR,
    rationale       VARCHAR,
    run_id          VARCHAR,
    created_at      VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_ses_client (
    vertex_id           VARCHAR     PRIMARY KEY,
    _seq                BIGINT,
    created_date        DATE,
    sensitivity_ord     INT,
    owner_did           VARCHAR,
    actor_did           VARCHAR,
    org_did             VARCHAR,
    at_did              VARCHAR,
    client_company      VARCHAR,
    company_normalized  VARCHAR,
    first_seen_at       VARCHAR,
    created_at          VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_ses_engineer (
    vertex_id           VARCHAR     PRIMARY KEY,
    _seq                BIGINT,
    created_date        DATE,
    sensitivity_ord     INT,
    owner_did           VARCHAR,
    actor_did           VARCHAR,
    org_did             VARCHAR,
    at_did              VARCHAR,
    engineer_name       VARCHAR,
    name_normalized     VARCHAR,
    first_seen_at       VARCHAR,
    created_at          VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_ses_run (
    vertex_id           VARCHAR     PRIMARY KEY,
    _seq                BIGINT,
    created_date        DATE,
    sensitivity_ord     INT,
    owner_did           VARCHAR,
    actor_did           VARCHAR,
    org_did             VARCHAR,
    at_did              VARCHAR,
    run_id              VARCHAR,
    source_kind         VARCHAR,
    anken_decision      VARCHAR,
    anken_vertex_id     VARCHAR,
    jokyo_vertex_id     VARCHAR,
    jokyo_appended      BOOLEAN,
    jokyo_skipped       BOOLEAN,
    status              VARCHAR,
    error_text          VARCHAR,
    model_ids_json      VARCHAR,
    tokens_total        INT,
    started_at          VARCHAR,
    finished_at         VARCHAR,
    created_at          VARCHAR
);

-- ── Edge tables ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS edge_ses_anken_client (
    edge_id         VARCHAR     PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord INT,
    owner_did       VARCHAR,
    actor_did       VARCHAR,
    org_did         VARCHAR,
    created_at      VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_ses_anken_engineer (
    edge_id         VARCHAR     PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord INT,
    owner_did       VARCHAR,
    actor_did       VARCHAR,
    org_did         VARCHAR,
    created_at      VARCHAR
);
