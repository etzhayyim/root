import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * sbom.etzhayyim.com — Phase C feeder (cveIngestOsv) + Phase D query (recall).
 *
 *   sbom_cve_ingest_osv  ai.gftd.apps.sbom.cveIngestOsv
 *   sbom_recall          ai.gftd.apps.sbom.recall
 *
 * Both registered as version 1; F5 watcher deploys to Zeebe within 30s.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-06T12:00:00Z";
const ownerDid = "did:web:sbom.etzhayyim.com";
const actorTag = "sys.bpmn.seed.sbom-phase-cd";

const processSeeds: P[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-cve-ingest-osv-v1",
    bpmnProcessId: "sbom_cve_ingest_osv",
    sourcePath: "00-contracts/bpmn/ai/gftd/sbom/cveIngestOsv.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-recall-v1",
    bpmnProcessId: "sbom_recall",
    sourcePath: "00-contracts/bpmn/ai/gftd/sbom/recall.bpmn",
    ownerDid,
  },
];

const bindingSeeds: B[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-cveIngestOsv-v1",
    nsid: "ai.gftd.apps.sbom.cveIngestOsv",
    bpmnProcessId: "sbom_cve_ingest_osv",
    ownerDid,
    // 1h — daily refresh can pull tens of thousands of vulnerabilities.
    resultTimeoutMs: 3_600_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-recall-v1",
    nsid: "ai.gftd.apps.sbom.recall",
    bpmnProcessId: "sbom_recall",
    ownerDid,
    resultTimeoutMs: 60_000,
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord,
      org_id, user_id, actor_id
    )
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml},
           CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt},
           1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord,
      org_id, user_id, actor_id
    )
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
           CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt},
           1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
