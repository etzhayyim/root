-- Migration: SES 案件・状況 indexes (ADR-2605120000) — apply AFTER tables settle
-- Separate file so the phased applier can INSERT the idx phase after a 2s sleep.

CREATE INDEX IF NOT EXISTS idx_ses_anken_actor_did
    ON vertex_ses_anken (actor_did);

CREATE INDEX IF NOT EXISTS idx_ses_anken_client_name
    ON vertex_ses_anken (client_name);

CREATE INDEX IF NOT EXISTS idx_ses_jokyo_anken
    ON vertex_ses_jokyo (anken_vertex_id);

CREATE INDEX IF NOT EXISTS idx_ses_jokyo_created
    ON vertex_ses_jokyo (created_at);

CREATE INDEX IF NOT EXISTS idx_ses_run_actor
    ON vertex_ses_run (actor_did);

CREATE INDEX IF NOT EXISTS idx_ses_anken_client_src
    ON edge_ses_anken_client (src_vid);

CREATE INDEX IF NOT EXISTS idx_ses_anken_engineer_src
    ON edge_ses_anken_engineer (src_vid);
