CREATE TABLE IF NOT EXISTS vertex_houbun_statute (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      jurisdiction VARCHAR,
      statute_id VARCHAR,
      title VARCHAR,
      title_native VARCHAR,
      statute_type VARCHAR,
      enacted_date VARCHAR,
      effective_date VARCHAR,
      repealed_date VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      license VARCHAR,
      language VARCHAR,
      article_count BIGINT,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_houbun_statute_jurisdiction
      ON vertex_houbun_statute (jurisdiction);

CREATE INDEX IF NOT EXISTS idx_houbun_statute_statute_id
      ON vertex_houbun_statute (jurisdiction, statute_id);

CREATE INDEX IF NOT EXISTS idx_houbun_statute_source
      ON vertex_houbun_statute (source);

CREATE TABLE IF NOT EXISTS vertex_houbun_article (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      statute_ref VARCHAR,
      article_no VARCHAR,
      section VARCHAR,
      title VARCHAR,
      text VARCHAR,
      language VARCHAR,
      article_did VARCHAR,
      blake3_hash VARCHAR,
      amended_at VARCHAR,
      source_url VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_houbun_article_statute_ref
      ON vertex_houbun_article (statute_ref);

CREATE INDEX IF NOT EXISTS idx_houbun_article_did
      ON vertex_houbun_article (article_did);

CREATE TABLE IF NOT EXISTS vertex_houbun_amendmentEvent (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      statute_ref VARCHAR,
      article_ref VARCHAR,
      supersedes_article_did VARCHAR,
      op VARCHAR,
      amending_statute_ref VARCHAR,
      effective_date VARCHAR,
      diff_uri VARCHAR,
      note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_houbun_amendment_statute_ref
      ON vertex_houbun_amendmentEvent (statute_ref);

CREATE INDEX IF NOT EXISTS idx_houbun_amendment_supersedes
      ON vertex_houbun_amendmentEvent (supersedes_article_did);

CREATE TABLE IF NOT EXISTS vertex_houbun_treaty (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      title VARCHAR,
      title_native VARCHAR,
      parties_json VARCHAR,
      signed_date VARCHAR,
      entered_into_force_date VARCHAR,
      un_reg_no VARCHAR,
      depositary VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      source_url VARCHAR,
      language VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_houbun_treaty_source_record_id
      ON vertex_houbun_treaty (source, source_record_id);

CREATE TABLE IF NOT EXISTS edge_houbun_statute_article (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      article_no VARCHAR,
      order_key BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_houbun_statute_article_src
      ON edge_houbun_statute_article (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_houbun_statute_article_dst
      ON edge_houbun_statute_article (dst_vid);

CREATE TABLE IF NOT EXISTS edge_houbun_amends (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      op VARCHAR,
      effective_date VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_houbun_amends_src
      ON edge_houbun_amends (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_houbun_amends_dst
      ON edge_houbun_amends (dst_vid);
