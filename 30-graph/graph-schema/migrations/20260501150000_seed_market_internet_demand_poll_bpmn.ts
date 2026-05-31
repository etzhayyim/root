import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR 2605011300 — register the market_internet_demand_poll BPMN as an
// actor row so the F5 watcher (30s) deploys it to Zeebe. This is the
// internet-space → ∇φ ingestion process. Mirror of
// 20260501140100_seed_market_bundle_bpmn.ts.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-01T14:30:00Z";
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
    processVertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/market-internetDemandPoll-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/market-internetDemandPoll-v1",
    processId: "market_internet_demand_poll",
    nsid: "app.etzhayyim.market.internetDemandPoll",
    sourcePath: "00-contracts/bpmn/ai/gftd/generic/internetDemandPoll.bpmn",
    resultTimeoutMs: 90_000,
    writeTableAllowlist: "vertex_market_demand_signal",
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
