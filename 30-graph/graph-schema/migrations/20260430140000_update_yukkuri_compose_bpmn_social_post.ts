import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Extend yukkuriCompose.bpmn with a social post step (Task_SocialPost,
// task type: yukkuri.social.post) inserted between Task_Audit and End_Published.
// The new pyzeebe handler writes a app.bsky.feed.post record to vertex_repo_record
// as did:web:yukkuri.gftd.ai, making the published video visible on yoro.gftd.ai.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/yukkuri/yukkuriCompose.bpmn"),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        xml_byte_size = CAST(${size} AS integer),
        status = 'active',
        deployed_zeebe_key = NULL,
        deployed_at = NULL
    WHERE bpmn_process_id = 'yukkuri_compose'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'inactive'
    WHERE bpmn_process_id = 'yukkuri_compose'
  `.execute(db);
}
