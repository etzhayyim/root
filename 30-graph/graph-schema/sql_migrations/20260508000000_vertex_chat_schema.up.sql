CREATE TABLE IF NOT EXISTS vertex_chat_conversation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      conv_id varchar NOT NULL,
      title varchar,
      agent_did varchar NOT NULL,
      model_hint varchar,
      tier_hint varchar,
      visibility varchar NOT NULL,
      message_count int,
      last_message_at varchar,
      pinned boolean,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_message (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      conv_id varchar NOT NULL,
      msg_id varchar NOT NULL,
      role varchar NOT NULL,
      content varchar,
      tool_calls_json varchar,
      tool_call_id varchar,
      parent_msg_id varchar,
      ts_ms bigint NOT NULL,
      model_used varchar,
      prompt_tokens int,
      completion_tokens int,
      total_tokens int,
      finish_reason varchar,
      embedding real[],
      embedding_model varchar,
      embedding_norm double precision,
      ivf_cluster_id int,
      indexed_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_tool_invocation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      conv_id varchar NOT NULL,
      msg_id varchar NOT NULL,
      tool_call_id varchar NOT NULL,
      tool_name varchar NOT NULL,
      args_json varchar,
      result_summary varchar,
      result_byte_size int,
      duration_ms int,
      ts_ms bigint NOT NULL,
      side_effect_xrpc_uri varchar,
      side_effect_run_id varchar,
      error_code varchar,
      error_message varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_artifact (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      conv_id varchar NOT NULL,
      msg_id varchar,
      artifact_id varchar NOT NULL,
      kind varchar NOT NULL,
      mime_type varchar NOT NULL,
      byte_size bigint NOT NULL,
      sha256 varchar,
      b2_bucket varchar NOT NULL,
      b2_key varchar NOT NULL,
      title varchar,
      description varchar,
      prompt varchar,
      visibility varchar NOT NULL,
      ts_ms bigint NOT NULL,
      expires_at varchar,
      gc_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_checkpoint (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      thread_id varchar NOT NULL,
      checkpoint_id varchar NOT NULL,
      parent_checkpoint_id varchar,
      checkpoint_ns varchar,
      channel_versions_json varchar,
      channel_values_json varchar,
      pending_writes_json varchar,
      ts_ms bigint NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_memory (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      memory_id varchar NOT NULL,
      agent_did varchar NOT NULL,
      memory_kind varchar NOT NULL,
      content varchar,
      content_summary varchar,
      embedding real[],
      embedding_model varchar,
      embedding_norm double precision,
      ivf_cluster_id int,
      importance_score double precision,
      decay_at varchar,
      last_accessed_at varchar,
      access_count int,
      source_conv_id varchar,
      source_msg_id varchar,
      ts_ms bigint NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_chat_session (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      session_id varchar NOT NULL,
      ip_hash varchar,
      ua_hash varchar,
      country varchar,
      first_seen_at varchar NOT NULL,
      last_seen_at varchar NOT NULL,
      message_count int,
      conversation_count int,
      rate_limit_bucket varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_chat_message_in_conversation (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      conv_id varchar NOT NULL,
      msg_id varchar NOT NULL,
      seq int,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_chat_message_replies_to (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_chat_artifact_from_message (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_chat_invocation_from_message (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chat_recent_conversations AS
      SELECT
        owner_did,
        conv_id,
        title,
        agent_did,
        model_hint,
        message_count,
        last_message_at,
        status,
        created_at
      FROM vertex_chat_conversation
      WHERE status IN ('active', 'archived');

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chat_artifact_size_per_owner AS
      SELECT
        owner_did,
        kind,
        COUNT(*) AS artifact_count,
        SUM(byte_size) AS total_bytes
      FROM vertex_chat_artifact
      WHERE status = 'active'
      GROUP BY owner_did, kind;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chat_active_24h AS
      SELECT
        c.owner_did,
        c.conv_id,
        c.title,
        COUNT(m.vertex_id) AS msg_count_24h,
        MAX(m.ts_ms) AS last_msg_ts_ms
      FROM vertex_chat_conversation c
      JOIN vertex_chat_message m ON m.conv_id = c.conv_id
      WHERE c.status = 'active'
        AND m.status = 'active'
        AND to_timestamp(m.ts_ms / 1000.0) > now() - INTERVAL '24 hours'
      GROUP BY c.owner_did, c.conv_id, c.title;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_conversation         TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_conversation         TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_message              TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_message              TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_tool_invocation      TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_tool_invocation      TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_artifact             TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_artifact             TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_checkpoint           TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_checkpoint           TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_memory               TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_memory               TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_session              TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_chat_session              TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_chat_message_in_conversation TO root;

GRANT SELECT, INSERT, UPDATE ON edge_chat_message_in_conversation TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_chat_message_replies_to     TO root;

GRANT SELECT, INSERT, UPDATE ON edge_chat_message_replies_to     TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_chat_artifact_from_message  TO root;

GRANT SELECT, INSERT, UPDATE ON edge_chat_artifact_from_message  TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_chat_invocation_from_message TO root;

GRANT SELECT, INSERT, UPDATE ON edge_chat_invocation_from_message TO kaisya_app;
