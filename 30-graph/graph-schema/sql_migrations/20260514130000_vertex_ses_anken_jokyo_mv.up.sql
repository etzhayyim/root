-- Migration: SES 案件・状況 materialized views (ADR-2605120000)
-- Apply AFTER indexes settle. Uses ROW_NUMBER (not DISTINCT ON — unsupported in RW).

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ses_anken_latest_jokyo AS
SELECT
    anken_vertex_id,
    vertex_id  AS jokyo_vertex_id,
    jokyo,
    created_at AS jokyo_created_at
FROM (
    SELECT
        anken_vertex_id,
        vertex_id,
        jokyo,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY anken_vertex_id
            ORDER BY created_at DESC
        ) AS rn
    FROM vertex_ses_jokyo
) sub
WHERE rn = 1;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ses_anken_active AS
SELECT
    a.vertex_id,
    a.actor_did,
    a.org_did,
    a.client_name,
    a.client_company,
    a.start_month,
    a.rate_lower_yen,
    a.rate_upper_yen,
    a.work_location,
    a.remote_ok,
    lj.jokyo AS current_jokyo,
    lj.jokyo_created_at
FROM vertex_ses_anken a
JOIN mv_ses_anken_latest_jokyo lj ON lj.anken_vertex_id = a.vertex_id
WHERE lj.jokyo IN ('提案中', '選考中', '契約', '稼働中');
