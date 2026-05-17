import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase D pilot #1 (ADR-0056) — retire the 38-LoC lawyer.etzhayyim.com Worker.
// Mirrors the oshinobi seed migration shape (20260423220000_*) so the F5
// watcher picks this up and deploys lawyer_health to Zeebe automatically.

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  ownerDid: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number | null;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-23T23:00:00Z";
const ownerDid = "did:web:lawyer.etzhayyim.com";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawyer-health-v1",
    bpmnProcessId: "lawyer_health",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawyer/health.bpmn",
    ownerDid,
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/lawyer-health-v1",
    nsid: "ai.gftd.apps.lawyer.health",
    bpmnProcessId: "lawyer_health",
    ownerDid,
    resultTimeoutMs: 5000,
  },
];

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      owner_did,
      bpmn_process_id,
      version,
      xml,
      xml_byte_size,
      source_path,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.bpmnProcessId},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${seed.sourcePath},
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.lawyer'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id,
      owner_did,
      nsid,
      bpmn_process_id,
      bpmn_version,
      result_timeout_ms,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.nsid},
      ${seed.bpmnProcessId},
      1,
      CAST(${seed.resultTimeoutMs} AS integer),
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.lawyer'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of processSeeds) {
    await insertProcessDef(db, seed);
  }
  for (const seed of bindingSeeds) {
    await insertBinding(db, seed);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of bindingSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_process_def
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
}
