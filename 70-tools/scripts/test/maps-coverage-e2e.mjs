#!/usr/bin/env node
// maps-coverage-e2e.mjs — offline contract test for the 3-piece coverage pipeline
// (advanceCoverage / refreshCoverageStats / runCoverageJob).
//
// Catches drift the per-file syntax checks miss:
//   (A) BPMN <bpmn:documentation> NSID vs filename-derived NSID (sync-bpmn-actors convention)
//   (B) BPMN generic.http.fetch URL NSID vs lexicon JSON id
//   (C) collection-commands.ts `nsid("...")` command registrations vs lexicon filenames
//   (D) maps_source_dispatch_kind SQL CASE arms vs TS runCoverageJob dispatch arms
//       (prevents "added a new kind in UDF but forgot the TS branch" drift)
//   (E) migration filenames order + expected symbols
//
// Usage: node 70-tools/scripts/test/maps-coverage-e2e.mjs
// Exit codes: 0 = pass, 1 = any assertion failed.

import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

let failures = 0;
function ok(msg) { console.log(`  ✓ ${msg}`); }
function fail(msg) { console.log(`  ✗ ${msg}`); failures += 1; }
function header(msg) { console.log(`\n── ${msg} ──`); }

// ─── Expected pipeline ────────────────────────────────────────────────
// bpmnNsid = sync-bpmn-actors.py convention (com.etzhayyim.apps.{ns}.{camelCase(filename)})
// xrpcNsid = lexicon `id` (Worker-served procedure). One BPMN may call a
// different XRPC NSID from its own process id — e.g. runPendingCoverageJobs
// orchestrates the runCoverageJob XRPC in a multi-instance loop. The two
// NSIDs are deliberately distinct in that case.
const EXPECTED = [
  { kind: "advance",  bpmnNsid: "com.etzhayyim.apps.maps.advanceCoverage",        xrpcNsid: "com.etzhayyim.apps.maps.advanceCoverage",      bpmnFile: "advanceCoverage.bpmn",        lexFile: "advanceCoverage.json",       timer: "R/PT1M"  },
  { kind: "refresh",  bpmnNsid: "com.etzhayyim.apps.maps.refreshCoverageStats",   bpmnFile: "refreshCoverageStats.bpmn",                                                     xrpcNsid: "com.etzhayyim.apps.maps.refreshCoverageStats", lexFile: "refreshCoverageStats.json",  timer: "R/PT5M" },
  { kind: "run",      bpmnNsid: "com.etzhayyim.apps.maps.runPendingCoverageJobs", xrpcNsid: "com.etzhayyim.apps.maps.runCoverageJob",       bpmnFile: "runPendingCoverageJobs.bpmn", lexFile: "runCoverageJob.json",        timer: "R/PT3M"  },
];

const EXPECTED_MIGRATIONS = [
  { file: "20260424080000_udf_maps_coverage_gap.ts",                     symbols: ["vertex_maps_coverage_target", "maps_coverage_gap_score", "view_maps_coverage_gap_ranked"] },
  { file: "20260424090000_mv_maps_collected_per_source_label.ts",        symbols: ["mv_maps_collected_per_source_label"] },
  { file: "20260424100000_seed_maps_coverage_targets_phase2.ts",         symbols: ["vertex_maps_coverage_target", "street_view", "registry:jp-moj"] },
  { file: "20260424110000_udf_maps_source_dispatch_kind.ts",             symbols: ["maps_source_dispatch_kind"] },
];

// Must match the SQL CASE arms in the LATEST dispatch UDF migration AND
// the TS dispatch in collection-commands.ts cmdRunCoverageJob. Adding a
// kind anywhere requires adding it here and in both call sites.
const EXPECTED_DISPATCH_KINDS = [
  "gleif", "wikidata", "registry_other", "stac", "seismic",
  "mapillary", "overpass", "gtfs", "web_crawl", "unsupported",
  "wikipedia", "commons", "inaturalist", "gbif", "wikivoyage",
  "eonet", "opensky", "noaa_tides", "osm_notes",
];

// Of those, the kinds the TS handler must actually execute (the rest are
// routed to the error path intentionally).
const TS_IMPLEMENTED_KINDS = [
  "overpass", "gleif", "wikidata", "wikipedia", "commons",
  "inaturalist", "gbif", "wikivoyage", "eonet", "opensky",
  "noaa_tides", "osm_notes", "stac", "seismic", "mapillary",
];

// ─── A + B: BPMN ↔ lexicon ↔ NSID ─────────────────────────────────────
header("BPMN + lexicon NSID consistency");
for (const p of EXPECTED) {
  const bpmnPath = resolve(ROOT, "00-contracts/bpmn/com/etzhayyim/maps", p.bpmnFile);
  const lexPath = resolve(ROOT, "00-contracts/lexicons/com/etzhayyim/apps/maps", p.lexFile);

  if (!existsSync(bpmnPath)) { fail(`${p.bpmnFile}: not found`); continue; }
  if (!existsSync(lexPath))  { fail(`${p.lexFile}: not found`); continue; }

  const bpmn = readFileSync(bpmnPath, "utf8");
  const lex = JSON.parse(readFileSync(lexPath, "utf8"));

  // (A) BPMN process NSID (sync-bpmn-actors convention)
  const docNsid = bpmn.match(/"nsid"\s*:\s*"([^"]+)"/)?.[1];
  if (docNsid !== p.bpmnNsid) fail(`${p.bpmnFile}: documentation nsid="${docNsid}" ≠ expected "${p.bpmnNsid}"`);
  else ok(`${p.bpmnFile}: documentation nsid matches (${p.bpmnNsid})`);

  // (B) Lexicon id = XRPC NSID
  if (lex.id !== p.xrpcNsid) fail(`${p.lexFile}: id="${lex.id}" ≠ expected "${p.xrpcNsid}"`);
  else ok(`${p.lexFile}: id matches (${p.xrpcNsid})`);

  // Timer cadence
  if (!bpmn.includes(p.timer)) fail(`${p.bpmnFile}: expected timeCycle ${p.timer}`);
  else ok(`${p.bpmnFile}: timer ${p.timer}`);

  // BPMN must POST to the XRPC NSID it orchestrates.
  if (!bpmn.includes(p.xrpcNsid)) fail(`${p.bpmnFile}: expected to reference XRPC NSID ${p.xrpcNsid}`);
  else ok(`${p.bpmnFile}: references XRPC ${p.xrpcNsid}`);
}

// ─── C: Handler command registration ──────────────────────────────────
header("collection-commands.ts command registration");
const handlerPath = resolve(ROOT, "60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/collection-commands.ts");
const handler = readFileSync(handlerPath, "utf8");
const pyWorkerPath = resolve(ROOT, "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/maps_collection.py");
const pyWorker = readFileSync(pyWorkerPath, "utf8");
for (const p of EXPECTED) {
  const pattern = new RegExp(`nsid\\("${p.xrpcNsid.replace(/\./g, "\\.")}"\\)`);
  if (!pattern.test(handler)) fail(`${p.xrpcNsid}: not registered via nsid("...") in handler`);
  else ok(`${p.xrpcNsid}: registered`);
}

// Business logic has moved out of the CF Worker. Only the source-specific
// external fetch runner remains edge-local; coverage planning/stats are
// dispatched to Python/Zeebe through the thin proxy.
for (const command of ["advanceCoverage", "refreshCoverageStats", "batchCoverageCycle"]) {
  const pattern = new RegExp(`proxyCollectionCommand\\(ctx,\\s*"${command}"`);
  if (!pattern.test(handler)) fail(`${command}: not proxied to Python/Zeebe`);
  else ok(`${command}: proxied to Python/Zeebe`);
}
if (!new RegExp("async function cmdRunCoverageJob\\b").test(handler)) {
  fail("cmdRunCoverageJob: edge exception handler missing");
} else ok("cmdRunCoverageJob: edge exception handler present");

for (const fn of ["advance_coverage", "refresh_coverage_stats", "batch_coverage_cycle"]) {
  if (!new RegExp(`def ${fn}\\b`).test(pyWorker)) fail(`${fn}: Python worker implementation missing`);
  else ok(`${fn}: Python worker implementation present`);
}

// ─── D: UDF routing ↔ TS dispatch parity ──────────────────────────────
header("maps_source_dispatch_kind UDF ↔ TS dispatch parity");
// Read the LATEST dispatch UDF migration — later migrations DROP+CREATE
// the function with additional kinds. 20260424360000 adds osm_notes and
// is the current authoritative source.
const udfPath = resolve(ROOT, "30-graph/graph-schema/migrations/20260424360000_udf_osm_notes_plus_seed.ts");
const udfSrc = readFileSync(udfPath, "utf8");

const udfKinds = new Set();
for (const m of udfSrc.matchAll(/THEN\s+'([a-z_]+)'/g))  udfKinds.add(m[1]);
for (const m of udfSrc.matchAll(/ELSE\s+'([a-z_]+)'/g))  udfKinds.add(m[1]);

for (const k of EXPECTED_DISPATCH_KINDS) {
  if (!udfKinds.has(k)) fail(`UDF missing kind '${k}'`);
  else ok(`UDF emits '${k}'`);
}
for (const k of udfKinds) {
  if (!EXPECTED_DISPATCH_KINDS.includes(k)) fail(`UDF emits unexpected kind '${k}' — add to EXPECTED_DISPATCH_KINDS`);
}

// TS side must branch on every "implemented" kind.
for (const k of TS_IMPLEMENTED_KINDS) {
  if (!new RegExp(`dispatchKind\\s*===\\s*"${k}"`).test(handler)) {
    fail(`handler missing "if (dispatchKind === \\"${k}\\")" branch`);
  } else ok(`handler dispatches '${k}'`);
}

// ─── E: Migration ordering + symbols ──────────────────────────────────
header("migrations presence + key symbols");
for (const m of EXPECTED_MIGRATIONS) {
  const p = resolve(ROOT, "30-graph/graph-schema/migrations", m.file);
  if (!existsSync(p)) { fail(`${m.file}: not found`); continue; }
  const src = readFileSync(p, "utf8");
  for (const sym of m.symbols) {
    if (!src.includes(sym)) fail(`${m.file}: missing symbol '${sym}'`);
    else ok(`${m.file}: has '${sym}'`);
  }
}

// ─── F: BPMN runPending WHERE clause uses the UDF ─────────────────────
header("runPendingCoverageJobs uses UDF in WHERE");
const runPendingPath = resolve(ROOT, "orgs/etzhayyim/com-etzhayyim-maps/wire/bpmn/maps/runPendingCoverageJobs.bpmn");
const runPending = readFileSync(runPendingPath, "utf8");
if (!runPending.includes("maps_source_dispatch_kind(")) {
  fail("runPendingCoverageJobs.bpmn: WHERE clause does not call maps_source_dispatch_kind — drift risk");
} else ok("runPendingCoverageJobs.bpmn: UDF in WHERE clause");

if (!runPending.includes("'unsupported'")) {
  fail("runPendingCoverageJobs.bpmn: WHERE clause does not exclude 'unsupported' kind");
} else ok("runPendingCoverageJobs.bpmn: excludes 'unsupported'");

if (!runPending.includes("multiInstanceLoopCharacteristics")) {
  fail("runPendingCoverageJobs.bpmn: missing multi-instance fan-out");
} else ok("runPendingCoverageJobs.bpmn: multi-instance loop present");

// ─── G: advanceCoverage uses the gap-ranked view ──────────────────────
header("advanceCoverage uses view_maps_coverage_gap_ranked");
const advPath = resolve(ROOT, "orgs/etzhayyim/com-etzhayyim-maps/wire/bpmn/maps/advanceCoverage.bpmn");
const adv = readFileSync(advPath, "utf8");
if (!adv.includes("view_maps_coverage_gap_ranked")) {
  fail("advanceCoverage.bpmn: does not query view_maps_coverage_gap_ranked");
} else ok("advanceCoverage.bpmn: reads ranked view");
if (!pyWorker.includes("view_maps_coverage_gap_ranked")) {
  fail("advance_coverage Python worker: does not query view_maps_coverage_gap_ranked");
} else ok("advance_coverage Python worker: reads ranked view");

// ─── Summary ──────────────────────────────────────────────────────────
console.log("");
if (failures === 0) {
  console.log(`✅ maps coverage E2E contract test: PASS (${EXPECTED.length} XRPC × ${EXPECTED_MIGRATIONS.length} migrations × ${EXPECTED_DISPATCH_KINDS.length} dispatch kinds)`);
  process.exit(0);
} else {
  console.log(`❌ maps coverage E2E contract test: ${failures} failure(s)`);
  process.exit(1);
}
