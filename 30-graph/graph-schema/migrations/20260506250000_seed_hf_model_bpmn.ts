import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for HuggingFace Hub model scan BPMN (ADR-0056).
// Also seeds 3 starter vertex_hfhub_filter rows for models:
//   - llm-popular-models   : text-generation + image-text-to-text, 1K+ downloads
//   - japanese-models       : language:ja, any task
//   - open-license-models   : Apache-2.0 or MIT licensed models

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-06T23:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const INGEST_DID = "did:web:ingest.etzhayyim.com";

const PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/hf-model-scan-v1";
const BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/hf-model-scan-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/hf/modelScan.bpmn"),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VID}, ${OWNER_DID}, 'hf_model_scan', 1,
      ${xml}, CAST(${size} AS integer),
      '00-contracts/bpmn/ai/gftd/hf/modelScan.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.hf'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VID}, ${OWNER_DID}, 'hf_model_scan',
      'app.etzhayyim.apps.hf.modelScan',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.hf'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);

  // ── Starter filter: popular LLM / VLM models ──────────────────────────────
  await sql`
    INSERT INTO vertex_hfhub_filter
      (vertex_id, created_date, slug, display_name, description,
       filter_tags, filter_tasks, filter_languages, filter_license,
       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)
    SELECT
      'hf:filter:llm-popular-models', '2026-05-06'::date,
      'llm-popular-models',
      'Popular LLM & VLM models',
      'text-generation and image-text-to-text models with 1K+ monthly downloads',
      '[]',
      '["task_categories:text-generation","task_categories:image-text-to-text"]',
      '[]',
      NULL, 1000, TRUE, TRUE, 'model',
      ${INGEST_DID}, '2026-05-06 23:00:00'::timestamp
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = 'hf:filter:llm-popular-models')
  `.execute(db);

  // ── Starter filter: Japanese language models ───────────────────────────────
  await sql`
    INSERT INTO vertex_hfhub_filter
      (vertex_id, created_date, slug, display_name, description,
       filter_tags, filter_tasks, filter_languages, filter_license,
       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)
    SELECT
      'hf:filter:japanese-models', '2026-05-06'::date,
      'japanese-models',
      'Japanese language models',
      'Models tagged with language:ja, any task category',
      '["language:ja"]',
      '[]',
      '["ja"]',
      NULL, 100, TRUE, TRUE, 'model',
      ${INGEST_DID}, '2026-05-06 23:00:00'::timestamp
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = 'hf:filter:japanese-models')
  `.execute(db);

  // ── Starter filter: open-licensed models (Apache-2.0) ─────────────────────
  await sql`
    INSERT INTO vertex_hfhub_filter
      (vertex_id, created_date, slug, display_name, description,
       filter_tags, filter_tasks, filter_languages, filter_license,
       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)
    SELECT
      'hf:filter:apache2-models', '2026-05-06'::date,
      'apache2-models',
      'Apache-2.0 licensed models',
      'Models with Apache-2.0 license, 500+ monthly downloads',
      '[]', '[]', '[]',
      'apache-2.0', 500, TRUE, TRUE, 'model',
      ${INGEST_DID}, '2026-05-06 23:00:00'::timestamp
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = 'hf:filter:apache2-models')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_hfhub_filter WHERE vertex_id IN (
    'hf:filter:llm-popular-models','hf:filter:japanese-models','hf:filter:apache2-models'
  )`.execute(db);
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
