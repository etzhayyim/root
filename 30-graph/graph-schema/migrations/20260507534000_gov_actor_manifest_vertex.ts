import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_actor_manifest (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      path VARCHAR NOT NULL,
      country VARCHAR NOT NULL,
      display_name VARCHAR,
      description TEXT,
      performer_type VARCHAR,
      agent_type VARCHAR,
      is_bot BOOLEAN NOT NULL DEFAULT true,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    )
  `.execute(db);

  const oldTable = await sql<{ exists: boolean }>`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = current_schema()
        AND table_name = 'vertex_gov_record'
    ) AS exists
  `.execute(db);

  if (oldTable.rows[0]?.exists) {
    await sql`
      INSERT INTO vertex_gov_actor_manifest (
        vertex_id, record_key, record_kind, path, country, display_name,
        description, performer_type, agent_type, is_bot, value_json,
        indexed_at, created_at, updated_at, actor_did, org_did, owner_did,
        sensitivity_ord
      )
      SELECT
        vertex_id,
        record_key,
        record_kind,
        COALESCE(value_json::jsonb ->> 'path', ''),
        COALESCE(value_json::jsonb ->> 'country', ''),
        value_json::jsonb ->> 'displayName',
        value_json::jsonb ->> 'description',
        value_json::jsonb ->> 'performerType',
        value_json::jsonb ->> 'agentType',
        COALESCE((value_json::jsonb ->> 'isBot')::boolean, true),
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer)
      FROM vertex_gov_record
      WHERE record_kind = 'actorManifest'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gov_actor_manifest_owner_path
      ON vertex_gov_actor_manifest (owner_did, path)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gov_actor_manifest_actor
      ON vertex_gov_actor_manifest (actor_did, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_actor_manifest_coverage AS
    SELECT
      owner_did,
      country,
      COUNT(*) AS actor_count,
      MAX(indexed_at) AS latest_indexed_at
    FROM vertex_gov_actor_manifest
    GROUP BY owner_did, country
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist =
      CASE
        WHEN write_table_allowlist LIKE '%vertex_gov_actor_manifest%' THEN write_table_allowlist
        ELSE write_table_allowlist || ',vertex_gov_actor_manifest'
      END
    WHERE actor_id LIKE 'gov-%'
      AND write_table_allowlist IS NOT NULL
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_actor_manifest_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_actor_manifest`.execute(db);
}
