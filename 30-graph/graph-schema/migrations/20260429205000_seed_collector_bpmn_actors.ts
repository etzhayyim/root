import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; processId: string; nsid: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:collector.etzhayyim.com";
const createdAt = "2026-04-29T20:50:00+09:00";
const actorId = "sys.bpmn.seed.collector";
const project = "collector";

const seeds: Seed[] = [
  { slug: "collect-netintel-dns", processId: "collector_collect_netintel_dns", nsid: "ai.gftd.apps.collector.collectNetintelDns", sourcePath: "00-contracts/bpmn/ai/gftd/collector/collectNetintelDns.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_run,vertex_collector_dns_observation,vertex_collector_dns_snapshot,vertex_collector_organization" },
  { slug: "collect-blockchain-btc", processId: "collector_collect_blockchain_btc", nsid: "ai.gftd.apps.collector.collectBlockchainBtc", sourcePath: "00-contracts/bpmn/ai/gftd/collector/collectBlockchainBtc.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_run,vertex_collector_blockchain_actor,vertex_collector_risk_signal" },
  { slug: "collect-blockchain-eth", processId: "collector_collect_blockchain_eth", nsid: "ai.gftd.apps.collector.collectBlockchainEth", sourcePath: "00-contracts/bpmn/ai/gftd/collector/collectBlockchainEth.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_run,vertex_collector_blockchain_actor,vertex_collector_risk_signal" },
  { slug: "collect-common-crawl", processId: "collector_collect_common_crawl", nsid: "ai.gftd.apps.collector.collectCommonCrawl", sourcePath: "00-contracts/bpmn/ai/gftd/collector/collectCommonCrawl.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_archive_snapshot" },
  { slug: "collect-archive", processId: "collector_collect_archive", nsid: "ai.gftd.apps.collector.collectArchive", sourcePath: "00-contracts/bpmn/ai/gftd/collector/collectArchive.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_archive_snapshot" },
  { slug: "ingest-scan-result", processId: "collector_ingest_scan_result", nsid: "ai.gftd.apps.collector.ingestScanResult", sourcePath: "00-contracts/bpmn/ai/gftd/collector/ingestScanResult.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_collector_scan_result" },
  { slug: "trigger-run", processId: "collector_trigger_run", nsid: "ai.gftd.apps.collector.triggerRun", sourcePath: "00-contracts/bpmn/ai/gftd/collector/triggerRun.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_collector_run,vertex_collector_dns_observation,vertex_collector_dns_snapshot,vertex_collector_organization,vertex_collector_blockchain_actor,vertex_collector_archive_snapshot" },
  { slug: "get-dashboard", processId: "collector_get_dashboard", nsid: "ai.gftd.apps.collector.getDashboard", sourcePath: "00-contracts/bpmn/ai/gftd/collector/getDashboard.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-jobs", processId: "collector_list_jobs", nsid: "ai.gftd.apps.collector.listJobs", sourcePath: "00-contracts/bpmn/ai/gftd/collector/listJobs.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${project}-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
