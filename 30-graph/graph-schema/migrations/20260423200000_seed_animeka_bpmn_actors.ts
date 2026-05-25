import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2604231328 — animeka 12-stage BPMN pipeline registration.
 *
 * Seeds 13 BPMN process definitions + 13 NSID bindings so the
 * bpmn-dispatcher F5 watcher ships them to Zeebe and the per-stage
 * XRPC endpoints (`POST dispatcher.etzhayyim.com:8080/xrpc/app.etzhayyim.apps.animeka.*`)
 * go live within ~30 s of apply.
 *
 * 12 stages (1-12 of the production pipeline) + 1 companion (chat):
 *
 *   1  generateScript         Claude deep → Qwen mid structure → insert + social
 *   2  breakdownScene         Qwen mid → plan row
 *   3  generateStoryboard     Claude deep → ComfyUI (Animagine XL 512²) × per-candidate
 *   4  generateLayout         Qwen mid → ComfyUI (Animagine + ControlNet-depth 1024²)
 *   5  generateKeyframe       ComfyUI (Animagine + ControlNet-pose + IPAdapter)
 *   6  generateInbetween      Qwen mid easing → ComfyUI (WAN 5B i2v)
 *   7  designColorModel       Qwen mid palette → ComfyUI (color chart)
 *   8  autoTrace              ComfyUI (ControlNet-lineart + palette cond)
 *   9  generateBackground     Claude deep → ComfyUI (FLUX.1-dev 1920×1080)
 *  10  renderComposite        Qwen mid FX → ComfyUI (layer composite + camera move)
 *  11  generateSoundCue       XOR on trackType → SBV2 / StableAudio / MusicGen
 *  12  publishEpisode         db.select cuts → ComfyUI master → pds.dispatch
 *  +   chat                   llm.chat (tier knob, mid default)
 */

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
};

const OWNER_DID = "did:web:animeka.etzhayyim.com";
const createdAt = "2026-04-23T20:00:00Z";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readBpmn(fileName: string): string {
  return readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/animeka", fileName),
    "utf8",
  );
}

const stages: Array<{
  slug: string;
  bpmnProcessId: string;
  file: string;
  nsid: string;
  bindingSlug: string;
}> = [
  { slug: "animeka-generate-script-v1",      bpmnProcessId: "animeka_generate_script",      file: "generateScript.bpmn",      nsid: "app.etzhayyim.apps.animeka.generateScript",     bindingSlug: "animeka-generateScript-v1" },
  { slug: "animeka-breakdown-scene-v1",      bpmnProcessId: "animeka_breakdown_scene",      file: "breakdownScene.bpmn",      nsid: "app.etzhayyim.apps.animeka.breakdownScene",     bindingSlug: "animeka-breakdownScene-v1" },
  { slug: "animeka-generate-storyboard-v1",  bpmnProcessId: "animeka_generate_storyboard",  file: "generateStoryboard.bpmn",  nsid: "app.etzhayyim.apps.animeka.generateStoryboard", bindingSlug: "animeka-generateStoryboard-v1" },
  { slug: "animeka-generate-layout-v1",      bpmnProcessId: "animeka_generate_layout",      file: "generateLayout.bpmn",      nsid: "app.etzhayyim.apps.animeka.generateLayout",     bindingSlug: "animeka-generateLayout-v1" },
  { slug: "animeka-generate-keyframe-v1",    bpmnProcessId: "animeka_generate_keyframe",    file: "generateKeyframe.bpmn",    nsid: "app.etzhayyim.apps.animeka.generateKeyframe",   bindingSlug: "animeka-generateKeyframe-v1" },
  { slug: "animeka-generate-inbetween-v1",   bpmnProcessId: "animeka_generate_inbetween",   file: "generateInbetween.bpmn",   nsid: "app.etzhayyim.apps.animeka.generateInbetween",  bindingSlug: "animeka-generateInbetween-v1" },
  { slug: "animeka-design-color-model-v1",   bpmnProcessId: "animeka_design_color_model",   file: "designColorModel.bpmn",    nsid: "app.etzhayyim.apps.animeka.designColorModel",   bindingSlug: "animeka-designColorModel-v1" },
  { slug: "animeka-auto-trace-cut-v1",       bpmnProcessId: "animeka_auto_trace_cut",       file: "autoTraceCut.bpmn",        nsid: "app.etzhayyim.apps.animeka.autoTrace",          bindingSlug: "animeka-autoTrace-v1" },
  { slug: "animeka-generate-background-v1",  bpmnProcessId: "animeka_generate_background",  file: "generateBackground.bpmn",  nsid: "app.etzhayyim.apps.animeka.generateBackground", bindingSlug: "animeka-generateBackground-v1" },
  { slug: "animeka-render-composite-v1",     bpmnProcessId: "animeka_render_composite",     file: "renderComposite.bpmn",     nsid: "app.etzhayyim.apps.animeka.renderComposite",    bindingSlug: "animeka-renderComposite-v1" },
  { slug: "animeka-generate-sound-cue-v1",   bpmnProcessId: "animeka_generate_sound_cue",   file: "generateSoundCue.bpmn",    nsid: "app.etzhayyim.apps.animeka.generateSoundCue",   bindingSlug: "animeka-generateSoundCue-v1" },
  { slug: "animeka-publish-episode-v1",      bpmnProcessId: "animeka_publish_episode",      file: "publishEpisode.bpmn",      nsid: "app.etzhayyim.apps.animeka.publishEpisode",     bindingSlug: "animeka-publishEpisode-v1" },
  { slug: "animeka-chat-v1",                 bpmnProcessId: "animeka_chat",                 file: "chat.bpmn",                nsid: "app.etzhayyim.apps.animeka.chat",               bindingSlug: "animeka-chat-v1" },
];

const processSeeds: ProcessSeed[] = stages.map((s) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${s.slug}`,
  bpmnProcessId: s.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/ai/gftd/animeka/${s.file}`,
}));

const bindingSeeds: BindingSeed[] = stages.map((s) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${s.bindingSlug}`,
  nsid: s.nsid,
  bpmnProcessId: s.bpmnProcessId,
}));

export async function up(db: Kysely<unknown>): Promise<void> {
  // RisingWave sql_parser rejects `ON CONFLICT`. Use SELECT-then-INSERT
  // for idempotent re-runs. Pattern documented in ADR-2604241342.
  for (let i = 0; i < stages.length; i++) {
    const stage = stages[i];
    const seed = processSeeds[i];
    const xml = readBpmn(stage.file);
    const existing = await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId} LIMIT 1
    `.execute(db);
    if (existing.rows.length > 0) continue;
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, bpmn_process_id, version, xml, status,
        owner_did, source_path, created_at
      ) VALUES (
        ${seed.vertexId}, ${stage.bpmnProcessId}, 1, ${xml}, 'active',
        ${OWNER_DID}, ${seed.sourcePath}, ${createdAt}::timestamptz
      )
    `.execute(db);
  }

  for (const binding of bindingSeeds) {
    const existing = await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${binding.vertexId} LIMIT 1
    `.execute(db);
    if (existing.rows.length > 0) continue;
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, nsid, bpmn_process_id, status,
        owner_did, result_timeout_ms, created_at
      ) VALUES (
        ${binding.vertexId}, ${binding.nsid}, ${binding.bpmnProcessId}, 'active',
        ${OWNER_DID}, 600000, ${createdAt}::timestamptz
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const binding of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${binding.vertexId}`.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
}
