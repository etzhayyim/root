import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-25T19:30:00+09:00";
const ownerDid = "did:web:intel.etzhayyim.com";
const actorTag = "sys.bpmn.seed.intel";

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  resultTimeoutMs: number;
};

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-infer-dependencies-v1",
    bpmnProcessId: "intel_infer_dependencies",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/inferDependencies.bpmn",
    resultTimeoutMs: 180000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-resolve-entity-v1",
    bpmnProcessId: "intel_resolve_entity",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/resolveEntity.bpmn",
    resultTimeoutMs: 60000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-explain-dependency-v1",
    bpmnProcessId: "intel_explain_dependency",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/explainDependency.bpmn",
    resultTimeoutMs: 15000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-list-dependency-candidates-v1",
    bpmnProcessId: "intel_list_dependency_candidates",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/listDependencyCandidates.bpmn",
    resultTimeoutMs: 15000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-building-ownership-graph-v1",
    bpmnProcessId: "intel_get_building_ownership_graph",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/getBuildingOwnershipGraph.bpmn",
    resultTimeoutMs: 20000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-counterparty-graph-v1",
    bpmnProcessId: "intel_get_counterparty_graph",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/intel/getCounterpartyGraph.bpmn",
    resultTimeoutMs: 20000
  }
];

const bindingSeeds = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-inferDependencies-v1",
    nsid: "com.etzhayyim.apps.intel.inferDependencies",
    bpmnProcessId: "intel_infer_dependencies",
    resultTimeoutMs: 180000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-resolveEntity-v1",
    nsid: "com.etzhayyim.apps.intel.resolveEntity",
    bpmnProcessId: "intel_resolve_entity",
    resultTimeoutMs: 60000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-explainDependency-v1",
    nsid: "com.etzhayyim.apps.intel.explainDependency",
    bpmnProcessId: "intel_explain_dependency",
    resultTimeoutMs: 15000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-listDependencyCandidates-v1",
    nsid: "com.etzhayyim.apps.intel.listDependencyCandidates",
    bpmnProcessId: "intel_list_dependency_candidates",
    resultTimeoutMs: 15000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1",
    nsid: "com.etzhayyim.apps.intel.getBuildingOwnershipGraph",
    bpmnProcessId: "intel_get_building_ownership_graph",
    resultTimeoutMs: 20000
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getCounterpartyGraph-v1",
    nsid: "com.etzhayyim.apps.intel.getCounterpartyGraph",
    bpmnProcessId: "intel_get_counterparty_graph",
    resultTimeoutMs: 20000
  }
];

async function insertProcessDef(db: Kysely<unknown>, s: ProcessSeed): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(
  db: Kysely<unknown>,
  s: (typeof bindingSeeds)[number],
): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_intel_subject (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      subject_kind VARCHAR NOT NULL,
      canonical_key VARCHAR,
      label VARCHAR,
      source_did VARCHAR,
      source_vertex_id VARCHAR,
      lei VARCHAR,
      registration_number VARCHAR,
      jurisdiction VARCHAR,
      attributes_json VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_intel_inference_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      run_id VARCHAR NOT NULL,
      trigger_kind VARCHAR NOT NULL,
      scope_json VARCHAR,
      model VARCHAR,
      workflow_instance_key VARCHAR,
      candidate_count BIGINT,
      active_count BIGINT,
      review_count BIGINT,
      status VARCHAR,
      started_at VARCHAR,
      completed_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_intel_evidence (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      evidence_id VARCHAR NOT NULL,
      subject_vertex_id VARCHAR,
      source_uri VARCHAR,
      source_did VARCHAR,
      extractor VARCHAR,
      observed_at VARCHAR,
      hash VARCHAR,
      payload_json VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_intel_dependency (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      predicate VARCHAR NOT NULL,
      dependency_kind VARCHAR,
      confidence DOUBLE PRECISION,
      evidence_count BIGINT,
      evidence_json VARCHAR,
      inference_run_id VARCHAR,
      valid_from VARCHAR,
      valid_to VARCHAR,
      reason VARCHAR,
      model_version VARCHAR,
      status VARCHAR,
      reviewed_by VARCHAR,
      reviewed_at VARCHAR,
      review_note VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_intel_subject_kind ON vertex_intel_subject (subject_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_intel_subject_lei ON vertex_intel_subject (lei)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_intel_dependency_src ON edge_intel_dependency (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_intel_dependency_dst ON edge_intel_dependency (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_intel_dependency_status ON edge_intel_dependency (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_intel_dependency_predicate ON edge_intel_dependency (predicate)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_dependency_status AS
    SELECT predicate, status, COUNT(*) AS edge_count, AVG(confidence) AS avg_confidence
    FROM edge_intel_dependency
    GROUP BY predicate, status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_building_owner_lei AS
    SELECT
      d.edge_id,
      d.src_vid AS building_vid,
      d.dst_vid AS owner_vid,
      s.lei,
      s.label AS owner_label,
      d.confidence,
      d.status
    FROM edge_intel_dependency d
    LEFT JOIN vertex_intel_subject s ON s.vertex_id = d.dst_vid
    WHERE d.predicate IN ('owned_by', 'constructed_by', 'operated_by')
  `.execute(db);

  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
  for (const s of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_intel_building_owner_lei`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_intel_dependency_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_dependency_predicate`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_dependency_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_dependency_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_dependency_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_subject_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_intel_subject_kind`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_intel_dependency`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_intel_evidence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_intel_inference_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_intel_subject`.execute(db);
}
