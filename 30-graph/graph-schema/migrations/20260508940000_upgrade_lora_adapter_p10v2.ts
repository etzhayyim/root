import type { Kysely } from "kysely";
import { sql } from "kysely";

// Upgrade vertex_lora_adapter to P10v2 typed columns (ADR-0036).
// Adds B2 weight storage fields + adapter metadata.
// Drops value_json anti-pattern after backfill (value_json kept nullable for grace period).
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_b2_uri     VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_byte_size  BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_sha256     VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS base_model        VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_rank      INTEGER`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_alpha     DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_format    VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS display_name_yomi VARCHAR`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_owner_did    ON vertex_lora_adapter (owner_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_base_model   ON vertex_lora_adapter (base_model)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_weight_b2    ON vertex_lora_adapter (weight_b2_uri)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS display_name_yomi`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_format`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_alpha`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_rank`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS base_model`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_sha256`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_byte_size`.execute(db);
  await sql`ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_b2_uri`.execute(db);
}
