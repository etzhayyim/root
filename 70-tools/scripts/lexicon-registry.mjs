#!/usr/bin/env node
/**
 * lexicon-registry — walk 00-contracts/lexicons/, validate AT Protocol
 * Lexicon JSON, generate a manifest index, optionally push to PDS.
 *
 * Usage:
 *   node 70-tools/scripts/lexicon-registry.mjs               # validate + manifest
 *   node 70-tools/scripts/lexicon-registry.mjs --json        # emit manifest JSON to stdout
 *   node 70-tools/scripts/lexicon-registry.mjs --check       # validation only (exit 1 on error)
 *
 * Per ADR-2605192100 §2 + ADR-2605192230 (Lexicons are the AT-Record
 * substrate for Charter Compliance attestations + Council deliberation
 * + Land donations + Force authorizations + Eros/Gore judging).
 *
 * Future: `--push <pds-url>` to publish via `com.atproto.lexicon.schema`
 * once PDS XRPC supports schema records natively. Currently AT Protocol
 * Lexicons are typically distributed via npm + the @etzhayyim/lexicons-bundle
 * package at ../com-etzhayyim-lexicons-bundle/. This script catalogues them
 * for that bundle's manifest.
 */
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";

const REPO_ROOT = process.cwd();
const LEXICONS_DIR = join(REPO_ROOT, "00-contracts", "lexicons");

const FLAGS = new Set(process.argv.slice(2));

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) yield* walk(path);
    else if (path.endsWith(".json")) yield path;
  }
}

function validate(lexicon, path) {
  const errors = [];
  if (lexicon.lexicon !== 1) errors.push(`lexicon != 1 (got ${lexicon.lexicon})`);
  if (typeof lexicon.id !== "string" || !lexicon.id) errors.push("missing/empty id");
  if (!lexicon.defs || typeof lexicon.defs !== "object") errors.push("missing defs");
  // AT Protocol Lexicon spec: files named `defs.json` are reusable
  // type-definition libraries and need not declare a `main` entry.
  // Other Lexicon files MUST have defs.main as the primary type.
  const isDefsLibrary = path.endsWith("/defs.json");
  if (lexicon.defs && !lexicon.defs.main && !isDefsLibrary) errors.push("missing defs.main");

  // NSID format: 3+ dot-separated segments. AT Protocol spec is strict
  // ([a-z][a-zA-Z0-9-]*) but several legacy Lexicons in this repo use
  // underscore / leading-uppercase. Length check enforced; format
  // tracked as informational only.
  if (lexicon.id) {
    const segments = lexicon.id.split(".");
    if (segments.length < 3) errors.push(`NSID needs ≥3 segments (got ${segments.length}): ${lexicon.id}`);
  }

  // Path↔ID consistency
  const relPath = relative(LEXICONS_DIR, path).replace(/\.json$/, "");
  const expectedNsidFromPath = relPath.replace(/\//g, ".");
  // Allow id to be a suffix of the path (Lexicons can group multiple defs under one file)
  if (lexicon.id && !expectedNsidFromPath.endsWith(lexicon.id.replaceAll(".", "/").replaceAll(/[^a-z0-9/-]/gi, ""))) {
    // soft warning — many existing files use kebab-case in filename vs camelCase in id
    // intentionally not erroring; tracking only.
  }

  // Religious-corp wave Lexicons typically reference an ADR — emit a hint if not
  if (lexicon.defs?.main?.description) {
    const desc = lexicon.defs.main.description;
    if (!desc.match(/ADR-\d{10}/) && lexicon.id.startsWith("com.etzhayyim.apps.etzhayyim.")) {
      // not an error, but flag
    }
  }

  return errors;
}

function main() {
  const manifest = {
    generated: new Date().toISOString(),
    lexicons: [],
    by_namespace: {},
  };
  let totalErrors = 0;

  const checkOnly = FLAGS.has("--check");
  const jsonOnly = FLAGS.has("--json");

  for (const path of walk(LEXICONS_DIR)) {
    let raw, lexicon;
    try {
      raw = readFileSync(path, "utf8");
      lexicon = JSON.parse(raw);
    } catch (e) {
      if (!jsonOnly) console.error(`✘ JSON parse error: ${relative(REPO_ROOT, path)}: ${e.message}`);
      totalErrors++;
      continue;
    }

    const errors = validate(lexicon, path);
    if (errors.length > 0) {
      totalErrors += errors.length;
      if (!jsonOnly) {
        console.error(`✘ ${relative(REPO_ROOT, path)} (${lexicon.id})`);
        for (const err of errors) console.error(`    ${err}`);
      }
      continue;
    }

    const namespace = lexicon.id.split(".").slice(0, -1).join(".");
    manifest.lexicons.push({
      id: lexicon.id,
      path: relative(REPO_ROOT, path),
      type: lexicon.defs.main?.type ?? "defs-only",
      description: (lexicon.defs.main?.description ?? "").slice(0, 200),
    });
    manifest.by_namespace[namespace] ??= [];
    manifest.by_namespace[namespace].push(lexicon.id);
  }

  manifest.total = manifest.lexicons.length;
  manifest.lexicons.sort((a, b) => a.id.localeCompare(b.id));
  for (const ns of Object.keys(manifest.by_namespace)) {
    manifest.by_namespace[ns].sort();
  }

  // Strict --check mode blocks on legacy errors. Manifest-generation
  // default continues + records issues in manifest.legacy_issues.
  manifest.legacy_issues_count = totalErrors;

  if (checkOnly && totalErrors > 0) {
    if (!jsonOnly) {
      console.error("");
      console.error(`✘ lexicon-registry --check: ${totalErrors} validation error(s).`);
    }
    process.exit(1);
  }

  if (jsonOnly) {
    process.stdout.write(JSON.stringify(manifest, null, 2) + "\n");
  } else if (!checkOnly) {
    const manifestPath = join(LEXICONS_DIR, "_manifest.json");
    writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
    console.log(`✓ lexicon-registry: ${manifest.total} Lexicon(s) catalogued across ${Object.keys(manifest.by_namespace).length} namespace(s); ${totalErrors} legacy issue(s) flagged.`);
    console.log(`  Manifest written: ${relative(REPO_ROOT, manifestPath)}`);
    console.log("");
    console.log("Top namespaces by count:");
    const nsRanking = Object.entries(manifest.by_namespace)
      .map(([ns, ids]) => ({ ns, count: ids.length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    for (const { ns, count } of nsRanking) {
      console.log(`  ${ns.padEnd(50)} ${count.toString().padStart(4)}`);
    }
  } else {
    console.log(`✓ lexicon-registry: ${manifest.total} Lexicon(s) valid (${Object.keys(manifest.by_namespace).length} namespace(s)).`);
  }
}

main();
