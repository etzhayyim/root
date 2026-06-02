import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * adsk.etzhayyim.com BPMN-as-actor seeding (ADR-0056) + Phase 1 HF dataset
 * catalog seed.
 *
 * Single timer-start BPMN `adsk_ingest_dataset` (R/P30D) that calls
 * the pyzeebe primitive `adsk.dataset.ingestAll`. No XRPC binding —
 * autonomous monthly cadence; manual one-shot via direct primitive
 * call (`task_adsk_dataset_ingest(slug=...)`).
 *
 * Phase 1 catalog (5 ADSKAILab datasets):
 *   Zero-To-CAD-100k                 parquet 101,516 rows  Apache-2.0
 *   Zero-To-CAD-1m                   parquet 1,000,000 rows Apache-2.0
 *   LLM-narrative-planning-taskset   3 zip archives        MIT
 *   dsl_icl_eval-2025_01_21_113247   parquet ~10 rows      —
 *   dsl_icl_eval-2025_01_21_112645   parquet ~500 rows     —
 *
 * codeparrot_megatron is excluded (Megatron .bin/.idx pre-tokenized,
 * not text-readable). 3D / voxel / point-cloud datasets (ABC-1M,
 * Make-A-Shape-*, WaLa-*) are Phase 2 (B2 blob storage).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

type CatalogSeed = {
  slug: string;
  org: string;
  name: string;
  modality: string;
  license: string;
  hfUrl: string;
  taskCategories: string;
  tags: string;
  rowCountExpected: number | null;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-05T22:00:00Z";
const ownerDid = "did:web:adsk.etzhayyim.com";
const actorTag = "sys.bpmn.seed.adsk-hf-ingest";

const processSeeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v1",
    bpmnProcessId: "adsk_ingest_dataset",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/adsk/ingestAdskDataset.bpmn",
    ownerDid,
  },
];

const catalogSeeds: CatalogSeed[] = [
  {
    slug: "ADSKAILab/Zero-To-CAD-100k",
    org: "ADSKAILab",
    name: "Zero-To-CAD-100k",
    modality: "code+image",
    license: "apache-2.0",
    hfUrl: "https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-100k",
    taskCategories: "text-to-3d,image-to-3d",
    tags: "CAD,CadQuery,synthetic-data,construction-sequence,parametric-CAD,curated",
    rowCountExpected: 101516,
  },
  {
    slug: "ADSKAILab/Zero-To-CAD-1m",
    org: "ADSKAILab",
    name: "Zero-To-CAD-1m",
    modality: "code+image",
    license: "apache-2.0",
    hfUrl: "https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m",
    taskCategories: "text-to-3d,image-to-3d",
    tags: "CAD,CadQuery,synthetic-data,construction-sequence,parametric-CAD",
    rowCountExpected: 1000000,
  },
  {
    slug: "ADSKAILab/LLM-narrative-planning-taskset",
    org: "ADSKAILab",
    name: "LLM-narrative-planning-taskset",
    modality: "text",
    license: "mit",
    hfUrl: "https://huggingface.co/datasets/ADSKAILab/LLM-narrative-planning-taskset",
    taskCategories: "",
    tags: "narrative-planning,story-generation,zip-archive",
    rowCountExpected: null,
  },
  {
    slug: "ADSKAILab/dsl_icl_eval-2025_01_21_113247_model-anthropic-claude-3.5-sonnet_fewshot-5",
    org: "ADSKAILab",
    name: "dsl_icl_eval-claude-3.5-sonnet-fewshot-5",
    modality: "text",
    license: "",
    hfUrl: "https://huggingface.co/datasets/ADSKAILab/dsl_icl_eval-2025_01_21_113247_model-anthropic-claude-3.5-sonnet_fewshot-5",
    taskCategories: "",
    tags: "DSL,IFC,architecture,eval,parquet",
    rowCountExpected: 10,
  },
  {
    slug: "ADSKAILab/dsl_icl_eval-2025_01_21_112645_model-openai-gpt-4o-2024-11-20_fewshot-5",
    org: "ADSKAILab",
    name: "dsl_icl_eval-gpt-4o-fewshot-5",
    modality: "text",
    license: "",
    hfUrl: "https://huggingface.co/datasets/ADSKAILab/dsl_icl_eval-2025_01_21_112645_model-openai-gpt-4o-2024-11-20_fewshot-5",
    taskCategories: "",
    tags: "DSL,IFC,architecture,eval,parquet",
    rowCountExpected: 500,
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertCatalog(db: Kysely<unknown>, c: CatalogSeed): Promise<void> {
  const vertexId = `at://${ownerDid}/com.etzhayyim.apps.adsk.dataset/${c.slug.replace(/[^a-zA-Z0-9]/g, "-")}`;
  const rowCountExpectedSql =
    c.rowCountExpected === null
      ? sql`CAST(NULL AS bigint)`
      : sql`CAST(${c.rowCountExpected} AS bigint)`;
  await sql`
    INSERT INTO vertex_hf_dataset (
      vertex_id, owner_did, sensitivity_ord,
      slug, org, name, modality, license, hf_url, task_categories, tags,
      row_count_expected, row_count_ingested, last_synced_at, status,
      created_at, org_id, user_id, actor_id
    )
    SELECT
      ${vertexId}, ${ownerDid}, CAST(0 AS int),
      ${c.slug}, ${c.org}, ${c.name}, ${c.modality}, ${c.license}, ${c.hfUrl}, ${c.taskCategories}, ${c.tags},
      ${rowCountExpectedSql}, CAST(0 AS bigint), CAST(NULL AS varchar), 'active',
      ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = ${vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const c of catalogSeeds) await insertCatalog(db, c);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const c of catalogSeeds) {
    const vertexId = `at://${ownerDid}/com.etzhayyim.apps.adsk.dataset/${c.slug.replace(/[^a-zA-Z0-9]/g, "-")}`;
    await sql`DELETE FROM vertex_hf_dataset WHERE vertex_id = ${vertexId}`.execute(db);
  }
  for (const s of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
}
