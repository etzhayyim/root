import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * yatabase.etzhayyim.com BPMN-as-actor seeding (ADR-0056 + ADR-2605080000 §D10).
 *
 * 10 BPMN process defs (4 timer-start + 6 XRPC-bound) + 6 XRPC bindings.
 * No CF Worker on the BPMN side (T2 tier: pymagatama + Zeebe only). The
 * CF Worker `yatabase.etzhayyim.com` is a separate edge proxy that talks to
 * bpmn-dispatcher via internal HTTP for storage operations and to RW
 * directly for SPARQL/PG passthrough.
 *
 *  Process / NSID                                 Trigger
 *  ----------------------------------------------------------------------
 *  yata_storage_metering_rollup    (autonomous)   R/PT1H
 *  yata_storage_embedding_drain    (autonomous)   R/PT5M
 *  yata_storage_tier_migrate       (autonomous)   cron 0 0 5 * * ?
 *  yata_multipart_reap             (autonomous)   R/PT6H
 *  yata_put_object                 ai.gftd.apps.yata.putObject
 *  yata_get_object                 ai.gftd.apps.yata.getObject
 *  yata_delete_object              ai.gftd.apps.yata.deleteObject
 *  yata_presign_url                ai.gftd.apps.yata.presignUrl
 *  yata_run_sparql                 ai.gftd.apps.yata.runSparql
 *  yata_provision_database         ai.gftd.apps.yata.provisionDatabase
 *
 * Lexicons NOT bound here (deferred to P3.1 follow-up; served via
 * generic.db.{select,insert} dispatch directly):
 *   listBuckets, createBucket, deleteBucket, listObjects, headObject,
 *   coverage, multipartInit, multipartPart, multipartComplete,
 *   multipartAbort.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T16:01:00Z";
const ownerDid = "did:web:yatabase.etzhayyim.com";
const actorTag = "sys.bpmn.seed.yata";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-storage-metering-rollup-v1",
    bpmnProcessId: "yata_storage_metering_rollup",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/storageMeteringRollup.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-storage-embedding-drain-v1",
    bpmnProcessId: "yata_storage_embedding_drain",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/storageEmbeddingDrain.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-storage-tier-migrate-v1",
    bpmnProcessId: "yata_storage_tier_migrate",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/storageTierMigrate.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-multipart-reap-v1",
    bpmnProcessId: "yata_multipart_reap",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/multipartReap.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-put-object-v1",
    bpmnProcessId: "yata_put_object",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/putObject.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-get-object-v1",
    bpmnProcessId: "yata_get_object",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/getObject.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-delete-object-v1",
    bpmnProcessId: "yata_delete_object",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/deleteObject.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-presign-url-v1",
    bpmnProcessId: "yata_presign_url",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/presignUrl.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-run-sparql-v1",
    bpmnProcessId: "yata_run_sparql",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/runSparql.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yata-provision-database-v1",
    bpmnProcessId: "yata_provision_database",
    sourcePath: "00-contracts/bpmn/ai/gftd/yata/provisionDatabase.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-putObject-v1",
    nsid: "ai.gftd.apps.yata.putObject",
    bpmnProcessId: "yata_put_object", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-getObject-v1",
    nsid: "ai.gftd.apps.yata.getObject",
    bpmnProcessId: "yata_get_object", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-deleteObject-v1",
    nsid: "ai.gftd.apps.yata.deleteObject",
    bpmnProcessId: "yata_delete_object", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-presignUrl-v1",
    nsid: "ai.gftd.apps.yata.presignUrl",
    bpmnProcessId: "yata_presign_url", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-runSparql-v1",
    nsid: "ai.gftd.apps.yata.runSparql",
    bpmnProcessId: "yata_run_sparql", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yata-provisionDatabase-v1",
    nsid: "ai.gftd.apps.yata.provisionDatabase",
    bpmnProcessId: "yata_provision_database", ownerDid, resultTimeoutMs: 60_000 },
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
