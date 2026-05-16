import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: C
// Ameno browser WebGPU inference result. ADR-2605111200 persistence target.
// Worker → bpmn-dispatcher → AgentGateway MCP → ameno-langserver pod →
// INSERT INTO vertex_ameno_inferenceresult.
//
// SUPERSEDED by Alembic revision (Phase 5i):
//   30-graph/graph-schema/alembic/current_versions/r_20260515031000_vertex_ameno_inferenceresult.py
//   30-graph/graph-schema/sql_migrations/20260515031000_vertex_ameno_inferenceresult.{up,down}.sql
// This file is kept as historical lineage per `30-graph/graph-schema/CLAUDE.md`
// (legacy Kysely directory: do not add new graph-schema DDL here).
// Do not replay this file into the live cluster — `pnpm db:migrate` runs the
// Alembic revision instead.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ameno_inferenceresult (
      vertex_id VARCHAR PRIMARY KEY,
      result_id VARCHAR,
      model_id VARCHAR NOT NULL,
      lora_adapters VARCHAR,
      prompt VARCHAR,
      output VARCHAR,
      prompt_tokens BIGINT,
      output_tokens BIGINT,
      elapsed_ms BIGINT,
      tokens_per_sec BIGINT,
      webgpu_adapter VARCHAR,
      rag_context_used BOOLEAN,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_ameno_inferenceresult`.execute(db);
}
