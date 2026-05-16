import { Kysely, sql } from 'kysely';

/**
 * ALTER vertex_bpmn_process + vertex_bpmn_instance to add the BPMN executor
 * (Phase 5b) columns. These tables pre-existed with a different schema
 * (process_key / version_tag / did / process_did / instance_key etc.) used
 * by the original BPMN registry design. The Phase 5b executor emits
 * records with {processId, instanceId, xmlR2Key, ...} which the graph
 * worker auto-routes to the same tables; without these columns the
 * projection silently drops the record.
 *
 * Additive-only — pre-existing columns + consumers stay intact.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // vertex_bpmn_process
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS process_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS xml_r2_key VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS json_r2_key VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS xsd_valid VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deployed_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deployed_by VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deprecated VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS org_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS user_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS actor_id VARCHAR`.execute(db);

  // vertex_bpmn_instance
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS instance_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS process_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS state VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS variables_json VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS current_token_json VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS correlation_key VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS started_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS completed_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS error_code VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS waiting_json VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS org_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS user_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS actor_id VARCHAR`.execute(db);
}

export async function down(_db: Kysely<any>): Promise<void> {
  // ALTER DROP is non-destructive revert but RisingWave drop support is limited; leave no-op.
}
