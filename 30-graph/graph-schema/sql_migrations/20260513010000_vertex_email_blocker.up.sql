-- migration: 20260513010000_vertex_email_blocker (UP)
-- Blocker-aware email workflow schema.
-- Linked to vertex_email_message (pregel migration 20260512100000).
-- RisingWave constraints: no FK, no ON CONFLICT, varchar cols, integer permille.

-- Blocker registry: one row per blocker instance detected on an email action.
CREATE TABLE IF NOT EXISTS graphar.vertex_email_blocker (
    blocker_id          VARCHAR     NOT NULL,   -- sha256[:24] of message_id + blocker_type
    email_message_id    VARCHAR     NOT NULL,   -- FK-intent → vertex_email_message.message_id
    blocker_type        VARCHAR     NOT NULL,   -- financial|personnel|approval|system|external
    description         VARCHAR     NOT NULL,   -- human-readable reason
    detected_at         TIMESTAMPTZ NOT NULL,
    resolved_at         TIMESTAMPTZ,            -- NULL = unresolved
    resolution_note     VARCHAR,
    acknowledgment_sent BOOLEAN     NOT NULL DEFAULT FALSE,
    acknowledgment_draft_id VARCHAR,            -- Outlook draftId if ack was drafted
    follow_up_at        TIMESTAMPTZ,            -- scheduled re-check time
    -- RLS canonical columns (ADR-0095)
    owner               VARCHAR     NOT NULL,
    actor               VARCHAR     NOT NULL DEFAULT 'did:web:pregel.etzhayyim.com',
    org_did             VARCHAR     NOT NULL DEFAULT 'did:web:etzhayyim.com',
    sensitivity_ord     INTEGER     NOT NULL DEFAULT 0
) WITH (appendonly = false);

CREATE INDEX IF NOT EXISTS idx_email_blocker_message
    ON graphar.vertex_email_blocker (email_message_id);
CREATE INDEX IF NOT EXISTS idx_email_blocker_type
    ON graphar.vertex_email_blocker (blocker_type);
CREATE INDEX IF NOT EXISTS idx_email_blocker_unresolved
    ON graphar.vertex_email_blocker (detected_at)
    WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_email_blocker_followup
    ON graphar.vertex_email_blocker (follow_up_at)
    WHERE resolved_at IS NULL;

-- Edge: email_message → blocker
CREATE TABLE IF NOT EXISTS graphar.edge_email_blocked_by (
    src         VARCHAR     NOT NULL,   -- email_message_id
    dst         VARCHAR     NOT NULL,   -- blocker_id
    created_at  TIMESTAMPTZ NOT NULL
) WITH (appendonly = true);

CREATE INDEX IF NOT EXISTS idx_edge_email_blocked_by_src
    ON graphar.edge_email_blocked_by (src);

-- MV: unresolved blockers with email subject (narrow cardinality, MV-memory-safe)
CREATE MATERIALIZED VIEW IF NOT EXISTS graphar.mv_email_blocker_pending AS
SELECT
    b.blocker_id,
    b.email_message_id,
    b.blocker_type,
    b.description,
    b.detected_at,
    b.follow_up_at,
    b.acknowledgment_sent,
    m.subject,
    m.from_address,
    m.urgency_score
FROM graphar.vertex_email_blocker b
JOIN graphar.vertex_email_message  m ON b.email_message_id = m.message_id
WHERE b.resolved_at IS NULL;

-- MV: count of unresolved blockers by type (dashboard use)
CREATE MATERIALIZED VIEW IF NOT EXISTS graphar.mv_email_blocker_count_by_type AS
SELECT
    blocker_type,
    COUNT(*) AS unresolved_count,
    MAX(detected_at) AS latest_detected
FROM graphar.vertex_email_blocker
WHERE resolved_at IS NULL
GROUP BY blocker_type;
