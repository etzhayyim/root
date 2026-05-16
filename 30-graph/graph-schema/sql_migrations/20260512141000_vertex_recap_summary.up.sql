-- vertex_recap_summary: LLM-generated summaries of media transcripts.
-- Written by lg-recap summarize graph.
-- ADR-0095: actor_did + org_did + at_did + created_at required.

CREATE TABLE IF NOT EXISTS vertex_recap_summary (
    vertex_id       varchar PRIMARY KEY,
    rkey            varchar NOT NULL,
    owner_did       varchar NOT NULL,
    actor_did       varchar NOT NULL,
    org_did         varchar NOT NULL DEFAULT 'anon',
    at_did          varchar,
    source_url      text NOT NULL,
    platform        varchar NOT NULL,
    title           text,
    uploader        varchar,
    duration_sec    integer,
    upload_date     varchar,
    license         varchar,
    transcript_lang varchar,
    transcript      text,
    summary         text,
    summary_lang    varchar NOT NULL DEFAULT 'ja',
    status          varchar NOT NULL DEFAULT 'done',
    created_at      varchar NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recap_summary_actor_did
    ON vertex_recap_summary (actor_did);

CREATE INDEX IF NOT EXISTS idx_recap_summary_platform_created
    ON vertex_recap_summary (platform, created_at DESC);
