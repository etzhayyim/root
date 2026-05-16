-- vertex_inbox_triage: inbox triage classification results (pregel 常駐化)
-- ADR-0095: actor_did, org_did, at_did (nullable), created_at required columns
-- RisingWave: no ON CONFLICT; float → integer permille

CREATE TABLE IF NOT EXISTS graphar.vertex_inbox_triage (
    -- ADR-0095 identity columns
    actor_did   VARCHAR          NOT NULL,
    org_did     VARCHAR          NOT NULL,
    at_did      VARCHAR,

    -- primary key: Graph AT URI
    vertex_id   VARCHAR          NOT NULL PRIMARY KEY,

    -- message identity
    message_id  VARCHAR          NOT NULL,

    -- sender metadata
    from_addr   VARCHAR          NOT NULL DEFAULT '',
    from_name   VARCHAR          NOT NULL DEFAULT '',

    -- email metadata
    subject     VARCHAR          NOT NULL DEFAULT '',
    received_at VARCHAR          NOT NULL DEFAULT '',
    body_preview TEXT            NOT NULL DEFAULT '',

    -- triage classification
    triage_category         VARCHAR NOT NULL,       -- KEEP | ARCHIVE | DELETE
    triage_reason           TEXT    NOT NULL DEFAULT '',
    triage_confidence_permille INTEGER NOT NULL DEFAULT 0, -- 0-1000 (float not supported in RW)
    triage_method           VARCHAR NOT NULL DEFAULT 'heuristic', -- heuristic | llm | heuristic-csv

    -- execution tracking
    triage_at   TIMESTAMPTZ      NOT NULL,
    moved_at    TIMESTAMPTZ,
    move_ok     BOOLEAN,

    -- ADR-0095 audit column
    created_at  TIMESTAMPTZ      NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vertex_inbox_triage_message_id
    ON graphar.vertex_inbox_triage (message_id);

CREATE INDEX IF NOT EXISTS idx_vertex_inbox_triage_actor_did
    ON graphar.vertex_inbox_triage (actor_did);

CREATE INDEX IF NOT EXISTS idx_vertex_inbox_triage_category
    ON graphar.vertex_inbox_triage (triage_category);

CREATE INDEX IF NOT EXISTS idx_vertex_inbox_triage_received_at
    ON graphar.vertex_inbox_triage (received_at);
