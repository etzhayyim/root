import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix invalid FEEL expressions in 3 LDA BPMN files:
// - inferLdaTopics:  flatten(for t in L1 for sw in L2 ...) → comma syntax + list filter predicate
// - inferLdaSignals: for c in list filter c.x = s.x → list[x = s.x] list filter predicate
// - inferLdaEntities: for t in topics let ... filter → if/then/else null (let bindings unsupported)
// Resets status='active' so F5 watcher re-deploys to Zeebe.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const project = "coverage";

const processes = [
  { proc: "inferLdaSignals",  sourcePath: "00-contracts/bpmn/ai/gftd/coverage/inferLdaSignals.bpmn" },
  { proc: "inferLdaTopics",   sourcePath: "00-contracts/bpmn/ai/gftd/coverage/inferLdaTopics.bpmn" },
  { proc: "inferLdaEntities", sourcePath: "00-contracts/bpmn/ai/gftd/coverage/inferLdaEntities.bpmn" },
] as const;

const processVertexId = (proc: string) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${project}-${proc}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const p of processes) {
    const xml = readFileSync(path.resolve(repoRoot, p.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const vid = processVertexId(p.proc);
    await sql`UPDATE vertex_bpmn_process_def
              SET "xml" = ${xml}, xml_byte_size = ${size}::integer, "version" = 2, status = 'active'
              WHERE vertex_id = ${vid}`.execute(db);
  }
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: reverting to broken FEEL would re-break Zeebe deployment.
}
