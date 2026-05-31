import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T09:00:00Z";
const ownerDid = "did:web:pd-color.etzhayyim.com";
const actorTag = "sys.bpmn.seed.public-domain-colorization";

const seed = {
  project: "public-domain-colorization",
  proc: "colorizeWork",
  bpmnProcessId: "public_domain_colorization_pipeline",
  nsid: "app.etzhayyim.apps.publicDomainColorization.colorizeWork",
  resultTimeoutMs: 900000,
};

const sourcePath = `00-contracts/bpmn/ai/gftd/${seed.project}/${seed.proc}.bpmn`;
const processVertexId = `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${seed.project}-colorize-work-v1`;
const bindingVertexId = `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${seed.project}-${seed.proc}-v1`;

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

async function createTables(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_work (
      vertex_id             varchar PRIMARY KEY,
      work_id               varchar NOT NULL,
      title                 varchar NOT NULL,
      work_kind             varchar NOT NULL,
      source_language       varchar,
      country_of_origin     varchar,
      first_published_at    varchar,
      source_url            varchar,
      source_blob_cid       varchar,
      source_ipfs_cid       varchar,
      source_ipfs_url       varchar,
      source_sha256         varchar,
      source_byte_size      bigint,
      status                varchar NOT NULL DEFAULT 'candidate',
      created_at            varchar NOT NULL,
      sensitivity_ord       int NOT NULL DEFAULT 1,
      owner_did             varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_source_asset (
      vertex_id             varchar PRIMARY KEY,
      work_id               varchar NOT NULL,
      source_url            varchar,
      source_blob_cid       varchar,
      source_ipfs_cid       varchar,
      source_ipfs_url       varchar,
      source_archive_id     varchar,
      sha256                varchar,
      media_kind            varchar NOT NULL,
      duration_ms           bigint,
      width                 int,
      height                int,
      frame_rate            varchar,
      acquisition_note      varchar,
      created_at            varchar NOT NULL,
      sensitivity_ord       int NOT NULL DEFAULT 1,
      owner_did             varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_rights_review (
      vertex_id              varchar PRIMARY KEY,
      work_id                varchar NOT NULL,
      publish_jurisdiction   varchar NOT NULL,
      rights_classification  varchar NOT NULL,
      rights_evidence_cid    varchar,
      blocked_reasons_json   varchar,
      reviewer_did           varchar,
      rights_approved        boolean NOT NULL DEFAULT false,
      reviewed_at            varchar,
      created_at             varchar NOT NULL,
      sensitivity_ord        int NOT NULL DEFAULT 1,
      owner_did              varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_run (
      vertex_id              varchar PRIMARY KEY,
      work_id                varchar NOT NULL,
      title                  varchar NOT NULL,
      work_kind              varchar NOT NULL,
      source_url             varchar,
      source_blob_cid        varchar,
      source_ipfs_cid        varchar,
      source_ipfs_url        varchar,
      source_sha256          varchar,
      source_byte_size       bigint,
      publish_jurisdiction   varchar NOT NULL,
      rights_classification  varchar,
      rights_evidence_cid    varchar,
      blocked_reasons_json   varchar,
      status                 varchar NOT NULL,
      created_at             varchar NOT NULL,
      sensitivity_ord        int NOT NULL DEFAULT 1,
      owner_did              varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_shot (
      vertex_id          varchar PRIMARY KEY,
      run_vertex_id      varchar NOT NULL,
      work_id            varchar NOT NULL,
      shot_index         int NOT NULL,
      start_ms           bigint NOT NULL,
      end_ms             bigint NOT NULL,
      keyframe_cid       varchar,
      shot_metadata_cid  varchar,
      created_at         varchar NOT NULL,
      sensitivity_ord    int NOT NULL DEFAULT 1,
      owner_did          varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_derivative_asset (
      vertex_id                       varchar PRIMARY KEY,
      run_vertex_id                   varchar NOT NULL,
      work_id                         varchar NOT NULL,
      master_video_cid                varchar,
      poster_cid                      varchar,
      publication_manifest_cid        varchar,
      timed_text_cid                  varchar,
      subtitle_manifest_cid           varchar,
      dubbed_audio_manifest_cid       varchar,
      localized_package_manifest_cid  varchar,
      target_languages_json           varchar,
      rights_evidence_cid             varchar,
      status                          varchar NOT NULL,
      created_at                      varchar NOT NULL,
      sensitivity_ord                 int NOT NULL DEFAULT 1,
      owner_did                       varchar,
      org_id                          varchar,
      user_id                         varchar,
      actor_id                        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_localization_asset (
      vertex_id                       varchar PRIMARY KEY,
      derivative_vertex_id            varchar NOT NULL,
      work_id                         varchar NOT NULL,
      lang                            varchar NOT NULL,
      subtitle_cid                    varchar,
      dubbed_audio_cid                varchar,
      localized_video_cid             varchar,
      voice_policy                    varchar,
      writing_direction               varchar,
      quality_score                   double precision NOT NULL DEFAULT 0.0,
      manifest_cid                    varchar,
      created_at                      varchar NOT NULL,
      sensitivity_ord                 int NOT NULL DEFAULT 1,
      owner_did                       varchar,
      org_id                          varchar,
      user_id                         varchar,
      actor_id                        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_pd_color_publication (
      vertex_id                       varchar PRIMARY KEY,
      derivative_vertex_id            varchar NOT NULL,
      work_id                         varchar NOT NULL,
      publication_cid                 varchar,
      publish_jurisdiction            varchar NOT NULL,
      publication_manifest_cid        varchar,
      localized_package_manifest_cid  varchar,
      rights_evidence_cid             varchar,
      status                          varchar NOT NULL,
      takedown_state                  varchar NOT NULL DEFAULT 'none',
      published_at                    varchar,
      created_at                      varchar NOT NULL,
      sensitivity_ord                 int NOT NULL DEFAULT 1,
      owner_did                       varchar,
      org_id                          varchar,
      user_id                         varchar,
      actor_id                        varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_pd_color_run_work ON vertex_pd_color_run (work_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_pd_color_run_source_ipfs ON vertex_pd_color_run (source_ipfs_cid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_pd_color_source_asset_ipfs ON vertex_pd_color_source_asset (source_ipfs_cid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_pd_color_derivative_run ON vertex_pd_color_derivative_asset (run_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_pd_color_localization_lang ON vertex_pd_color_localization_asset (lang)`.execute(db);
}

async function insertProcessDef(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>): Promise<void> {
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

export async function up(db: Kysely<unknown>): Promise<void> {
  await createTables(db);
  await insertProcessDef(db);
  await insertBinding(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_publication`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_localization_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_derivative_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_shot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_rights_review`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_source_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_pd_color_work`.execute(db);
}
