CREATE TABLE IF NOT EXISTS vertex_os_messaging_open_channel (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      platform         VARCHAR,
      channel_id       VARCHAR,
      channel_url      VARCHAR,
      title            VARCHAR,
      description      VARCHAR,
      country          VARCHAR,
      language         VARCHAR,
      first_seen_at    VARCHAR,
      last_seen_at     VARCHAR,
      source_url       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_osmsg_open_channel_platform_id ON vertex_os_messaging_open_channel (platform, channel_id);

CREATE INDEX IF NOT EXISTS idx_osmsg_open_channel_seen ON vertex_os_messaging_open_channel (last_seen_at);

CREATE TABLE IF NOT EXISTS vertex_os_messaging_open_message (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      platform           VARCHAR,
      channel_vertex_id  VARCHAR,
      channel_id         VARCHAR,
      platform_message_id VARCHAR,
      author_label       VARCHAR,
      message_text       VARCHAR,
      message_url        VARCHAR,
      published_at       VARCHAR,
      observed_at        VARCHAR,
      source_url         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_osmsg_open_message_channel ON vertex_os_messaging_open_message (channel_vertex_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_osmsg_open_message_platform_id ON vertex_os_messaging_open_message (platform, platform_message_id);

CREATE TABLE IF NOT EXISTS vertex_os_messaging_open_scraper_run (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      platform        VARCHAR,
      channel_id      VARCHAR,
      channel_url     VARCHAR,
      country         VARCHAR,
      language        VARCHAR,
      started_at      VARCHAR,
      finished_at     VARCHAR,
      status          VARCHAR,
      messages_seen   BIGINT,
      messages_new    BIGINT,
      error_message   VARCHAR,
      user_agent      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_osmsg_open_run_started ON vertex_os_messaging_open_scraper_run (platform, started_at);
