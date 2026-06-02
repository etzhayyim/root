import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { proc: string; bpmnProcessId: string; nsid: string; resultTimeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:kenkyusha.etzhayyim.com";
const createdAt = "2026-05-07T01:35:00Z";
const actorId = "sys.bpmn.seed.kenkyusha";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeProcs = new Set(["collectEvidence", "detectFrontiers", "evaluateHypothesis", "generateHypothesis", "registerDids", "seedDisciplines"]);
const procs = ["collectEvidence", "coverageMap", "detectFrontiers", "evaluateHypothesis", "generateHypothesis", "getFrontier", "listDisciplines", "listFrontiers", "registerDids", "searchEvidence", "seedDisciplines", "stats"];
const writeTableAllowlist = [
  "vertex_kenkyusha_discipline",
  "vertex_kenkyusha_frontier",
  "vertex_kenkyusha_hypothesis",
  "vertex_kenkyusha_evidence",
  "vertex_kenkyusha_did_registration",
  "edge_kenkyusha_frontier_discipline",
  "edge_kenkyusha_hypothesis_frontier",
  "edge_kenkyusha_evidence_hypothesis",
].join(",");

const seeds: Seed[] = procs.map((proc) => ({
  proc,
  bpmnProcessId: `kenkyusha_${snake(proc)}`,
  nsid: `com.etzhayyim.apps.kenkyusha.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeProcs.has(proc) ? writeTableAllowlist : "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/kenkyusha/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kenkyusha-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kenkyusha-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${s.resultTimeoutMs}, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
