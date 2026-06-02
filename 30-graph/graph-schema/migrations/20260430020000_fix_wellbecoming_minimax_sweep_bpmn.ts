import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix BPMN 2.0 XSD ordering bug in minimaxSweep.bpmn:
// <timerEventDefinition> was before <outgoing> inside <startEvent>.
// Zeebe rejects this with INVALID_ARGUMENT; pyzeebe wraps it as ProcessInvalidError("")
// and the dispatcher marks the process inactive + adds it to _deployed_in_flight.
// This migration re-seeds the corrected XML and resets status='active'.
// Requires a pod restart of bpmn-dispatcher to clear _deployed_in_flight.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/com/etzhayyim/wellbecoming/minimaxSweep.bpmn"),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        xml_byte_size = CAST(${size} AS integer),
        status = 'active',
        deployed_zeebe_key = NULL
    WHERE bpmn_process_id = 'wellbecoming_minimax_sweep'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'inactive'
    WHERE bpmn_process_id = 'wellbecoming_minimax_sweep'
  `.execute(db);
}
