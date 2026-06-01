import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * yatabase.etzhayyim.com P3.2.5 — multipart + ListObjectsV2 BPMN seed
 * (ADR-2605080000 §D10 P3.2.5).
 *
 * 5 new BPMN process_def + 5 new XRPC bindings, all keyed off the
 * `app.etzhayyim.apps.yata.{multipartInit,multipartPart,multipartComplete,
 * multipartAbort,listObjects}` lexicons.  All XRPC-bound (no timer-start).
 *
 * Process / NSID                                  Trigger
 * ---------------------------------------------------------
 * yata_multipart_init      app.etzhayyim.apps.yata.multipartInit
 * yata_multipart_part      app.etzhayyim.apps.yata.multipartPart
 * yata_multipart_complete  app.etzhayyim.apps.yata.multipartComplete
 * yata_multipart_abort     app.etzhayyim.apps.yata.multipartAbort
 * yata_list_objects        app.etzhayyim.apps.yata.listObjects
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);
const repoRoot   = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt    = "2026-05-08T18:00:00Z";
const ownerDid     = "did:web:yatabase.etzhayyim.com";
const actorTag     = "sys.bpmn.seed.yata.multipart";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yata-multipart-init-v1",
    bpmnProcessId: "yata_multipart_init",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/multipartInit.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yata-multipart-part-v1",
    bpmnProcessId: "yata_multipart_part",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/multipartPart.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yata-multipart-complete-v1",
    bpmnProcessId: "yata_multipart_complete",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/multipartComplete.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yata-multipart-abort-v1",
    bpmnProcessId: "yata_multipart_abort",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/multipartAbort.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yata-list-objects-v1",
    bpmnProcessId: "yata_list_objects",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/listObjects.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yata-multipartInit-v1",
    nsid: "app.etzhayyim.apps.yata.multipartInit",
    bpmnProcessId: "yata_multipart_init", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yata-multipartPart-v1",
    nsid: "app.etzhayyim.apps.yata.multipartPart",
    bpmnProcessId: "yata_multipart_part", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yata-multipartComplete-v1",
    nsid: "app.etzhayyim.apps.yata.multipartComplete",
    bpmnProcessId: "yata_multipart_complete", ownerDid, resultTimeoutMs: 120_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yata-multipartAbort-v1",
    nsid: "app.etzhayyim.apps.yata.multipartAbort",
    bpmnProcessId: "yata_multipart_abort", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yata-listObjects-v1",
    nsid: "app.etzhayyim.apps.yata.listObjects",
    bpmnProcessId: "yata_list_objects", ownerDid, resultTimeoutMs: 30_000 },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
