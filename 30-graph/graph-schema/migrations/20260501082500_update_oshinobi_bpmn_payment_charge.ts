import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

// Replace oshinobi subscribe + tipCreator BPMN XML:
// - Task_Charge was using generic.http.fetch (stub), now oshinobi.payment.charge (real Stripe)
// - Removes dependence on paymentProviderChargeUrl process variable

export async function up(db: Kysely<unknown>): Promise<void> {
  const ownerDid = "did:web:oshinobi.etzhayyim.com";
  const updatedAt = "2026-05-01T08:25:00Z";

  const updates = [
    {
      vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/oshinobi-subscribe-v1",
      bpmnProcessId: "oshinobi_subscribe",
      sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/subscribe.bpmn",
    },
    {
      vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/oshinobi-tip-creator-v1",
      bpmnProcessId: "oshinobi_tip_creator",
      sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/tipCreator.bpmn",
    },
  ];

  for (const u of updates) {
    const xml = readContract(u.sourcePath);
    const xmlByteSize = Buffer.byteLength(xml, "utf8");
    // RisingWave PK upsert: same vertex_id overwrites the existing row.
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
      ) VALUES (
        ${u.vertexId},
        ${ownerDid},
        ${u.bpmnProcessId},
        2,
        ${xml},
        CAST(${xmlByteSize} AS integer),
        ${u.sourcePath},
        'active',
        ${updatedAt},
        1,
        ${ownerDid},
        ${ownerDid},
        'sys.bpmn.seed.oshinobi'
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // no-op: BPMN XML rollback not supported (redeploy from git)
}
