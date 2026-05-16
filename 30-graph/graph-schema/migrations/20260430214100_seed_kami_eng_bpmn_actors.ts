import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; nsid: string; task: string; fn: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:eng-kami.gftd.ai";
const createdAt = "2026-04-30T21:41:00+09:00";
const actorId = "sys.bpmn.seed.kami-eng";
const writeTableAllowlist = [
  "vertex_kami_eng_eda_schematic",
  "vertex_kami_eng_cad_model",
  "vertex_kami_eng_cad_feature",
  "vertex_kami_eng_cam_job",
  "vertex_kami_eng_rtl_module_ref",
  "vertex_kami_eng_rtl_simulation",
  "vertex_kami_eng_cae_analysis",
  "edge_kami_eng_cad_model_feature",
  "edge_kami_eng_cad_model_cam_job",
  "edge_kami_eng_rtl_module_simulation",
  "edge_kami_eng_cad_model_cae_analysis",
].join(",");

const seeds: Seed[] = [
  { slug: "eda-create-schematic", nsid: "ai.gftd.apps.kami.eda.createSchematic", task: "eda.createSchematic", fn: "edaCreateSchematic", processId: "kami_eng_eda_create_schematic", writeTableAllowlist },
  { slug: "eda-run-erc", nsid: "ai.gftd.apps.kami.eda.runErc", task: "eda.runErc", fn: "edaRunErc", processId: "kami_eng_eda_run_erc", writeTableAllowlist: "" },
  { slug: "eda-export-gerber", nsid: "ai.gftd.apps.kami.eda.exportGerber", task: "eda.exportGerber", fn: "edaExportGerber", processId: "kami_eng_eda_export_gerber", writeTableAllowlist: "" },
  { slug: "cad-create-model", nsid: "ai.gftd.apps.kami.cad.createModel", task: "cad.createModel", fn: "cadCreateModel", processId: "kami_eng_cad_create_model", writeTableAllowlist },
  { slug: "cad-add-feature", nsid: "ai.gftd.apps.kami.cad.addFeature", task: "cad.addFeature", fn: "cadAddFeature", processId: "kami_eng_cad_add_feature", writeTableAllowlist },
  { slug: "cad-export-step", nsid: "ai.gftd.apps.kami.cad.exportStep", task: "cad.exportStep", fn: "cadExportStep", processId: "kami_eng_cad_export_step", writeTableAllowlist: "" },
  { slug: "cam-create-job", nsid: "ai.gftd.apps.kami.cam.createJob", task: "cam.createJob", fn: "camCreateJob", processId: "kami_eng_cam_create_job", writeTableAllowlist },
  { slug: "cam-generate-gcode", nsid: "ai.gftd.apps.kami.cam.generateGcode", task: "cam.generateGcode", fn: "camGenerateGcode", processId: "kami_eng_cam_generate_gcode", writeTableAllowlist: "" },
  { slug: "rtl-parse-hdl", nsid: "ai.gftd.apps.kami.rtl.parseHdl", task: "rtl.parseHdl", fn: "rtlParseHdl", processId: "kami_eng_rtl_parse_hdl", writeTableAllowlist: "" },
  { slug: "rtl-simulate", nsid: "ai.gftd.apps.kami.rtl.simulate", task: "rtl.simulate", fn: "rtlSimulate", processId: "kami_eng_rtl_simulate", writeTableAllowlist },
  { slug: "rtl-synthesize", nsid: "ai.gftd.apps.kami.rtl.synthesize", task: "rtl.synthesize", fn: "rtlSynthesize", processId: "kami_eng_rtl_synthesize", writeTableAllowlist: "" },
  { slug: "cae-generate-mesh", nsid: "ai.gftd.apps.kami.cae.generateMesh", task: "cae.generateMesh", fn: "caeGenerateMesh", processId: "kami_eng_cae_generate_mesh", writeTableAllowlist: "" },
  { slug: "cae-run-analysis", nsid: "ai.gftd.apps.kami.cae.runAnalysis", task: "cae.runAnalysis", fn: "caeRunAnalysis", processId: "kami_eng_cae_run_analysis", writeTableAllowlist },
  { slug: "cae-get-results", nsid: "ai.gftd.apps.kami.cae.getResults", task: "cae.getResults", fn: "caeGetResults", processId: "kami_eng_cae_get_results", writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/kamiEng/${s.fn}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kami-eng-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/kami-eng-${s.slug}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
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
