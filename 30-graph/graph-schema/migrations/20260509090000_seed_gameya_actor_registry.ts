import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO actor_registry
      (did, handle, tier, backend_kind, backend_url, mcp_endpoint, capability_tags, governance_class, created_at, deactivated_at)
    VALUES
      ('did:web:gameya.etzhayyim.com', 'gameya.etzhayyim.com', 'T3', 'cf-worker', 'https://gameya.etzhayyim.com/', 'https://gameya.etzhayyim.com/mcp', 'game,canvas,langgraph-quality-loop', 'T3', '2026-05-09T00:00:00Z', NULL)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM actor_registry
    WHERE did = 'did:web:gameya.etzhayyim.com'
  `.execute(db);
}
