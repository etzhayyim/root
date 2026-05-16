import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for HuggingFace Hub dataset catalog scan BPMN.
// F5 watcher deploys to Zeebe within 30s of INSERT (ADR-0056).
// Also seeds:
//   - vertex_bpmn_lexicon_binding for ai.gftd.apps.hf.datasetScan
//   - 2 starter vertex_hfhub_filter rows (NLP-ja + text-classification)

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-06T22:00:00Z";
const OWNER_DID = "did:web:bpmn.gftd.ai";
const INGEST_DID = "did:web:ingest.gftd.ai";

const PROCESS_VID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/hf-dataset-scan-v1";
const BINDING_VID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/hf-dataset-scan-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── BPMN process def ───────────────────────────────────────────────────────
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/hf/datasetScan.bpmn"),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VID}, ${OWNER_DID}, 'hf_dataset_scan', 1,
      ${xml}, CAST(${size} AS integer),
      '00-contracts/bpmn/ai/gftd/hf/datasetScan.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.hf'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  // ── Lexicon binding ────────────────────────────────────────────────────────
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VID}, ${OWNER_DID}, 'hf_dataset_scan',
      'ai.gftd.apps.hf.datasetScan',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.hf'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);

  // ── Starter filter: Japanese NLP datasets ──────────────────────────────────
  await sql`
    INSERT INTO vertex_hfhub_filter
      (vertex_id, created_date, slug, display_name, description,
       filter_tags, filter_tasks, filter_languages,
       filter_license, min_downloads, exclude_private, enabled,
       actor_did, created_at)
    SELECT
      'hf:filter:nlp-ja', '2026-05-06'::date,
      'nlp-ja',
      'Japanese NLP datasets',
      'Datasets with language:ja tag for Japanese NLP tasks',
      '["language:ja"]',
      '["task_categories:text-classification","task_categories:question-answering","task_categories:summarization"]',
      '["ja"]',
      NULL, 100, TRUE, TRUE,
      ${INGEST_DID}, '2026-05-06 22:00:00'::timestamp
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = 'hf:filter:nlp-ja')
  `.execute(db);

  // ── Starter filter: general text classification (high-download) ────────────
  await sql`
    INSERT INTO vertex_hfhub_filter
      (vertex_id, created_date, slug, display_name, description,
       filter_tags, filter_tasks, filter_languages,
       filter_license, min_downloads, exclude_private, enabled,
       actor_did, created_at)
    SELECT
      'hf:filter:text-clf-popular', '2026-05-06'::date,
      'text-clf-popular',
      'Popular text classification datasets',
      'Text classification datasets with 1K+ monthly downloads',
      '[]',
      '["task_categories:text-classification"]',
      '[]',
      NULL, 1000, TRUE, TRUE,
      ${INGEST_DID}, '2026-05-06 22:00:00'::timestamp
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = 'hf:filter:text-clf-popular')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_hfhub_filter WHERE vertex_id IN ('hf:filter:nlp-ja','hf:filter:text-clf-popular')`.execute(db);
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
