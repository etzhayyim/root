import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations.
// tier: B  (conversation thread + turn — message text may include user PII
//          like address/phone if the agent collected them, but the agent
//          policy redirects PII to T3 Preferences; the conversation table
//          stores only the redacted summary. Raw turns are kept for replay
//          and for LangGraph checkpoint, with sensitivity_ord=1.)

/**
 * otakiage.gftd.ai Phase 2 — conversational agent state schema
 * (ADR-2605081700 + ADR-2605072000 LangGraph + ADR-2605080200 Pydantic L6).
 *
 * Tables (2 vertex):
 *   vertex_otakiage_conversation       会話 thread (1 caller_did : N turn)
 *   vertex_otakiage_conversation_turn  個別の turn (user message + agent reply + intent + action_json)
 *
 * Streaming MV (1):
 *   mv_otakiage_conversation_recent    直近 24h の active conversation
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_conversation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      thread_id varchar NOT NULL,
      caller_did varchar NOT NULL,
      title varchar,
      turn_count int,
      last_intent varchar,
      last_message_at varchar,
      state varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_otakiage_conversation_turn (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      turn_id varchar NOT NULL,
      thread_id varchar NOT NULL,
      thread_uri varchar NOT NULL,
      caller_did varchar NOT NULL,
      turn_index int NOT NULL,
      user_message varchar NOT NULL,
      agent_reply varchar,
      intent varchar,
      actions_json varchar,
      llm_calls int,
      latency_ms int,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // Streaming MV — active conversation rows; consumer applies 24h window at query time.
  // Cardinality bounded by daily caller count × ~10 turns; safe per MV memory guardrails.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_otakiage_conversation_recent AS
      SELECT
        vertex_id,
        thread_id,
        caller_did,
        turn_count,
        last_intent,
        last_message_at,
        state,
        created_at
      FROM vertex_otakiage_conversation
      WHERE state = 'active';
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_conversation       TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_conversation       TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_conversation_turn  TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_otakiage_conversation_turn  TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_otakiage_conversation_recent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_conversation_turn`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_otakiage_conversation`.execute(db);
}
