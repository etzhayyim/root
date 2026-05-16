import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Hazelcast→RisingWave bridge sequence position.
  // One row per ringbuffer name; stores the next sequence to read from.
  await db.schema
    .createTable("vertex_zeebe_seq_pos")
    .ifNotExists()
    .addColumn("ringbuffer_name", "varchar", (c) => c.notNull())
    .addColumn("next_seq", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("updated_at", "varchar", (c) => c.notNull().defaultTo(""))
    .addPrimaryKeyConstraint("vertex_zeebe_seq_pos_pkey", ["ringbuffer_name"])
    .execute();

  // Process definitions from Zeebe PROCESS records.
  // PK = process_definition_key; RisingWave implicit upsert overwrites on re-deploy.
  await db.schema
    .createTable("vertex_zeebe_process")
    .ifNotExists()
    .addColumn("process_definition_key", "bigint", (c) => c.notNull())
    .addColumn("bpmn_process_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("version", "integer", (c) => c.notNull().defaultTo(0))
    .addColumn("resource_name", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("intent", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("event_time_ms", "bigint", (c) => c.notNull().defaultTo(0))
    .addPrimaryKeyConstraint("vertex_zeebe_process_pkey", ["process_definition_key"])
    .execute();

  // Process instance events (append-only: one row per instance × intent).
  // PK = (process_instance_key, intent) so ELEMENT_ACTIVATING and
  // ELEMENT_COMPLETED for the same instance are separate rows.
  // Only ROOT-level events (bpmnElementType = PROCESS) are stored here.
  await db.schema
    .createTable("vertex_zeebe_instance")
    .ifNotExists()
    .addColumn("process_instance_key", "bigint", (c) => c.notNull())
    .addColumn("intent", "varchar", (c) => c.notNull())
    .addColumn("event_time_ms", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("bpmn_process_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("process_definition_key", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("bpmn_element_type", "varchar", (c) => c.notNull().defaultTo(""))
    .addPrimaryKeyConstraint("vertex_zeebe_instance_pkey", [
      "process_instance_key",
      "intent",
    ])
    .execute();

  // Job events (append-only: one row per job_key × intent).
  await db.schema
    .createTable("vertex_zeebe_job")
    .ifNotExists()
    .addColumn("job_key", "bigint", (c) => c.notNull())
    .addColumn("intent", "varchar", (c) => c.notNull())
    .addColumn("event_time_ms", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("job_type", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("process_instance_key", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("bpmn_process_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("element_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("retries", "integer", (c) => c.notNull().defaultTo(0))
    .addColumn("error_message", "varchar", (c) => c.notNull().defaultTo(""))
    .addPrimaryKeyConstraint("vertex_zeebe_job_pkey", ["job_key", "intent"])
    .execute();

  // Incident events (append-only: one row per incident_key × intent).
  await db.schema
    .createTable("vertex_zeebe_incident")
    .ifNotExists()
    .addColumn("incident_key", "bigint", (c) => c.notNull())
    .addColumn("intent", "varchar", (c) => c.notNull())
    .addColumn("event_time_ms", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("error_type", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("error_message", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("bpmn_process_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("process_instance_key", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("element_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("job_key", "bigint", (c) => c.notNull().defaultTo(0))
    .addPrimaryKeyConstraint("vertex_zeebe_incident_pkey", [
      "incident_key",
      "intent",
    ])
    .execute();

  // Message events (one row per message_key × intent).
  await db.schema
    .createTable("vertex_zeebe_message")
    .ifNotExists()
    .addColumn("message_key", "bigint", (c) => c.notNull())
    .addColumn("intent", "varchar", (c) => c.notNull())
    .addColumn("event_time_ms", "bigint", (c) => c.notNull().defaultTo(0))
    .addColumn("message_name", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("correlation_key", "varchar", (c) => c.notNull().defaultTo(""))
    .addPrimaryKeyConstraint("vertex_zeebe_message_pkey", [
      "message_key",
      "intent",
    ])
    .execute();

  // --- Materialized Views ---

  // Instance summary per BPMN process.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_zeebe_instance_summary AS
    SELECT
      bpmn_process_id,
      SUM(CASE WHEN intent = 'ELEMENT_ACTIVATING'  THEN 1 ELSE 0 END) AS started_count,
      SUM(CASE WHEN intent = 'ELEMENT_COMPLETED'   THEN 1 ELSE 0 END) AS completed_count,
      SUM(CASE WHEN intent = 'ELEMENT_TERMINATED'  THEN 1 ELSE 0 END) AS terminated_count
    FROM vertex_zeebe_instance
    WHERE bpmn_element_type = 'PROCESS'
    GROUP BY bpmn_process_id
  `.execute(db);

  // Incident summary per BPMN process (open = created - resolved).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_zeebe_incident_summary AS
    SELECT
      bpmn_process_id,
      SUM(CASE WHEN intent = 'CREATED'  THEN 1 ELSE 0 END) AS created_count,
      SUM(CASE WHEN intent = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count
    FROM vertex_zeebe_incident
    GROUP BY bpmn_process_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_zeebe_incident_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_zeebe_instance_summary`.execute(db);
  await db.schema.dropTable("vertex_zeebe_message").ifExists().execute();
  await db.schema.dropTable("vertex_zeebe_incident").ifExists().execute();
  await db.schema.dropTable("vertex_zeebe_job").ifExists().execute();
  await db.schema.dropTable("vertex_zeebe_instance").ifExists().execute();
  await db.schema.dropTable("vertex_zeebe_process").ifExists().execute();
  await db.schema.dropTable("vertex_zeebe_seq_pos").ifExists().execute();
}
