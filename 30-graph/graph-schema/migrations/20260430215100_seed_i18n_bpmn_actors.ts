import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; fn: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:i18n.etzhayyim.com";
const createdAt = "2026-04-30T21:51:00+09:00";
const actorId = "sys.bpmn.seed.i18n";
const writeTableAllowlist = [
  "vertex_i18n_project",
  "vertex_i18n_project_translation",
  "vertex_i18n_translation_memory",
  "vertex_i18n_text_node",
  "vertex_i18n_credit_job",
  "edge_i18n_project_translation",
  "edge_i18n_translation_text",
  "edge_i18n_text_language",
].join(",");

const seeds: Seed[] = [
  { slug: "register-project", op: "registerProject", fn: "registerProject", processId: "i18n_register_project", writeTableAllowlist },
  { slug: "translate-batch", op: "translateBatch", fn: "translateBatch", processId: "i18n_translate_batch", writeTableAllowlist },
  { slug: "export-messages", op: "exportMessages", fn: "exportMessages", processId: "i18n_export_messages", writeTableAllowlist: "" },
  { slug: "translate-on-demand", op: "translateOnDemand", fn: "translateOnDemand", processId: "i18n_translate_on_demand", writeTableAllowlist },
  { slug: "translate-page", op: "translatePage", fn: "translatePage", processId: "i18n_translate_page", writeTableAllowlist },
  { slug: "translate-message", op: "translateMessage", fn: "translateMessage", processId: "i18n_translate_message", writeTableAllowlist },
  { slug: "translate-signal", op: "translateSignal", fn: "translateSignal", processId: "i18n_translate_signal", writeTableAllowlist },
  { slug: "widget-lookup", op: "widgetLookup", fn: "widgetLookup", processId: "i18n_widget_lookup", writeTableAllowlist: "" },
  { slug: "widget-suggest", op: "widgetSuggest", fn: "widgetSuggest", processId: "i18n_widget_suggest", writeTableAllowlist: "" },
  { slug: "widget-approve", op: "widgetApprove", fn: "widgetApprove", processId: "i18n_widget_approve", writeTableAllowlist },
  { slug: "get-language-registry", op: "getLanguageRegistry", fn: "getLanguageRegistry", processId: "i18n_get_language_registry", writeTableAllowlist: "" },
  { slug: "get-translation-status", op: "getTranslationStatus", fn: "getTranslationStatus", processId: "i18n_get_translation_status", writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/i18n/${s.fn}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/i18n-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/i18n-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
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
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.i18n.${s.op}`}, ${s.processId}, 1,
        30000, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
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
