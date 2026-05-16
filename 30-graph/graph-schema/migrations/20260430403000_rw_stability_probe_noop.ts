import type { Kysely } from "kysely";

export async function up(_db: Kysely<unknown>): Promise<void> {
  // No-op migration used to verify the RisingWave single-migration wrapper.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op.
}
