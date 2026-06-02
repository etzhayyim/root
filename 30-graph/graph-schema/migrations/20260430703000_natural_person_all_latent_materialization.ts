import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-30T20:30:00Z";
const ownerDid = "did:web:natural-person.etzhayyim.com";
const actorTag = "sys.bpmn.seed.natural-person";
const project = "natural-person";

const seed = {
  proc: "materializeAllLatentEntities",
  bpmnProcessId: "natural_person_materialize_all_latent_entities_v1",
  nsid: "com.etzhayyim.apps.naturalPerson.materializeAllLatentEntities",
  sourcePath: "00-contracts/bpmn/com/etzhayyim/natural-person/materializeAllLatentEntities.bpmn",
  resultTimeoutMs: 300000,
};

const processVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-materialize-all-latent-entities-v1`;
const bindingVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${seed.proc}-v1`;

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_natural_person_latent_materialization_cursor (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      sensitivity_ord    INTEGER DEFAULT 300,
      owner_did          VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR,
      created_at         TIMESTAMP,
      updated_at         TIMESTAMP,
      cohort_vid         VARCHAR,
      cohort_hash        VARCHAR,
      target_count       BIGINT,
      next_ordinal       BIGINT,
      materialized_count BIGINT,
      batch_size         BIGINT,
      status             VARCHAR,
      last_error         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_np_latent_cursor_status ON vertex_natural_person_latent_materialization_cursor(status, updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_np_latent_cursor_hash ON vertex_natural_person_latent_materialization_cursor(cohort_hash)`.execute(db);

  const xml = readContract(seed.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_natural_person_latent_materialization_cursor`.execute(db);
}
