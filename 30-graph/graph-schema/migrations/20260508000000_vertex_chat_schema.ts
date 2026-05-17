import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (chat content — message body / artifact metadata are sensitive
//          but not Tier-3 PII; private text columns carry signal:v1: ciphertext
//          per CLAUDE.md field-level encrypt convention)

/**
 * etzhayyim.com chat shell — Phase 1 schema (ADR-0036 + ADR-2604282300 + ADR-0049).
 *
 * Apex chat product (`etzhayyim.com/`) — ChatGPT/Claude.ai-style. Hot path is
 * **HTTP SSE direct** (CF Worker → CF Tunnel → aiohttp pod), not BPMN-as-actor.
 * Side effects + maintenance run as Zeebe BPMN.
 *
 * Tables (7 vertex + 4 edge):
 *   vertex_chat_conversation        thread metadata (owner / agent / model)
 *   vertex_chat_message             per-turn (role / content / embedding for RAG)
 *   vertex_chat_tool_invocation     audit + replay of LangGraph tool calls
 *   vertex_chat_artifact            saved files (image / code output / document) → B2
 *   vertex_chat_checkpoint          LangGraph state save point (pickled channels)
 *   vertex_chat_memory              Path F long-term / working memory (ADR 260413)
 *   vertex_chat_session             anonymous browser session (rate-limit + ephemeral)
 *   edge_chat_message_in_conversation
 *   edge_chat_message_replies_to
 *   edge_chat_artifact_from_message
 *   edge_chat_invocation_from_message
 *
 * Streaming MVs (3):
 *   mv_chat_recent_conversations    per owner_did latest 50 (last_message_at desc)
 *   mv_chat_artifact_size_per_owner B2 quota tracking (sum bytes per owner)
 *   mv_chat_active_24h              active conversations + message counts last 24h
 *
 * Embedding columns (vertex_chat_message.embedding, vertex_chat_memory.embedding)
 * use REAL[] for IVF; index applied separately by site.ivfPq.* maintenance Zeebe
 * task (ADR-0044 SQL UDF strategy). Cardinality: per-user ~100s of conversations
 * × ~20 messages = ~10K rows per active user — well under MV guardrail.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_chat_message_in_conversation (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      conv_id varchar NOT NULL,
      msg_id varchar NOT NULL,
      seq int,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_chat_message_replies_to (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_chat_artifact_from_message (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_chat_invocation_from_message (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────
  // Cardinality: ~10K conversations per active user × ~100 active users < 1M rows. Safe.

  await sql`
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
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chat_artifact_size_per_owner AS
      SELECT
        owner_did,
        kind,
        COUNT(*) AS artifact_count,
        SUM(byte_size) AS total_bytes
      FROM vertex_chat_artifact
      WHERE status = 'active'
      GROUP BY owner_did, kind;
  `.execute(db);

  await sql`
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
  `.execute(db);

  // ── Grants ─────────────────────────────────────────────────────────
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_conversation         TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_conversation         TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_message              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_message              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_tool_invocation      TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_tool_invocation      TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_artifact             TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_artifact             TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_checkpoint           TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_checkpoint           TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_memory               TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_memory               TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_session              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_chat_session              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_message_in_conversation TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_message_in_conversation TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_message_replies_to     TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_message_replies_to     TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_artifact_from_message  TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_artifact_from_message  TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_invocation_from_message TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_chat_invocation_from_message TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_chat_active_24h`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_chat_artifact_size_per_owner`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_chat_recent_conversations`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_chat_invocation_from_message`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_chat_artifact_from_message`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_chat_message_replies_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_chat_message_in_conversation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_session`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_memory`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_checkpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_tool_invocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_message`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_chat_conversation`.execute(db);
}
