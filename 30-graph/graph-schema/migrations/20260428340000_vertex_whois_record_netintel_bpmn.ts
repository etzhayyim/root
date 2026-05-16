import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:ingest.gftd.ai";
const ingestDid = "did:web:ingest.gftd.ai";
const createdAt = "2026-04-28T18:00:00Z";
const actorTag = "sys.bpmn.seed.netintel-ingest";

const seeds = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-dns-delta-v1",
    bindingId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-netintel-dns-delta-v1",
    processId: "netintel_dns_delta",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/netintelDnsDelta.bpmn",
    writeTables: "vertex_dns_observation,vertex_ingest_run",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-ip-enrich-delta-v1",
    bindingId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-netintel-ip-enrich-delta-v1",
    processId: "netintel_ip_enrich_delta",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/ipEnrichDelta.bpmn",
    writeTables: "vertex_ip_address,vertex_ingest_run",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-whois-delta-v1",
    bindingId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-netintel-whois-delta-v1",
    processId: "netintel_whois_delta",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/whoisDelta.bpmn",
    writeTables: "vertex_whois_record,vertex_ingest_run",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-scan-banner-delta-v1",
    bindingId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-netintel-scan-banner-delta-v1",
    processId: "netintel_scan_banner_delta",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/scanBannerDelta.bpmn",
    writeTables: "vertex_scan_result,vertex_ingest_run",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-fingerprint-delta-v1",
    bindingId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-netintel-fingerprint-delta-v1",
    processId: "netintel_fingerprint_delta",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/fingerprintDelta.bpmn",
    writeTables: "vertex_scan_result,vertex_ingest_run",
  },
];

function readXml(sourcePath: string): string {
  return readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_whois_record (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      domain VARCHAR,
      registrar VARCHAR,
      registrar_iana_id VARCHAR,
      nameservers VARCHAR,
      created_date_rdap VARCHAR,
      updated_date_rdap VARCHAR,
      expires_date_rdap VARCHAR,
      status VARCHAR,
      dnssec VARCHAR,
      raw_excerpt TEXT,
      queried_at VARCHAR,
      run_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_whois_record_domain ON vertex_whois_record (domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_whois_record_queried ON vertex_whois_record (domain, queried_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_whois_record_run ON vertex_whois_record (run_id)`.execute(db);

  for (const seed of seeds) {
    const body = readXml(seed.sourcePath);
    const size = Buffer.byteLength(body, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${seed.vertexId}, ${ownerDid}, ${seed.processId},
             1, ${body}, CAST(${size} AS integer), ${seed.sourcePath}, 'active',
             ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId})
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
        actor_id, write_table_allowlist
      )
      SELECT ${seed.bindingId}, ${ingestDid}, 'ai.gftd.apps.ingest.start',
             ${seed.processId}, 1, CAST(0 AS integer), 'active',
             ${createdAt}, 1, ${ingestDid}, ${ingestDid}, ${actorTag},
             ${seed.writeTables}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
  await sql`DROP TABLE IF EXISTS vertex_whois_record`.execute(db);
}
