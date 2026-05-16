CREATE TABLE IF NOT EXISTS vertex_fukkou_diet_speech (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      speech_id         VARCHAR,
      meeting_url       VARCHAR,
      issue_id          VARCHAR,
      session           VARCHAR,
      chamber           VARCHAR,
      committee_name    VARCHAR,
      meeting_date      DATE,
      speech_order      INTEGER,
      speaker_name      VARCHAR,
      speaker_yomi      VARCHAR,
      speaker_group     VARCHAR,
      speaker_position  VARCHAR,
      speaker_role      VARCHAR,
      speech_text       VARCHAR,
      speech_length     INTEGER,
      topic_tag         VARCHAR,
      sentiment         VARCHAR,
      created_at        TIMESTAMP WITH TIME ZONE,
      llm_topic         VARCHAR,
      llm_position      VARCHAR,
      llm_commitment    VARCHAR,
      llm_summary       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_diet_speech_committee ON vertex_fukkou_diet_speech (committee_name, meeting_date);

CREATE INDEX IF NOT EXISTS idx_diet_speech_session ON vertex_fukkou_diet_speech (session, chamber, meeting_date);

CREATE INDEX IF NOT EXISTS idx_diet_speech_speaker ON vertex_fukkou_diet_speech (speaker_name, speaker_group);
