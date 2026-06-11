#!/usr/bin/env node

import { existsSync } from "node:fs";
import path from "node:path";
import { loadBpmnCoverageManifest, BPMN_COVERAGE_MANIFEST_PATH } from "./bpmn-coverage-manifest.mjs";

const ROOT = process.cwd();
const jsonMode = process.argv.includes("--json");
const REQUIRED_BINDING_KEYS = ["area", "project", "proc", "sourcePath", "bpmnProcessId", "nsid", "lexiconPath"];

function existsRel(relPath) {
  return existsSync(path.join(ROOT, relPath));
}

function expectedSourcePath(binding) {
  return `00-contracts/bpmn/com/etzhayyim/${binding.project}/${binding.proc}.bpmn`;
}

function expectedLexiconPath(binding) {
  const nsidPrefix = "com.etzhayyim.apps.";
  if (!binding.nsid?.startsWith(nsidPrefix)) return null;
  const parts = binding.nsid.slice(nsidPrefix.length).split(".");
  if (parts.length < 2) return null;
  return `00-contracts/lexicons/com/etzhayyim/apps/${parts.join("/")}.json`;
}

function duplicateEntries(values) {
  const seen = new Map();
  const duplicates = [];
  values.forEach((value, index) => {
    if (!value) return;
    if (seen.has(value)) {
      duplicates.push({ value, firstIndex: seen.get(value), index });
    } else {
      seen.set(value, index);
    }
  });
  return duplicates;
}

function validateManifest() {
  const manifest = loadBpmnCoverageManifest(ROOT);
  const errors = [];
  const warnings = [];
  const bindings = manifest.bindings;
  const migrations = manifest.migrations;

  if (manifest.schemaVersion !== 1) {
    errors.push(`schemaVersion must be 1, got ${manifest.schemaVersion}`);
  }
  if (!Array.isArray(bindings) || bindings.length === 0) {
    errors.push("bindings must be a non-empty array");
  }
  if (!Array.isArray(migrations) || migrations.length === 0) {
    errors.push("migrations must be a non-empty array");
  }

  for (const [index, binding] of bindings.entries()) {
    for (const key of REQUIRED_BINDING_KEYS) {
      if (typeof binding[key] !== "string" || !binding[key].trim()) {
        errors.push(`bindings[${index}].${key} must be a non-empty string`);
      }
    }
    if (binding.sourcePath && !binding.sourcePath.endsWith(".bpmn")) {
      errors.push(`bindings[${index}].sourcePath must end with .bpmn: ${binding.sourcePath}`);
    }
    if (binding.lexiconPath && !binding.lexiconPath.endsWith(".json")) {
      errors.push(`bindings[${index}].lexiconPath must end with .json: ${binding.lexiconPath}`);
    }
    if (binding.sourcePath && !existsRel(binding.sourcePath)) {
      errors.push(`bindings[${index}].sourcePath does not exist: ${binding.sourcePath}`);
    }
    if (binding.lexiconPath && !existsRel(binding.lexiconPath)) {
      errors.push(`bindings[${index}].lexiconPath does not exist: ${binding.lexiconPath}`);
    }
    if (binding.bindingNsid !== undefined && (typeof binding.bindingNsid !== "string" || !binding.bindingNsid.trim())) {
      errors.push(`bindings[${index}].bindingNsid must be a non-empty string when present`);
    }
    const expectedSource = expectedSourcePath(binding);
    if (binding.sourcePath && expectedSource !== binding.sourcePath) {
      warnings.push(`bindings[${index}].sourcePath differs from project/proc convention: ${binding.sourcePath} != ${expectedSource}`);
    }
    const expectedLexicon = expectedLexiconPath(binding);
    if (binding.lexiconPath && expectedLexicon && expectedLexicon !== binding.lexiconPath) {
      warnings.push(`bindings[${index}].lexiconPath differs from nsid convention: ${binding.lexiconPath} != ${expectedLexicon}`);
    }
  }

  for (const duplicate of duplicateEntries(bindings.map((binding) => binding.sourcePath))) {
    errors.push(`duplicate sourcePath ${duplicate.value} at bindings[${duplicate.firstIndex}] and bindings[${duplicate.index}]`);
  }
  for (const duplicate of duplicateEntries(bindings.map((binding) => binding.bpmnProcessId))) {
    errors.push(`duplicate bpmnProcessId ${duplicate.value} at bindings[${duplicate.firstIndex}] and bindings[${duplicate.index}]`);
  }
  for (const duplicate of duplicateEntries(bindings.map((binding) => binding.nsid))) {
    errors.push(`duplicate nsid ${duplicate.value} at bindings[${duplicate.firstIndex}] and bindings[${duplicate.index}]`);
  }
  for (const duplicate of duplicateEntries(bindings.map((binding) => binding.lexiconPath))) {
    errors.push(`duplicate lexiconPath ${duplicate.value} at bindings[${duplicate.firstIndex}] and bindings[${duplicate.index}]`);
  }

  for (const [index, migration] of migrations.entries()) {
    if (typeof migration !== "string" || !migration.trim()) {
      errors.push(`migrations[${index}] must be a non-empty string`);
      continue;
    }
    if (!migration.endsWith(".ts")) {
      errors.push(`migrations[${index}] must end with .ts: ${migration}`);
    }
    if (!existsRel(migration)) {
      errors.push(`migrations[${index}] does not exist: ${migration}`);
    }
  }
  for (const duplicate of duplicateEntries(migrations)) {
    errors.push(`duplicate migration ${duplicate.value} at migrations[${duplicate.firstIndex}] and migrations[${duplicate.index}]`);
  }

  return {
    ok: errors.length === 0,
    manifestPath: BPMN_COVERAGE_MANIFEST_PATH,
    bindingCount: bindings.length,
    migrationCount: migrations.length,
    errors,
    warnings,
  };
}

function main() {
  const report = validateManifest();
  if (jsonMode) {
    console.log(JSON.stringify(report, null, 2));
  } else if (!report.ok) {
    console.error("bpmn-coverage-manifest: errors found");
    for (const error of report.errors) console.error(`- ${error}`);
    for (const warning of report.warnings) console.error(`warning: ${warning}`);
  } else {
    console.log(`bpmn-coverage-manifest: OK (${report.bindingCount} bindings, ${report.migrationCount} migrations)`);
    for (const warning of report.warnings) console.warn(`warning: ${warning}`);
  }
  if (!report.ok) {
    process.exitCode = 1;
  }
}

main();
