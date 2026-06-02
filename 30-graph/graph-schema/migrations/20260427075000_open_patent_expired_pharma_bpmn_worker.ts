import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  project: string;
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T07:50:00Z";
const ownerDid = "did:web:open-patent.etzhayyim.com";
const actorTag = "sys.bpmn.seed.open-patent-expired-pharma";

const seeds: Seed[] = [
  {
    project: "open-patent",
    proc: "summarizeSeiyakuStartProgress",
    bpmnProcessId: "open_patent_summarize_seiyaku_start_progress",
    nsid: "com.etzhayyim.apps.openPatent.summarizeSeiyakuStartProgress",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "acknowledgeSeiyakuBatchStart",
    bpmnProcessId: "open_patent_acknowledge_seiyaku_batch_start",
    nsid: "com.etzhayyim.apps.openPatent.acknowledgeSeiyakuBatchStart",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "queueSeiyakuBatchStart",
    bpmnProcessId: "open_patent_queue_seiyaku_batch_start",
    nsid: "com.etzhayyim.apps.openPatent.queueSeiyakuBatchStart",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "validateSeiyakuBatchDraft",
    bpmnProcessId: "open_patent_validate_seiyaku_batch_draft",
    nsid: "com.etzhayyim.apps.openPatent.validateSeiyakuBatchDraft",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "prepareSeiyakuBatchDraft",
    bpmnProcessId: "open_patent_prepare_seiyaku_batch_draft",
    nsid: "com.etzhayyim.apps.openPatent.prepareSeiyakuBatchDraft",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "handoffGenericCandidateToSeiyaku",
    bpmnProcessId: "open_patent_handoff_generic_candidate_to_seiyaku",
    nsid: "com.etzhayyim.apps.openPatent.handoffGenericCandidateToSeiyaku",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "recordDrugRegulatoryBlocker",
    bpmnProcessId: "open_patent_record_drug_regulatory_blocker",
    nsid: "com.etzhayyim.apps.openPatent.recordDrugRegulatoryBlocker",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "runExpiredDrugPatentPipeline",
    bpmnProcessId: "open_patent_run_expired_drug_patent_pipeline",
    nsid: "com.etzhayyim.apps.openPatent.runExpiredDrugPatentPipeline",
    resultTimeoutMs: 120000,
  },
  {
    project: "open-patent",
    proc: "collectExpiredDrugPatentBacklog",
    bpmnProcessId: "open_patent_collect_expired_drug_patent_backlog",
    nsid: "com.etzhayyim.apps.openPatent.collectExpiredDrugPatentBacklog",
    resultTimeoutMs: 60000,
  },
  {
    project: "open-patent",
    proc: "screenExpiredDrugPatent",
    bpmnProcessId: "open_patent_screen_expired_drug_patent",
    nsid: "com.etzhayyim.apps.openPatent.screenExpiredDrugPatent",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-patent",
    proc: "startGenericManufacturingCandidate",
    bpmnProcessId: "open_patent_start_generic_manufacturing_candidate",
    nsid: "com.etzhayyim.apps.openPatent.startGenericManufacturingCandidate",
    resultTimeoutMs: 30000,
  },
];

function sourcePath(seed: Seed): string {
  return `00-contracts/bpmn/com/etzhayyim/${seed.project}/${seed.proc}.bpmn`;
}

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

function slug(proc: string): string {
  return proc.replace(/([A-Z])/g, "-$1").toLowerCase();
}

function processVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${seed.project}-${slug(seed.proc)}-v1`;
}

function bindingVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${seed.project}-${seed.proc}-v1`;
}

async function createTables(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_regulatory_blocker (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      patent_vertex_id   varchar NOT NULL,
      patent_number      varchar NOT NULL,
      jurisdiction       varchar NOT NULL,
      product_id         varchar,
      blocker_type       varchar NOT NULL,
      blocking_until     varchar NOT NULL,
      source             varchar,
      evidence_uri       varchar,
      as_of              varchar NOT NULL,
      active             boolean NOT NULL,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_expiry_backlog_run (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      as_of              varchar NOT NULL,
      jurisdiction       varchar,
      limit_count        int,
      scanned_count      int NOT NULL,
      candidate_count    int NOT NULL,
      inserted_count     int NOT NULL,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_drug_expiry (
      vertex_id                    varchar PRIMARY KEY,
      _seq                         bigint,
      created_date                 date,
      sensitivity_ord              int,
      owner_did                    varchar,
      patent_vertex_id             varchar NOT NULL,
      patent_number                varchar NOT NULL,
      jurisdiction                 varchar NOT NULL,
      product_id                   varchar,
      atc_code                     varchar,
      ndc_code                     varchar,
      expiry_date                  varchar NOT NULL,
      blocking_exclusivity_until   varchar,
      as_of                        varchar NOT NULL,
      eligible                     boolean NOT NULL,
      status                       varchar NOT NULL,
      created_at                   varchar,
      org_id                       varchar,
      user_id                      varchar,
      actor_id                     varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_generic_candidate (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      expiry_screen_vid      varchar NOT NULL,
      product_id             varchar NOT NULL,
      candidate_kind         varchar NOT NULL,
      manufacturer_org_id    varchar,
      plant_org_id           varchar,
      dosage_form            varchar,
      process_type           varchar,
      target_market          varchar,
      seiyaku_process_id     varchar NOT NULL,
      status                 varchar NOT NULL,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_handoff (
      vertex_id               varchar PRIMARY KEY,
      _seq                    bigint,
      created_date            date,
      sensitivity_ord         int,
      owner_did               varchar,
      generic_candidate_vid   varchar NOT NULL,
      product_id              varchar NOT NULL,
      seiyaku_process_id      varchar NOT NULL,
      target_market           varchar,
      manufacturer_org_id     varchar,
      plant_org_id            varchar,
      dosage_form             varchar,
      batch_intent            varchar,
      status                  varchar NOT NULL,
      created_at              varchar,
      org_id                  varchar,
      user_id                 varchar,
      actor_id                varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_batch_draft (
      vertex_id               varchar PRIMARY KEY,
      _seq                    bigint,
      created_date            date,
      sensitivity_ord         int,
      owner_did               varchar,
      handoff_vid             varchar NOT NULL,
      product_id              varchar NOT NULL,
      manufacturer_org_id     varchar NOT NULL,
      plant_org_id            varchar NOT NULL,
      product_code            varchar NOT NULL,
      batch_number            varchar NOT NULL,
      dosage_form             varchar,
      target_market           varchar,
      seiyaku_process_id      varchar NOT NULL,
      batch_payload           jsonb,
      status                  varchar NOT NULL,
      created_at              varchar,
      org_id                  varchar,
      user_id                 varchar,
      actor_id                varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_batch_validation (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      batch_draft_vid       varchar,
      passed                boolean NOT NULL,
      status                varchar NOT NULL,
      findings              jsonb,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_start_request (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      batch_draft_vid    varchar NOT NULL,
      validation_vid     varchar,
      start_nsid         varchar NOT NULL,
      bpmn_process_id    varchar NOT NULL,
      request_payload    jsonb,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_start_ack (
      vertex_id                 varchar PRIMARY KEY,
      _seq                      bigint,
      created_date              date,
      sensitivity_ord           int,
      owner_did                 varchar,
      start_request_vid         varchar NOT NULL,
      seiyaku_instance_key      bigint,
      seiyaku_batch_vertex_id   varchar,
      status                    varchar NOT NULL,
      message                   varchar,
      created_at                varchar,
      org_id                    varchar,
      user_id                   varchar,
      actor_id                  varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_progress (
      vertex_id                 varchar PRIMARY KEY,
      _seq                      bigint,
      created_date              date,
      sensitivity_ord           int,
      owner_did                 varchar,
      start_request_vid         varchar NOT NULL,
      ack_vid                   varchar,
      progress_status           varchar NOT NULL,
      seiyaku_instance_key      bigint,
      seiyaku_batch_vertex_id   varchar,
      message                   varchar,
      created_at                varchar,
      org_id                    varchar,
      user_id                   varchar,
      actor_id                  varchar
    )
  `.execute(db);
}

async function insertProcessDef(db: Kysely<unknown>, seed: Seed): Promise<void> {
  const relPath = sourcePath(seed);
  const xml = readContract(relPath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(seed)}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${relPath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(seed)}, ${ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createTables(db);
  for (const seed of seeds) await insertProcessDef(db, seed);
  for (const seed of seeds) await insertBinding(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}`.execute(db);
  }
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}`.execute(db);
  }
  await sql`DROP TABLE IF EXISTS vertex_open_patent_generic_candidate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_progress`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_start_ack`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_start_request`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_batch_validation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_batch_draft`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_seiyaku_handoff`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_drug_expiry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_expiry_backlog_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_patent_regulatory_blocker`.execute(db);
}
