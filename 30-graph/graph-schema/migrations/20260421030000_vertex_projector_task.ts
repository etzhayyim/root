import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_projector_task — dedicated table for app.etzhayyim.projector.addConvoTask
 * / completeConvoTask / listConvoTasks (ADR-0036 Phase 2).
 *
 * Previously the handler wrote an app.etzhayyim.projectorTask AT record that
 * had no graph-worker consumer, so task CRUD was silently no-op. The
 * read path (listConvoTasks) queried vertex_project_props — the same
 * table used for projects — which would cross-contaminate projects and
 * tasks once direct writes landed. Splitting tasks off cleanly avoids
 * retrofitting `WHERE label = 'Project'` filters on the 14 existing
 * project-read sites.
 *
 * Columns:
 *   Standard 7: vertex_id / _seq / created_date / sensitivity_ord /
 *               owner_did / rkey / repo
 *   Task body:  convo_id / title / status / priority / assignee_did /
 *               due_date / completed_by / completed_at / created_by
 *   RLS 4:      created_at / org_id / user_id / actor_id
 *
 * Index (convo_id, status) drives listConvoTasks's hot path where the
 * status filter narrows the per-convo list.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_task (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      convo_id VARCHAR, title VARCHAR, status VARCHAR, priority VARCHAR,
      assignee_did VARCHAR, due_date VARCHAR,
      completed_by VARCHAR, completed_at VARCHAR, created_by VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_projector_task_convo_status
            ON vertex_projector_task (convo_id, status)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_projector_task_convo_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_task`.execute(db);
}
