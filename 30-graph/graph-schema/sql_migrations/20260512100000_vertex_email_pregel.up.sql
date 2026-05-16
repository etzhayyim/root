-- pregel email analysis schema: vertex/edge/idx/mv
-- intent, urgency, sales detection, dependency mapping
-- NO ON CONFLICT, NO float, NO nested array-of-object — AT Protocol record-log rules apply

-- ─── vertex: one row per email message (append-only) ────────────────────────
CREATE TABLE IF NOT EXISTS graphar.vertex_email_message (
    -- identity
    message_id          VARCHAR         NOT NULL,   -- hash(message-id header) = AT record key
    thread_id           VARCHAR,                    -- hash(In-Reply-To chain)
    external_id         VARCHAR,                    -- raw Message-ID header (truncated 500)

    -- envelope
    from_address        VARCHAR         NOT NULL,
    from_name           VARCHAR,
    to_addresses        VARCHAR,                    -- comma-separated
    cc_addresses        VARCHAR,
    subject             VARCHAR,
    received_at         TIMESTAMPTZ     NOT NULL,
    body_preview        VARCHAR,                    -- first 500 chars, no PII encrypt needed (preview only)

    -- AI classification (written by pregel langserver)
    intent_primary      VARCHAR,        -- billing | sales | hr | ops | legal | tech | info | urgent | internal
    intent_secondary    VARCHAR,        -- comma-separated secondary intents
    urgency_score       INTEGER,        -- 0-100; 80+ = red, 50-79 = yellow, 0-49 = green
    action_required     BOOLEAN         DEFAULT FALSE,
    action_summary      VARCHAR,        -- one-line what the human needs to do
    is_sales            BOOLEAN         DEFAULT FALSE,
    sales_product       VARCHAR,        -- product/service being pitched
    sales_vendor        VARCHAR,        -- vendor org name
    response_status     VARCHAR         DEFAULT 'pending',  -- pending | replied | archived | na
    folder_target       VARCHAR,        -- 受信トレイ | 営業 | 請求 | etc
    dependency_tracks   VARCHAR,        -- comma-separated: track_a | track_b | track_c | hubspot | keiei | vultr | jasa

    -- RLS canonical columns (ADR-0095)
    owner               VARCHAR,
    actor               VARCHAR,
    org_did             VARCHAR,
    sensitivity_ord     INTEGER         DEFAULT 0,

    -- audit
    analyzed_at         TIMESTAMPTZ,
    model_id            VARCHAR,        -- which LLM produced the classification

    PRIMARY KEY (message_id)
);

-- ─── vertex: deduplicated sender profiles ───────────────────────────────────
CREATE TABLE IF NOT EXISTS graphar.vertex_email_sender (
    sender_id           VARCHAR         NOT NULL,   -- hash(lower(address))
    address             VARCHAR         NOT NULL,
    display_name        VARCHAR,
    org_name            VARCHAR,
    org_domain          VARCHAR,
    sender_type         VARCHAR,        -- internal | external_partner | vendor | sales | government | legal_firm | recruitment | system
    trust_level         INTEGER         DEFAULT 50, -- 0-100
    first_seen          TIMESTAMPTZ,
    last_seen           TIMESTAMPTZ,
    owner               VARCHAR,
    org_did             VARCHAR,
    sensitivity_ord     INTEGER         DEFAULT 0,
    PRIMARY KEY (sender_id)
);

-- ─── edge: message → sender ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS graphar.edge_email_sent_by (
    src                 VARCHAR         NOT NULL,   -- message_id
    dst                 VARCHAR         NOT NULL,   -- sender_id
    role                VARCHAR         DEFAULT 'from',  -- from | cc | bcc
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (src, dst, role)
);

-- ─── edge: message → pipeline track dependency ──────────────────────────────
CREATE TABLE IF NOT EXISTS graphar.edge_email_re_track (
    src                 VARCHAR         NOT NULL,   -- message_id
    dst                 VARCHAR         NOT NULL,   -- track id: track_a | track_b | track_c | hubspot | keiei | vultr
    confidence_permille INTEGER         DEFAULT 1000,  -- 0-1000 (no float — ADR guardrail)
    rationale           VARCHAR,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (src, dst)
);

-- ─── indexes ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_email_message_from
    ON graphar.vertex_email_message (from_address, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_message_intent
    ON graphar.vertex_email_message (intent_primary, action_required, response_status);

CREATE INDEX IF NOT EXISTS idx_email_message_sales
    ON graphar.vertex_email_message (is_sales, response_status, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_message_urgency
    ON graphar.vertex_email_message (urgency_score DESC, action_required, response_status);

CREATE INDEX IF NOT EXISTS idx_email_message_thread
    ON graphar.vertex_email_message (thread_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_sender_domain
    ON graphar.vertex_email_sender (org_domain, sender_type);

-- ─── materialized views ─────────────────────────────────────────────────────
-- MV: pending actions ordered by urgency (small cardinality — action_required is rare)
CREATE MATERIALIZED VIEW IF NOT EXISTS graphar.mv_email_pending_action AS
SELECT
    m.message_id,
    m.subject,
    m.from_address,
    m.from_name,
    m.received_at,
    m.intent_primary,
    m.urgency_score,
    m.action_summary,
    m.dependency_tracks,
    m.response_status
FROM graphar.vertex_email_message m
WHERE m.action_required = TRUE
  AND m.response_status = 'pending';

-- MV: sales inbox (small cardinality — is_sales subset only)
CREATE MATERIALIZED VIEW IF NOT EXISTS graphar.mv_email_sales_queue AS
SELECT
    m.message_id,
    m.subject,
    m.from_address,
    m.from_name,
    m.received_at,
    m.sales_product,
    m.sales_vendor,
    m.urgency_score,
    m.response_status
FROM graphar.vertex_email_message m
WHERE m.is_sales = TRUE
  AND m.response_status = 'pending';
