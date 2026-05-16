-- malak pursuit-loop schema — resident OSINT agent state (ADR-0036 / ADR-0095)
-- 3 vertex + 4 edge + 6 index + 2 MV
--
-- vertex_malak_pursuit_target   — what we are chasing (1 row per identifier)
-- vertex_malak_osint_source     — provenance (registry / API / scraper)
-- vertex_malak_osint_observation— what we learned in one OSINT tick
--
-- edge_malak_observation_about  — observation → target
-- edge_malak_observation_from   — observation → source
-- edge_malak_target_extends     — target → upstream yabai_entity (cross-link)
-- edge_malak_target_discovered  — observation → newly_discovered target (recursive)
--
-- Per ADR-2604241038 (record-log semantics) + ADR-0095 (RLS columns)
-- + ADR-0004 (no ON CONFLICT — delete-then-insert)

-- ─── Vertices ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_malak_pursuit_target (
    vertex_id              VARCHAR PRIMARY KEY,
    rkey                   VARCHAR NOT NULL,
    repo                   VARCHAR NOT NULL,
    target_id              VARCHAR NOT NULL,         -- canonical identifier (domain / handle / org name / phone / addr)
    target_kind            VARCHAR NOT NULL,         -- url | domain | line-p2p | line-open-chat | btc | eth | jp-name | jp-corp | phone | unknown
    case_id                VARCHAR NOT NULL,         -- e.g. case:takahashi-hiroyuki-20260512
    priority               INTEGER NOT NULL,         -- 0=stop, 1-9 (9=critical)
    pursuit_status         VARCHAR NOT NULL,         -- queued | active | exhausted | paused
    extends_entity_vid     VARCHAR,                  -- upstream yabai entity (if any)
    next_due_at            VARCHAR NOT NULL,         -- ISO8601 next tick time
    last_pursued_at        VARCHAR,                  -- ISO8601 last tick
    pursuit_tick_count     INTEGER NOT NULL,         -- monotonic count
    observation_count      INTEGER NOT NULL,
    note                   VARCHAR,
    tlp                    VARCHAR NOT NULL,
    created_at             VARCHAR NOT NULL,
    created_date           DATE NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL,
    org_id                 VARCHAR NOT NULL,
    user_id                VARCHAR NOT NULL,
    actor_id               VARCHAR NOT NULL,
    actor_did              VARCHAR NOT NULL,
    org_did                VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS vertex_malak_osint_source (
    vertex_id              VARCHAR PRIMARY KEY,
    rkey                   VARCHAR NOT NULL,
    repo                   VARCHAR NOT NULL,
    source_id              VARCHAR NOT NULL,         -- canonical name (e.g. crt.sh, urlscan.io, gbizinfo)
    source_kind            VARCHAR NOT NULL,         -- ct-log | passive-dns | whois | corp-registry | sanctions | web | manual
    source_url             VARCHAR,                  -- canonical home page
    api_endpoint           VARCHAR,                  -- query endpoint pattern
    auth_kind              VARCHAR NOT NULL,         -- none | api-key | oauth | scrape
    reliability_pct        INTEGER NOT NULL,         -- 0-100
    licensed               BOOLEAN NOT NULL,
    legal_basis            VARCHAR,                  -- e.g. "公開情報 OSINT"
    note                   VARCHAR,
    tlp                    VARCHAR NOT NULL,
    created_at             VARCHAR NOT NULL,
    created_date           DATE NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL,
    org_id                 VARCHAR NOT NULL,
    user_id                VARCHAR NOT NULL,
    actor_id               VARCHAR NOT NULL,
    actor_did              VARCHAR NOT NULL,
    org_did                VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS vertex_malak_osint_observation (
    vertex_id              VARCHAR PRIMARY KEY,
    rkey                   VARCHAR NOT NULL,
    repo                   VARCHAR NOT NULL,
    observation_id         VARCHAR NOT NULL,
    target_vid             VARCHAR NOT NULL,         -- → vertex_malak_pursuit_target.vertex_id
    source_vid             VARCHAR NOT NULL,         -- → vertex_malak_osint_source.vertex_id
    case_id                VARCHAR NOT NULL,
    finding_kind           VARCHAR NOT NULL,         -- whois-snapshot | cert-row | dns-record | corp-record | search-hit | abuse-report | screenshot | nothing-found
    title                  VARCHAR NOT NULL,
    body                   VARCHAR NOT NULL,
    body_sha256            VARCHAR NOT NULL,
    confidence             DOUBLE PRECISION NOT NULL,
    observed_at            VARCHAR NOT NULL,         -- timestamp the data referenced
    fetched_at             VARCHAR NOT NULL,
    raw_url                VARCHAR,                  -- exact fetched URL
    raw_status             INTEGER,                  -- HTTP status if applicable
    tick_seq               INTEGER NOT NULL,         -- N-th tick on this target
    tlp                    VARCHAR NOT NULL,
    created_at             VARCHAR NOT NULL,
    created_date           DATE NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL,
    org_id                 VARCHAR NOT NULL,
    user_id                VARCHAR NOT NULL,
    actor_id               VARCHAR NOT NULL,
    actor_did              VARCHAR NOT NULL,
    org_did                VARCHAR NOT NULL
);

-- ─── Edges ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS edge_malak_observation_about (
    src_id                 VARCHAR NOT NULL,         -- observation
    dst_id                 VARCHAR NOT NULL,         -- target
    edge_id                VARCHAR PRIMARY KEY,
    relation               VARCHAR NOT NULL,         -- 'observation_about'
    created_at             VARCHAR NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_malak_observation_from (
    src_id                 VARCHAR NOT NULL,         -- observation
    dst_id                 VARCHAR NOT NULL,         -- source
    edge_id                VARCHAR PRIMARY KEY,
    relation               VARCHAR NOT NULL,
    created_at             VARCHAR NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_malak_target_extends (
    src_id                 VARCHAR NOT NULL,         -- pursuit_target
    dst_id                 VARCHAR NOT NULL,         -- yabai_entity / malak_threat_actor / malak_bank_account
    edge_id                VARCHAR PRIMARY KEY,
    relation               VARCHAR NOT NULL,         -- 'extends' | 'about_entity'
    dst_kind               VARCHAR NOT NULL,         -- 'yabai_entity' | 'malak_threat_actor' | ...
    created_at             VARCHAR NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_malak_target_discovered (
    src_id                 VARCHAR NOT NULL,         -- discovering observation
    dst_id                 VARCHAR NOT NULL,         -- newly discovered target
    edge_id                VARCHAR PRIMARY KEY,
    relation               VARCHAR NOT NULL,         -- 'discovered'
    created_at             VARCHAR NOT NULL,
    sensitivity_ord        BIGINT NOT NULL,
    owner_did              VARCHAR NOT NULL
);

-- ─── Indexes ───────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_pursuit_target_priority
    ON vertex_malak_pursuit_target (pursuit_status, priority DESC, next_due_at);

CREATE INDEX IF NOT EXISTS idx_pursuit_target_case
    ON vertex_malak_pursuit_target (case_id, pursuit_status, priority DESC);

CREATE INDEX IF NOT EXISTS idx_pursuit_target_kind
    ON vertex_malak_pursuit_target (target_kind, pursuit_status);

CREATE INDEX IF NOT EXISTS idx_osint_observation_target
    ON vertex_malak_osint_observation (target_vid, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_osint_observation_source
    ON vertex_malak_osint_observation (source_vid, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_osint_observation_kind_conf
    ON vertex_malak_osint_observation (finding_kind, confidence DESC);

-- ─── MVs ───────────────────────────────────────────────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_pursuit_dashboard AS
SELECT
    t.target_kind,
    t.pursuit_status,
    t.case_id,
    COUNT(*)                                        AS targets,
    SUM(t.observation_count)                        AS observations,
    SUM(t.pursuit_tick_count)                       AS ticks,
    AVG(t.priority)                                 AS avg_priority,
    MAX(t.last_pursued_at)                          AS last_pursued_at,
    MIN(t.next_due_at)                              AS next_due_at
FROM vertex_malak_pursuit_target t
GROUP BY t.target_kind, t.pursuit_status, t.case_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_malak_osint_source_coverage AS
SELECT
    o.source_vid,
    s.source_id                                     AS source_name,
    s.source_kind                                   AS source_kind,
    s.reliability_pct                               AS source_reliability_pct,
    o.case_id,
    COUNT(*)                                        AS observations,
    COUNT(DISTINCT o.target_vid)                    AS distinct_targets,
    AVG(o.confidence)                               AS avg_confidence,
    MAX(o.fetched_at)                               AS last_fetched_at
FROM vertex_malak_osint_observation o
JOIN vertex_malak_osint_source s ON s.vertex_id = o.source_vid
GROUP BY o.source_vid, s.source_id, s.source_kind, s.reliability_pct, o.case_id;
