import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  slug: string;
  bpmnProcessId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T20:00:00+09:00";
const ownerDid = "did:web:open-adnetwork.etzhayyim.com";
const actorTag = "sys.bpmn.seed.open-adnetwork";
const project = "open-adnetwork";

const seeds: Seed[] = [
  {
    slug: "register-publisher",
    bpmnProcessId: "open_adnetwork_register_publisher",
    nsid: "com.etzhayyim.apps.openAdnetwork.registerPublisher",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/registerPublisher.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_publisher",
  },
  {
    slug: "record-ad-unit",
    bpmnProcessId: "open_adnetwork_record_ad_unit",
    nsid: "com.etzhayyim.apps.openAdnetwork.recordAdUnit",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/recordAdUnit.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_ad_unit",
  },
  {
    slug: "register-advertiser",
    bpmnProcessId: "open_adnetwork_register_advertiser",
    nsid: "com.etzhayyim.apps.openAdnetwork.registerAdvertiser",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/registerAdvertiser.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_advertiser",
  },
  {
    slug: "create-campaign",
    bpmnProcessId: "open_adnetwork_create_campaign",
    nsid: "com.etzhayyim.apps.openAdnetwork.createCampaign",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/createCampaign.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_campaign",
  },
  {
    slug: "record-impression",
    bpmnProcessId: "open_adnetwork_record_impression",
    nsid: "com.etzhayyim.apps.openAdnetwork.recordImpression",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/recordImpression.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_impression",
  },
  {
    slug: "record-conversion",
    bpmnProcessId: "open_adnetwork_record_conversion",
    nsid: "com.etzhayyim.apps.openAdnetwork.recordConversion",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/recordConversion.bpmn",
    resultTimeoutMs: 30000,
    writeTableAllowlist: "vertex_open_adnetwork_conversion",
  },
  {
    slug: "compute-publisher-rpm",
    bpmnProcessId: "open_adnetwork_compute_publisher_rpm",
    nsid: "com.etzhayyim.apps.openAdnetwork.computePublisherRpm",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/computePublisherRpm.bpmn",
    resultTimeoutMs: 90000,
    writeTableAllowlist: "vertex_open_adnetwork_revenue_snapshot",
  },
  {
    slug: "fetch-auction-market-delta",
    bpmnProcessId: "open_adnetwork_fetch_auction_market_delta",
    nsid: "com.etzhayyim.apps.openAdnetwork.fetchAuctionMarketDelta",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-adnetwork/fetchAuctionMarketDelta.bpmn",
    resultTimeoutMs: 90000,
    writeTableAllowlist: "",
  },
];

const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${s.slug}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
      actor_did, org_did
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, write_table_allowlist, status, created_at,
      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), ${s.writeTableAllowlist},
      'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = ${s.writeTableAllowlist}
    WHERE bpmn_process_id = ${s.bpmnProcessId}
      AND nsid = ${s.nsid}
      AND (write_table_allowlist IS NULL OR write_table_allowlist <> ${s.writeTableAllowlist})
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
