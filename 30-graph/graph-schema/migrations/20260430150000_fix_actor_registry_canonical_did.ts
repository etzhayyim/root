import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix actor_registry.did for nanoid-based actors whose canonical DID
// (/.well-known/atproto-did) differs from the handle-derived did:web:{handle}.
// Enables AppView resolveHandleToDid() to query actor_registry instead of
// HTTP-fetching /.well-known/atproto-did per request.
//
// Actor → canonical DID mapping source: curl https://{handle}/.well-known/atproto-did
//   yukkuri.etzhayyim.com → did:web:y5kk5r1x.etzhayyim.com  (was: did:plc:yukkuri)

export async function up(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support UPDATE on PK columns — use DELETE + INSERT.
  await sql`DELETE FROM actor_registry WHERE handle = 'yukkuri.etzhayyim.com'`.execute(db);
  await sql`
    INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:web:y5kk5r1x.etzhayyim.com', 'yukkuri.etzhayyim.com', 'T3', NOW())
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM actor_registry WHERE handle = 'yukkuri.etzhayyim.com'`.execute(db);
  await sql`
    INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:plc:yukkuri', 'yukkuri.etzhayyim.com', 'T3', NOW())
  `.execute(db);
}
