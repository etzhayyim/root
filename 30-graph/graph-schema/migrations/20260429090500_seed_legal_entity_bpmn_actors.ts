import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T09:05:00Z";
const ownerDid = "did:web:legal-entity.etzhayyim.com";
const actorTag = "sys.bpmn.seed.legal-entity";
// bpmn-coverage gate marker: project: "legal-entity"
const project = "legal-entity";

const seeds: Seed[] = [
  {
    proc: "collectGlobalGleif",
    bpmnProcessId: "legal_entity_collect_global_gleif",
    nsid: "com.etzhayyim.apps.legalEntity.collectGlobalGleif",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectGlobalGleif.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "registerGleifDids",
    bpmnProcessId: "legal_entity_register_gleif_dids",
    nsid: "com.etzhayyim.apps.legalEntity.registerGleifDids",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/registerGleifDids.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectUsaEdgar",
    bpmnProcessId: "legal_entity_collect_usa_edgar",
    nsid: "com.etzhayyim.apps.legalEntity.collectUsaEdgar",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectUsaEdgar.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "ingestSecDisclosure",
    bpmnProcessId: "legal_entity_ingest_sec_disclosure",
    nsid: "com.etzhayyim.apps.legalEntity.ingestSecDisclosure",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/ingestSecDisclosure.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectJpn",
    bpmnProcessId: "legal_entity_collect_jpn",
    nsid: "com.etzhayyim.apps.legalEntity.collectJpn",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectJpn.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectGbr",
    bpmnProcessId: "legal_entity_collect_gbr",
    nsid: "com.etzhayyim.apps.legalEntity.collectGbr",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectGbr.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectFra",
    bpmnProcessId: "legal_entity_collect_fra",
    nsid: "com.etzhayyim.apps.legalEntity.collectFra",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectFra.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectNor",
    bpmnProcessId: "legal_entity_collect_nor",
    nsid: "com.etzhayyim.apps.legalEntity.collectNor",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectNor.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectDnk",
    bpmnProcessId: "legal_entity_collect_dnk",
    nsid: "com.etzhayyim.apps.legalEntity.collectDnk",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectDnk.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectFin",
    bpmnProcessId: "legal_entity_collect_fin",
    nsid: "com.etzhayyim.apps.legalEntity.collectFin",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectFin.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectEst",
    bpmnProcessId: "legal_entity_collect_est",
    nsid: "com.etzhayyim.apps.legalEntity.collectEst",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectEst.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectCze",
    bpmnProcessId: "legal_entity_collect_cze",
    nsid: "com.etzhayyim.apps.legalEntity.collectCze",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectCze.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectNzl",
    bpmnProcessId: "legal_entity_collect_nzl",
    nsid: "com.etzhayyim.apps.legalEntity.collectNzl",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectNzl.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectChe",
    bpmnProcessId: "legal_entity_collect_che",
    nsid: "com.etzhayyim.apps.legalEntity.collectChe",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectChe.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectNld",
    bpmnProcessId: "legal_entity_collect_nld",
    nsid: "com.etzhayyim.apps.legalEntity.collectNld",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectNld.bpmn",
    resultTimeoutMs: 120000,
  },
  {
    proc: "collectIsr",
    bpmnProcessId: "legal_entity_collect_isr",
    nsid: "com.etzhayyim.apps.legalEntity.collectIsr",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/legal-entity/collectIsr.bpmn",
    resultTimeoutMs: 120000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-${s.proc}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await insertProcessDef(db, s);
    await insertBinding(db, s);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
