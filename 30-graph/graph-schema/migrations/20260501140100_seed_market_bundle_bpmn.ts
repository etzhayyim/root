import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR 2605011300 — register the market_settlement_bundle BPMN as an
// actor row so the F5 watcher (30s) deploys it to Zeebe. Mirror of
// 20260501130100_seed_graph_expand_bpmn.ts.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-01T13:00:00Z";
const ownerDid = "did:web:market.etzhayyim.com";
const actorId = "sys.bpmn.seed.market";

interface BpmnSeed {
  processVertexId: string;
  bindingVertexId: string;
  processId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
}

const seeds: BpmnSeed[] = [
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/market-settlementBundle-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/market-settlementBundle-v1",
    processId: "market_settlement_bundle",
    nsid: "com.etzhayyim.market.settlementBundle",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/generic/settlementBundle.bpmn",
    resultTimeoutMs: 120_000,
    writeTableAllowlist: "vertex_market_settlement",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readContract(s.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${s.processVertexId}, ${ownerDid}, ${s.processId}, 1, ${xml},
             CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt},
             1, ${ownerDid}, ${ownerDid}, ${actorId}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.processVertexId}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
         write_table_allowlist, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${s.bindingVertexId}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
             CAST(${s.resultTimeoutMs} AS integer), ${s.writeTableAllowlist},
             'active', ${createdAt}, 1,
             ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = ${s.processVertexId}`.execute(db);
  }
}
