-- Migration: vertex_open_patent_invention_seed + vertex_open_patent_novelty_report
-- Project: etzhayyim-project-open-patent (op3np4t1)
-- RisingWave: no VARCHAR(N), no DEFAULT CURRENT_DATE

CREATE TABLE IF NOT EXISTS vertex_open_patent_invention_seed (
    vertex_id               VARCHAR      PRIMARY KEY,
    _seq                    BIGINT,
    created_date            DATE,
    sensitivity_ord         INT,
    owner_did               VARCHAR,
    tech_domain             VARCHAR,
    title                   VARCHAR,
    summary                 VARCHAR,
    key_claims_json         VARCHAR,
    ipc_class               VARCHAR,
    corpus_patent_ids_json  VARCHAR,
    novelty_score           INT,
    novelty_status          VARCHAR,
    created_at              VARCHAR,
    actor_id                VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_open_patent_novelty_report (
    vertex_id               VARCHAR      PRIMARY KEY,
    _seq                    BIGINT,
    created_date            DATE,
    sensitivity_ord         INT,
    owner_did               VARCHAR,
    seed_vid                VARCHAR,
    prior_art_count         INT,
    prior_art_vids_json     VARCHAR,
    similarity_scores_json  VARCHAR,
    overall_novelty_score   INT,
    reasoning               VARCHAR,
    created_at              VARCHAR,
    actor_id                VARCHAR
);
