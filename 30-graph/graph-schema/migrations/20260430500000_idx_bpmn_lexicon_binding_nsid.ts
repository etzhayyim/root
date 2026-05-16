import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bpmn_lexicon_binding_nsid ON public.vertex_bpmn_lexicon_binding(nsid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_bpmn_lexicon_binding_nsid`.execute(db);
}
