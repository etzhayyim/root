-- vertex_recap_download: multi-platform media download records.
--
-- Written by lg-recap LangGraph download graph (psycopg direct INSERT).
-- Fair-use policy enforced at application layer (scope IN ('research','authorized')).
-- ADR-0095: actor_did + org_did + at_did + created_at required on all new tables.

CREATE TABLE IF NOT EXISTS vertex_recap_download (
    vertex_id           varchar PRIMARY KEY,
    rkey                varchar NOT NULL,
    owner_did           varchar NOT NULL,
    actor_did           varchar NOT NULL,
    org_did             varchar NOT NULL DEFAULT 'anon',
    at_did              varchar,
    source_url          text NOT NULL,
    platform            varchar NOT NULL,
    title               text,
    uploader            varchar,
    duration_sec        integer,
    upload_date         varchar,
    format_id           varchar,
    format_note         varchar,
    blob_key            varchar,
    blob_size_bytes     bigint,
    thumbnail_url       text,
    status              varchar NOT NULL DEFAULT 'done',
    scope               varchar NOT NULL DEFAULT 'research',
    error_msg           text,
    created_at          varchar NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recap_download_actor_did
    ON vertex_recap_download (actor_did);

CREATE INDEX IF NOT EXISTS idx_recap_download_platform_created
    ON vertex_recap_download (platform, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recap_download_status
    ON vertex_recap_download (status);
