import type { Kysely } from "kysely";

export async function up(_db: Kysely<unknown>): Promise<void> {
  // Intentionally empty: verifies rw_admin + wrapper + ledger path.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Intentionally empty.
}
