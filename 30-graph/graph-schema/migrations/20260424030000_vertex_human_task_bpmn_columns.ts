/**
 * ADR-0056 — typed BPMN correlation columns on vertex_human_task.
 *
 * The user_task_sink (20-actors/magatama/py/src/pymagatama/handlers/user_task_sink.py)
 * currently stuffs Zeebe correlation keys into overloaded string columns:
 *   - task_code        = "zeebe:{jobKey}"           (parsed by kaisya completeTask)
 *   - related_project  = "{processInstanceKey}"     (stringified int)
 *   - task_type        = "bpmn:{elementId}"         (prefix-stripped by UI)
 *   - result_data      = JSON blob (formKey, candidateGroups, variables, ...)
 *
 * That works for MVP but the overloads are fragile — `related_project` already
 * carries human project refs for non-BPMN rows, and the string prefixes bypass
 * typed indexing. This migration adds 5 typed columns so the sink, the kaisya
 * completeTask XRPC, and any future tasklist consumer can query directly:
 *
 *   zeebe_job_key              BIGINT         — broker job id, primary Zeebe handle
 *   bpmn_process_instance_key  BIGINT         — Zeebe process instance id
 *   bpmn_process_definition_key BIGINT        — deployed BPMN key (join to vertex_bpmn_process_def.deployed_zeebe_key)
 *   bpmn_process_id            VARCHAR        — logical process id, e.g. "kaisya_start_legal_case"
 *   bpmn_element_id            VARCHAR        — BPMN activity id, e.g. "Task_CLOTriage"
 *   form_key                   VARCHAR        — Camunda Forms key, e.g. "embedded:app:forms/legal-case.form.json"
 *
 * Plus one index (`zeebe_job_key`) to let CompleteJob-style callers do an
 * O(log n) lookup by job id.
 *
 * The string overloads are kept as write targets during a grace period — the
 * next sink release can switch to typed-only writes once clients have
 * migrated. No data migration here: existing rows pre-date Zeebe and aren't
 * affected.
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    ALTER TABLE vertex_human_task
      ADD COLUMN IF NOT EXISTS zeebe_job_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_instance_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_definition_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_id VARCHAR,
      ADD COLUMN IF NOT EXISTS bpmn_element_id VARCHAR,
      ADD COLUMN IF NOT EXISTS form_key VARCHAR
  `.execute(db);

  // Hot path: user_task_sink UPDATE-on-complete looks up by jobKey.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_human_task_zeebe_job_key
      ON vertex_human_task (zeebe_job_key)
      WHERE zeebe_job_key IS NOT NULL
  `.execute(db);

  // Inbox filtering by process also helps the /workflow UI.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_human_task_bpmn_process_instance
      ON vertex_human_task (bpmn_process_instance_key)
      WHERE bpmn_process_instance_key IS NOT NULL
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_human_task_bpmn_process_instance`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_human_task_zeebe_job_key`.execute(db);
  await sql`
    ALTER TABLE vertex_human_task
      DROP COLUMN IF EXISTS form_key,
      DROP COLUMN IF EXISTS bpmn_element_id,
      DROP COLUMN IF EXISTS bpmn_process_id,
      DROP COLUMN IF EXISTS bpmn_process_definition_key,
      DROP COLUMN IF EXISTS bpmn_process_instance_key,
      DROP COLUMN IF EXISTS zeebe_job_key
  `.execute(db);
}
