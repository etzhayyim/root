CREATE TABLE IF NOT EXISTS "vertex_meetingrecorder_session" (
      "vertex_id"           VARCHAR PRIMARY KEY,
      "_seq"                BIGINT,
      "session_id"          VARCHAR,
      "session_did"         VARCHAR,
      "provider"            VARCHAR NOT NULL,
      "external_meeting_id" VARCHAR,
      "on_behalf_of_did"    VARCHAR,
      "organizer_hint"      VARCHAR,
      "consent_jwt_hash"    VARCHAR,
      "status"              VARCHAR,
      "record_audio"        BOOLEAN,
      "record_video"        BOOLEAN,
      "transcribe"          BOOLEAN,
      "chunk_seconds"       BIGINT,
      "display_name"        VARCHAR,
      "started_at"          TIMESTAMPTZ,
      "ended_at"            TIMESTAMPTZ,
      "duration_ms"         BIGINT,
      "leave_reason"        VARCHAR,
      "error"               TEXT,
      "created_at"          TIMESTAMPTZ DEFAULT NOW(),
      "updated_at"          TIMESTAMPTZ DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS idx_mrec_session_obo ON "vertex_meetingrecorder_session" (on_behalf_of_did, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_mrec_session_provider ON "vertex_meetingrecorder_session" (provider, status);

CREATE INDEX IF NOT EXISTS idx_mrec_session_ext ON "vertex_meetingrecorder_session" (provider, external_meeting_id);

CREATE TABLE IF NOT EXISTS "vertex_meetingrecorder_chunk" (
      "vertex_id"    VARCHAR PRIMARY KEY,
      "_seq"         BIGINT,
      "session_did"  VARCHAR NOT NULL,
      "provider"     VARCHAR NOT NULL,
      "seq"          BIGINT NOT NULL,
      "kind"         VARCHAR NOT NULL,
      "codec"        VARCHAR,
      "b2_bucket"    VARCHAR,
      "b2_key"       VARCHAR NOT NULL,
      "sha256"       VARCHAR,
      "size_bytes"   BIGINT,
      "started_at"   TIMESTAMPTZ,
      "duration_ms"  BIGINT,
      "created_at"   TIMESTAMPTZ DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS idx_mrec_chunk_session_seq ON "vertex_meetingrecorder_chunk" (session_did, seq);

CREATE TABLE IF NOT EXISTS "vertex_meetingrecorder_participant" (
      "vertex_id"           VARCHAR PRIMARY KEY,
      "_seq"                BIGINT,
      "session_did"         VARCHAR NOT NULL,
      "provider_id_hash"    VARCHAR NOT NULL,
      "participant_did"     VARCHAR,
      "display_name_cipher" TEXT,
      "role"                VARCHAR,
      "joined_at"           TIMESTAMPTZ,
      "left_at"             TIMESTAMPTZ,
      "speaking_ms"         BIGINT,
      "created_at"          TIMESTAMPTZ DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS idx_mrec_part_session ON "vertex_meetingrecorder_participant" (session_did);

CREATE INDEX IF NOT EXISTS idx_mrec_part_did ON "vertex_meetingrecorder_participant" (participant_did);

CREATE TABLE IF NOT EXISTS "vertex_meetingrecorder_transcript_seg" (
      "vertex_id"      VARCHAR PRIMARY KEY,
      "_seq"           BIGINT,
      "session_did"    VARCHAR NOT NULL,
      "chunk_seq"      BIGINT,
      "seq"            BIGINT NOT NULL,
      "started_at_ms"  BIGINT,
      "ended_at_ms"    BIGINT,
      "speaker_hash"   VARCHAR,
      "lang"           VARCHAR,
      "confidence"     DOUBLE PRECISION,
      "text_cipher"    TEXT NOT NULL,
      "model"          VARCHAR,
      "created_at"     TIMESTAMPTZ DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS idx_mrec_trans_session_seq ON "vertex_meetingrecorder_transcript_seg" (session_did, seq);

CREATE TABLE IF NOT EXISTS "edge_meetingrecorder_attended" (
      "edge_id"       VARCHAR PRIMARY KEY,
      "_seq"          BIGINT,
      "src_vid"       VARCHAR NOT NULL,
      "dst_vid"       VARCHAR NOT NULL,
      "provider"      VARCHAR,
      "joined_at"     TIMESTAMPTZ,
      "left_at"       TIMESTAMPTZ,
      "speaking_ms"   BIGINT,
      "created_at"    TIMESTAMPTZ DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS idx_mrec_edge_src ON "edge_meetingrecorder_attended" (src_vid);

CREATE INDEX IF NOT EXISTS idx_mrec_edge_dst ON "edge_meetingrecorder_attended" (dst_vid);
