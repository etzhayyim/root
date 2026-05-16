import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_process_event (
      vertex_id         varchar PRIMARY KEY,
      run_vertex_id     varchar NOT NULL,
      work_id           varchar,
      activity          varchar NOT NULL,
      task_type         varchar NOT NULL,
      lifecycle         varchar NOT NULL,
      status            varchar NOT NULL,
      event_at          varchar NOT NULL,
      duration_ms       bigint,
      artifact_cid      varchar,
      detail_json       varchar,
      sensitivity_ord   int NOT NULL DEFAULT 1,
      owner_did         varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_pd_color_process_event_run
      ON vertex_pd_color_process_event (run_vertex_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_pd_color_process_event_activity
      ON vertex_pd_color_process_event (activity)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_pd_color_process_event_at
      ON vertex_pd_color_process_event (event_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_pd_color_process_event`.execute(db);
}
