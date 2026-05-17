import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0056 BPMN-as-actor seed — arms expired permit scanner.
// Inserts 2 rows: 1 vertex_bpmn_process_def + 1 vertex_bpmn_lexicon_binding.
// F5 watcher (30s) picks up the new process_def row and deploys to Zeebe automatically.
// Timer: R/P1D — scans vertex_arms_permit WHERE expires_at < NOW() AND status = 'active'
// and PK-upserts those rows with status = 'expired' (RisingWave implicit overwrite).

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-28T00:00:00Z";
const ownerDid = "did:web:arms.etzhayyim.com";

const processDefVertexId =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/arms-expired-permit-scanner-v1";
const bindingVertexId =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/arms-scanExpiredPermits-v1";

const bpmnSourcePath =
  "00-contracts/bpmn/ai/gftd/arms/expiredPermitScanner.bpmn";
const bpmnProcessId = "arms_expired_permit_scanner";
const nsid = "ai.gftd.apps.arms.scanExpiredPermits";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(bpmnSourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");

  // Row 1: process definition
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
      ${processDefVertexId},
      ${ownerDid},
      ${bpmnProcessId},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${bpmnSourcePath},
      'active',
      ${createdAt},
      1,
      ${ownerDid},
      ${ownerDid},
      'sys.bpmn.seed.arms'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processDefVertexId}
    )
  `.execute(db);

  // Row 2: lexicon binding (allows manual XRPC trigger + maps NSID to process)
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
      ${bindingVertexId},
      ${ownerDid},
      ${nsid},
      ${bpmnProcessId},
      1,
      CAST(60000 AS integer),
      'active',
      ${createdAt},
      1,
      ${ownerDid},
      ${ownerDid},
      'sys.bpmn.seed.arms'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
  `.execute(db);
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processDefVertexId}
  `.execute(db);
}
