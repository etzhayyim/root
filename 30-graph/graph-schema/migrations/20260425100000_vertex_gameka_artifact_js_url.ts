import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_gameka_artifact + `js_url` column (ADR 2604250900 P5).
 *
 * The wasm-pack runner emits two B2 objects per build:
 *   - `builds/{wasmCid}.wasm`           the binary
 *   - `builds/{wasmCid}/main.js`        the wasm-bindgen glue (renamed from
 *                                       kami_app_{slug}.js for stable URL)
 *
 * Both presigned URLs are written to the -built row of vertex_gameka_artifact.
 * The playtest shell at game-play.gftd.ai/__playtest__.html loads the glue
 * first, then calls `init(wasmUrl)` to override the default same-dir wasm
 * fetch with the explicit presigned binary URL.
 *
 * Existing rows (pre-P5) get NULL js_url — the playtest shell handles that
 * gracefully by reporting captureSucceeded=false to the visualCritic.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_gameka_artifact ADD COLUMN js_url VARCHAR
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gameka_artifact DROP COLUMN js_url`.execute(db);
}
