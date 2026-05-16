import type { Kysely } from "kysely";

export async function up(_db: Kysely<unknown>): Promise<void> {
  // No-op migration used to re-probe the RisingWave wrapper after DDL cleanup.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op.
}
