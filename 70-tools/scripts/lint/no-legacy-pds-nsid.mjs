#!/usr/bin/env node
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const LEGACY_NSIDS = [
  "com.etzhayyim.apps.pds.listHeartbeatApps",
  "com.etzhayyim.apps.pds.registerSyncApp",
  "com.etzhayyim.kagami.query",
  "com.etzhayyim.kagami.command",
  "com.etzhayyim.kagami.queryExec",
  "com.etzhayyim.kagami.graphExec",
];

const EXCLUDE_GLOBS = [
  "--glob=!**/node_modules/**",
  "--glob=!**/.git/**",
  "--glob=!**/dist/**",
  "--glob=!**/.svelte-kit/**",
  "--glob=!**/build/**",
  "--glob=!**/static/**",
  "--glob=!**/coverage/**",
  "--glob=!scripts/lint/no-legacy-pds-nsid.mjs",
  "--glob=!**/pds-dispatch.ts",
  "--glob=!**/*.test.ts",
  "--glob=!**/test/**",
];

const INCLUDE_GLOBS = [
  "--glob=*.{ts,tsx,js,mjs,cjs,svelte}",
];

const ROOT = process.cwd();
const BASELINE_PATH = path.join(ROOT, "90-docs/rules/legacy-pds-nsid-baseline.txt");

function loadBaseline() {
  try {
    return new Set(readFileSync(BASELINE_PATH, "utf8").split("\n").filter(Boolean));
  } catch {
    return new Set();
  }
}

const SEARCH_ROOTS = ["60-apps", "50-infra", "20-actors", "30-graph", "40-engine"];
const violations = new Set();
for (const nsid of new Set(LEGACY_NSIDS)) {
  const cmd = [
    "rg",
    "-n",
    "--fixed-strings",
    JSON.stringify(nsid),
    ...INCLUDE_GLOBS,
    ...EXCLUDE_GLOBS,
    ...SEARCH_ROOTS,
  ].join(" ");
  let out = "";
  try {
    out = execSync(cmd, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch (err) {
    if (err.status === 1) continue; // no match
    throw err;
  }
  const lines = out.trim().split("\n").filter(Boolean);
  for (const line of lines) violations.add(line);
}

if (process.argv.includes("--update-baseline")) {
  writeFileSync(BASELINE_PATH, [...violations].sort().join("\n") + "\n");
  console.log(`updated baseline: ${BASELINE_PATH} (${violations.size} entries)`);
  process.exit(0);
}

const baseline = loadBaseline();
const newViolations = [...violations].filter((v) => !baseline.has(v));

if (newViolations.length > 0) {
  console.error(`lint:legacy-pds-nsid failed: ${newViolations.length} new legacy PDS NSID violations`);
  for (const line of newViolations) console.error(`  ${line}`);
  console.error("\nIf these are existing code, run: node 70-tools/scripts/lint/no-legacy-pds-nsid.mjs --update-baseline");
  process.exit(1);
}

console.log(`lint:legacy-pds-nsid ok (current=${violations.size}, baseline=${baseline.size})`);
