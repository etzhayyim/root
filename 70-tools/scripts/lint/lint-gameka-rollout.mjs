#!/usr/bin/env node
/**
 * lint-gameka-rollout.mjs (P12) — single-shot structural sanity check
 * for the gameka.etzhayyim.com actor rollout (ADR 2604250900).
 *
 * Runs in CI + locally. Exits non-zero on any drift between the
 * artefacts that have to be in lockstep before `proposeGame` will
 * reach `publishGame` end-to-end. Pure stdlib (no node deps), reads
 * paths only — no compilation, no DB.
 *
 * Checks (one section per concern):
 *
 *   1. Lexicons present + parse + correct id.
 *      9 NSIDs under `00-contracts/lexicons/com/etzhayyim/apps/gameka/`.
 *
 *   2. BPMNs present + parse + claim the right NSID.
 *      5 process files under `00-contracts/bpmn/com/etzhayyim/gameka/`.
 *
 *   3. Migrations present in expected order.
 *      4 timestamp-prefixed files under `30-graph/graph-schema/migrations/`
 *      starting with `20260425{0900..1300}00_*`.
 *
 *   4. PDS routing-table contains all 5 gameka NSIDs.
 *      `50-infra/cloudflare/workers/atproto/src/routing-table.ts` must
 *      include each XRPC method as an exact-match entry routed to
 *      `BPMN_URL`. Without this, requests 404 to the Layer 10 catch-all
 *      (gameka has no Worker).
 *
 *   5. zeebe-worker registers all 4 gameka task types.
 *      `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py`
 *      must declare:
 *        - com.etzhayyim.agent.gameka.studio
 *        - gameka.codegen.renderKamiApp
 *        - gameka.avatar.render
 *        - com.etzhayyim.agent.gameka.visualCritic
 *
 *   6. gameka-build-runner Dockerfile COPY paths still exist.
 *      Drift between repo layout and build-runner image breaks
 *      generateGame at the wasm-pack step.
 *
 *   7. gameka-playtest-shell Worker reads the columns publishGame
 *      writes.
 *      worker.ts SELECT must include the columns the BPMN's
 *      generic.db.insert wrote — silent mismatch would 404 a title
 *      that just published.
 */

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { resolve, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const errors = [];
const ok = (msg) => console.log(`  ok   ${msg}`);
const fail = (msg) => { errors.push(msg); console.error(`  FAIL ${msg}`); };
const section = (title) => console.log(`\n=== ${title} ===`);

function read(rel) {
  const path = resolve(REPO, rel);
  if (!existsSync(path)) {
    fail(`missing file: ${rel}`);
    return null;
  }
  return readFileSync(path, "utf8");
}

// ─── 1. Lexicons ────────────────────────────────────────────────────────

section("lexicons");
const LEXICON_DIR = "00-contracts/lexicons/com/etzhayyim/apps/gameka";
const EXPECTED_LEXICONS = [
  ["proposeGame.json",   "com.etzhayyim.apps.gameka.proposeGame",   "procedure"],
  ["generateGame.json",  "com.etzhayyim.apps.gameka.generateGame",  "procedure"],
  ["playtestGame.json",  "com.etzhayyim.apps.gameka.playtestGame",  "procedure"],
  ["publishGame.json",   "com.etzhayyim.apps.gameka.publishGame",   "procedure"],
  ["tickStudio.json",    "com.etzhayyim.apps.gameka.tickStudio",    "procedure"],
  ["gameSpec.json",      "com.etzhayyim.apps.gameka.gameSpec",      "record"],
  ["buildArtifact.json", "com.etzhayyim.apps.gameka.buildArtifact", "record"],
  ["gameQa.json",        "com.etzhayyim.apps.gameka.gameQa",        "record"],
  ["gameTitle.json",     "com.etzhayyim.apps.gameka.gameTitle",     "record"],
];
for (const [file, id, type] of EXPECTED_LEXICONS) {
  const raw = read(`${LEXICON_DIR}/${file}`);
  if (!raw) continue;
  let j;
  try { j = JSON.parse(raw); } catch (e) { fail(`${file}: invalid JSON: ${e.message}`); continue; }
  if (j.id !== id) fail(`${file}: id="${j.id}" expected "${id}"`);
  else if (j.defs?.main?.type !== type) fail(`${file}: defs.main.type="${j.defs?.main?.type}" expected "${type}"`);
  else ok(`${file}  id=${id}  type=${type}`);
}

// ─── 2. BPMNs ───────────────────────────────────────────────────────────

section("BPMNs");
const BPMN_DIR = "00-contracts/bpmn/com/etzhayyim/gameka";
const EXPECTED_BPMNS = [
  ["proposeGame.bpmn",   "com.etzhayyim.apps.gameka.proposeGame"],
  ["generateGame.bpmn",  "com.etzhayyim.apps.gameka.generateGame"],
  ["playtestGame.bpmn",  "com.etzhayyim.apps.gameka.playtestGame"],
  ["publishGame.bpmn",   "com.etzhayyim.apps.gameka.publishGame"],
  ["tickStudio.bpmn",    "com.etzhayyim.apps.gameka.tickStudio"],
];
for (const [file, expectedNsid] of EXPECTED_BPMNS) {
  const raw = read(`${BPMN_DIR}/${file}`);
  if (!raw) continue;
  // Quick well-formedness check: every <bpmn:process> has a
  // <bpmn:documentation> with a JSON object containing the NSID. The
  // sync-bpmn-actors.py script reads it the same way.
  const docMatch = raw.match(/<bpmn:documentation>\s*([\s\S]*?)\s*<\/bpmn:documentation>/);
  if (!docMatch) { fail(`${file}: missing <bpmn:documentation>`); continue; }
  let meta;
  try { meta = JSON.parse(docMatch[1]); } catch (e) {
    fail(`${file}: <bpmn:documentation> not JSON: ${e.message}`);
    continue;
  }
  if (meta.nsid !== expectedNsid) fail(`${file}: nsid=${meta.nsid} expected ${expectedNsid}`);
  else ok(`${file}  nsid=${expectedNsid}  v${meta.version ?? "?"}`);
}

// ─── 3. Migrations ──────────────────────────────────────────────────────

section("migrations");
const MIG_DIR = "30-graph/graph-schema/migrations";
const EXPECTED_MIGRATIONS = [
  "20260425090000_vertex_gameka_studio.ts",
  "20260425100000_vertex_gameka_artifact_js_url.ts",
  "20260425110000_vertex_gameka_studio_config.ts",
  "20260425120000_seed_gameka_merge_specs.ts",
  "20260425130000_vertex_gameka_title_avatar_data_uri.ts",
];
for (const file of EXPECTED_MIGRATIONS) {
  const raw = read(`${MIG_DIR}/${file}`);
  if (!raw) continue;
  if (!raw.includes("export async function up")) fail(`${file}: missing up()`);
  else if (!raw.includes("export async function down")) fail(`${file}: missing down()`);
  else ok(`${file}  up()+down() present`);
}

// ─── 4. PDS routing table ───────────────────────────────────────────────

section("PDS routing table");
const ROUTING = read("50-infra/cloudflare/workers/atproto/src/routing-table.ts");
if (ROUTING) {
  for (const [, nsid] of EXPECTED_BPMNS) {
    if (!ROUTING.includes(`"${nsid}"`)) fail(`routing-table.ts: missing exact-match for ${nsid}`);
    else ok(`exact-match entry for ${nsid}`);
  }
}

// ─── 5. zeebe-worker registrations ──────────────────────────────────────

section("zeebe-worker task registrations");
const ZBW = read("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py");
if (ZBW) {
  const TASKS = [
    "com.etzhayyim.agent.gameka.studio",
    "com.etzhayyim.agent.gameka.visualCritic",
    "gameka.codegen.renderKamiApp",
    "gameka.avatar.render",
  ];
  for (const t of TASKS) {
    const rx = new RegExp(`task_type=["']${t.replace(/\./g, "\\.")}["']`);
    if (!rx.test(ZBW)) fail(`zeebe_worker_main.py: missing worker.task(task_type="${t}")`);
    else ok(`registered: ${t}`);
  }
}

// ─── 6. gameka-build-runner Dockerfile COPY paths ───────────────────────

section("gameka-build-runner COPY paths");
const DOCKER = read("50-infra/vultr/gameka-build-runner/Dockerfile");
if (DOCKER) {
  // Extract every COPY <src> <dst> line. The runner pulls in the
  // engine workspace + the canonical codegen module.
  const copyLines = [...DOCKER.matchAll(/^COPY\s+(\S+)\s+/gm)].map((m) => m[1]);
  for (const src of copyLines) {
    const path = resolve(REPO, src);
    if (!existsSync(path)) fail(`Dockerfile COPY src missing: ${src}`);
    else ok(`COPY src exists: ${src}`);
  }
}

// ─── 7. playtest-shell Worker reads what publishGame writes ─────────────

section("playtest-shell ↔ publishGame column alignment");
const SHELL = read("50-infra/cloudflare/workers/gameka-playtest-shell/src/worker.ts");
const PUBLISH = read("00-contracts/bpmn/com/etzhayyim/gameka/publishGame.bpmn");
if (SHELL && PUBLISH) {
  // The Worker reads vertex_gameka_title columns; publishGame writes
  // the same columns. Mismatch = 404 on /play/{slug}.
  const REQUIRED_COLS = [
    "slug",
    "sub_did",
    "title_id",
    "parent_artifact_id",
    "avatar_data_uri",
  ];
  for (const col of REQUIRED_COLS) {
    const inWorker = SHELL.includes(`"${col}"`);
    const inPublish = PUBLISH.includes(col + ":");
    if (!inWorker) fail(`worker.ts SELECT missing column: ${col}`);
    else if (!inPublish) fail(`publishGame.bpmn INSERT missing column: ${col}`);
    else ok(`column round-trip: ${col}`);
  }
}

// ─── Result ─────────────────────────────────────────────────────────────

console.log();
if (errors.length) {
  console.error(`✗ ${errors.length} error${errors.length === 1 ? "" : "s"}`);
  for (const e of errors) console.error(`    ${e}`);
  process.exit(1);
} else {
  console.log("✓ gameka rollout invariants intact");
}
