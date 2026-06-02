import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for the
// myco-yeast (カビ×酵母) artificial organism three-layer architecture.
// ADR-2605071200 (Myco-Yeast Artificial Organism, PoNF consensus).
// F5 watcher deploys each BPMN to Zeebe within 30s of INSERT.
//
// Layer mapping:
//   kobo  (酵母) — individual agents:   budding / germination / sporulation
//   kabi  (カビ) — mycelial network:    anastomosis-gate
//   kinoko (キノコ) — fruiting body:    ponf-fruiting (PoNF consensus block)
//   hakkou (発酵) — fermentation output: ferment-pipeline

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T23:30:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

interface BpmnEntry {
  processId: string;
  bpmnPath: string;
  processVid: string;
  bindingVid: string;
  nsid: string;
}

const ENTRIES: BpmnEntry[] = [
  {
    processId: "kobo_budding",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/kobo/budding.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kobo-budding-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kobo-budding-v1",
    nsid: "com.etzhayyim.apps.kobo.budAgent",
  },
  {
    processId: "kobo_germination",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/kobo/germination.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kobo-germination-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kobo-germination-v1",
    nsid: "com.etzhayyim.apps.kobo.spawnAgent",
  },
  {
    processId: "kobo_sporulation",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/kobo/sporulation.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kobo-sporulation-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kobo-sporulation-v1",
    nsid: "com.etzhayyim.apps.kobo.sporulate",
  },
  {
    processId: "kabi_anastomosis_gate",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/kabi/anastomosis-gate.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kabi-anastomosis-gate-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kabi-anastomosis-gate-v1",
    nsid: "com.etzhayyim.apps.kabi.fusionProbe",
  },
  {
    processId: "kinoko_ponf_fruiting",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/kinoko/ponf-fruiting.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kinoko-ponf-fruiting-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/kinoko-ponf-fruiting-v1",
    nsid: "com.etzhayyim.apps.kinoko.formBlock",
  },
  {
    processId: "hakkou_ferment_pipeline",
    bpmnPath: "00-contracts/bpmn/com/etzhayyim/hakkou/ferment-pipeline.bpmn",
    processVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/hakkou-ferment-pipeline-v1",
    bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/hakkou-ferment-pipeline-v1",
    nsid: "com.etzhayyim.apps.hakkou.startFerment",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    const xml = readFileSync(path.resolve(repoRoot, e.bpmnPath), "utf8");
    const byteSize = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT
        ${e.processVid}, ${OWNER_DID}, ${e.processId}, 1,
        ${xml}, CAST(${byteSize} AS integer),
        ${e.bpmnPath}, 'active', ${CREATED_AT},
        1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.myco-yeast'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${e.processVid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, bpmn_process_id, nsid,
         created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT
        ${e.bindingVid}, ${OWNER_DID}, ${e.processId}, ${e.nsid},
        ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.myco-yeast'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVid}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${e.processVid}`.execute(db);
  }
}
