#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { globSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const UPDATE_BASELINE = process.argv.includes("--update-baseline");
const BASELINE_PATH = path.join(
  ROOT,
  "90-docs",
  "rules",
  "actor-write-schema-guard-baseline.txt",
);

const ACTOR_COVERAGE_ALLOWED = new Set([
  "vertex_id",
  "rkey",
  "repo",
  "did",
  "collection",
  "status",
  "actorDid",
  "actorName",
  "nanoid",
  "bucket",
  "nodeCount",
  "latestTs",
  "topCollections",
  "freshnessRate",
  "totalNodes",
  "freshNodes",
  "snapshotTs",
  "_alive",
  "_seq",
]);

function loadBaseline() {
  try {
    const src = readFileSync(BASELINE_PATH, "utf8");
    return new Set(
      src
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean)
        .filter((s) => !s.startsWith("#")),
    );
  } catch {
    return new Set();
  }
}

function findLineNumber(text, needle) {
  const idx = text.indexOf(needle);
  if (idx < 0) return 1;
  return text.slice(0, idx).split("\n").length;
}

function extractMergeLabelAndAlias(template) {
  const m = template.match(/MERGE\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\{/);
  if (!m) return null;
  return { alias: m[1], label: m[2] };
}

function extractMergeMapKeys(template, alias, label) {
  const re = new RegExp(
    `MERGE\\s*\\(\\s*${alias}\\s*:\\s*${label}\\s*\\{([^}]*)\\}`,
    "m",
  );
  const m = template.match(re);
  if (!m) return [];
  const body = m[1];
  const keys = [];
  const keyRe = /([A-Za-z_][A-Za-z0-9_]*)\s*:/g;
  let km;
  while ((km = keyRe.exec(body)) !== null) keys.push(km[1]);
  return keys;
}

function extractSetKeys(template, alias) {
  const keys = [];
  const re = new RegExp(`${alias}\\.([A-Za-z_][A-Za-z0-9_]*)\\s*=`, "g");
  let m;
  while ((m = re.exec(template)) !== null) keys.push(m[1]);
  return keys;
}

function collectViolationsForManifest(absPath) {
  const rel = path.relative(ROOT, absPath).replaceAll(path.sep, "/");
  const src = readFileSync(absPath, "utf8");
  let manifest;
  try {
    manifest = JSON.parse(src);
  } catch {
    return [];
  }

  const pipelines = Array.isArray(manifest?.pipelines) ? manifest.pipelines : [];
  const violations = [];

  for (const pipeline of pipelines) {
    const steps = Array.isArray(pipeline?.steps) ? pipeline.steps : [];
    for (const step of steps) {
      if (step?.fn !== "graph.write") continue;
      const template = String(step?.args?.template || step?.args?.sql || "");
      if (!template) continue;

      const merge = extractMergeLabelAndAlias(template);
      if (!merge) continue;

      // Dedicated table contract: ActorCoverageSnapshot -> graphar.vertex_actor_coverage.
      if (merge.label !== "ActorCoverageSnapshot") continue;

      const keys = new Set([
        ...extractMergeMapKeys(template, merge.alias, merge.label),
        ...extractSetKeys(template, merge.alias),
      ]);

      for (const key of keys) {
        if (ACTOR_COVERAGE_ALLOWED.has(key)) continue;
        const line = findLineNumber(src, template);
        violations.push(
          `${rel}:${line} label=${merge.label} disallowed_column=${key} allowed=vertex_actor_coverage`,
        );
      }
    }
  }

  return violations;
}

function main() {
  const manifestPaths = globSync("orgs/etzhayyim/com-etzhayyim-*/actor-manifest.jsonld", { cwd: ROOT })
    .map((p) => path.join(ROOT, p))
    .sort();

  const allViolations = [];
  for (const absPath of manifestPaths) {
    allViolations.push(...collectViolationsForManifest(absPath));
  }
  allViolations.sort();

  if (UPDATE_BASELINE) {
    const header = [
      "# actor-write-schema-guard baseline",
      "# format:",
      "# <path>:<line> label=<Label> disallowed_column=<col> allowed=vertex_actor_coverage",
      "# update with: node 70-tools/scripts/lint/actor-write-schema-guard.mjs --update-baseline",
      "",
    ].join("\n");
    writeFileSync(BASELINE_PATH, header + allViolations.join("\n") + "\n");
    console.log(`Updated baseline: ${path.relative(ROOT, BASELINE_PATH)}`);
    console.log(`Entries: ${allViolations.length}`);
    process.exit(0);
  }

  const baseline = loadBaseline();
  const newViolations = allViolations.filter((v) => !baseline.has(v));

  if (newViolations.length > 0) {
    console.error("actor-write-schema-guard: new schema violations detected.");
    for (const v of newViolations) console.error(`  ${v}`);
    console.error("");
    console.error("Why this fails:");
    console.error("  ActorCoverageSnapshot writes are validated against graphar.vertex_actor_coverage.");
    console.error("  The template uses columns outside the dedicated table contract.");
    console.error("");
    console.error("If intentional, refresh baseline:");
    console.error("  node 70-tools/scripts/lint/actor-write-schema-guard.mjs --update-baseline");
    process.exit(1);
  }

  console.log(
    `actor-write-schema-guard: OK (checked=${manifestPaths.length}, violations=${allViolations.length}, new=0)`,
  );
}

main();
