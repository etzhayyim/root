#!/usr/bin/env node

import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { loadBpmnCoverageManifest, BPMN_COVERAGE_MANIFEST_PATH } from "./bpmn-coverage-manifest.mjs";

const ROOT = process.cwd();
const jsonMode = process.argv.includes("--json");

const { bindings: EXPECTED, migrations: MIGRATIONS } = loadBpmnCoverageManifest(ROOT);



function readRel(relPath) {
  return readFileSync(path.join(ROOT, relPath), "utf8");
}

function fileExists(relPath) {
  return existsSync(path.join(ROOT, relPath));
}

function loadMigrations() {
  return MIGRATIONS
    .filter(fileExists)
    .map((relPath) => ({ relPath, text: readRel(relPath) }));
}

function loadLexiconId(relPath) {
  const json = JSON.parse(readRel(relPath));
  return json?.id;
}

function summarize(rows) {
  const byArea = new Map();
  for (const row of rows) {
    byArea.set(row.area, (byArea.get(row.area) ?? 0) + 1);
  }
  return Object.fromEntries([...byArea.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

function printJson(rows, errors) {
  const report = {
    ok: errors.length === 0,
    manifestPath: BPMN_COVERAGE_MANIFEST_PATH,
    count: rows.length,
    summary: summarize(rows),
    rows,
    errors,
  };
  console.log(JSON.stringify(report, null, 2));
}

function lexiconNamespaceOf(expected) {
  const prefix = "com.etzhayyim.apps.";
  const suffix = `.${expected.proc}`;
  if (!expected.nsid.startsWith(prefix) || !expected.nsid.endsWith(suffix)) return null;
  return expected.nsid.slice(prefix.length, -suffix.length);
}

function main() {
  const migrations = loadMigrations();
  const errors = [];
  const rows = [];

  for (const expected of EXPECTED) {
    const row = {
      area: expected.area,
      project: expected.project,
      proc: expected.proc,
      sourcePath: expected.sourcePath,
      bpmnProcessId: expected.bpmnProcessId,
      nsid: expected.nsid,
      lexiconPath: expected.lexiconPath,
      checks: {
        bpmnFile: false,
        bpmnProcessId: false,
        lexiconFile: false,
        lexiconId: false,
        graphSeedBinding: false,
      },
    };
    rows.push(row);

    if (!fileExists(expected.sourcePath)) {
      errors.push(`${expected.area}: missing BPMN ${expected.sourcePath}`);
      continue;
    }
    row.checks.bpmnFile = true;

    const bpmnXml = readRel(expected.sourcePath);
    if (!bpmnXml.includes(`id="${expected.bpmnProcessId}"`)) {
      errors.push(`${expected.area}: ${expected.sourcePath} does not define process ${expected.bpmnProcessId}`);
    } else {
      row.checks.bpmnProcessId = true;
    }

    if (!fileExists(expected.lexiconPath)) {
      errors.push(`${expected.area}: missing lexicon ${expected.lexiconPath}`);
    } else {
      row.checks.lexiconFile = true;
      const lexiconId = loadLexiconId(expected.lexiconPath);
      if (lexiconId !== expected.nsid) {
        errors.push(`${expected.area}: ${expected.lexiconPath} id is ${lexiconId}, expected ${expected.nsid}`);
      } else {
        row.checks.lexiconId = true;
      }
    }

    const seedNsid = expected.bindingNsid ?? expected.nsid;
    const seedExpected = { ...expected, nsid: seedNsid };
    const registered = migrations.some(({ text }) => {
      const hasExplicitSource = text.includes(expected.sourcePath);
      const hasGeneratedSourceParts =
        (text.includes(`project: "${expected.project}"`) || text.includes(`const project = "${expected.project}"`)) &&
        text.includes(`proc: "${expected.proc}"`);
      const nsidNamespace = lexiconNamespaceOf(seedExpected);
      const hasExplicitNsid = text.includes(seedNsid);
      const hasGeneratedNsidParts =
        nsidNamespace !== null &&
        text.includes(`nsidNs: "${nsidNamespace}"`) &&
        text.includes(`proc: "${expected.proc}"`);
      return (hasExplicitSource || hasGeneratedSourceParts) &&
        text.includes(expected.bpmnProcessId) &&
        (hasExplicitNsid || hasGeneratedNsidParts);
    });
    if (!registered) {
      errors.push(
        `${expected.area}: ${expected.bpmnProcessId} is not covered by processDef + lexicon binding seed for ${seedNsid}`,
      );
    } else {
      row.checks.graphSeedBinding = true;
    }
  }

  if (errors.length > 0) {
    if (jsonMode) printJson(rows, errors);
    else {
      console.error("bpmn-coverage: coverage gaps found");
      for (const error of errors) console.error(`- ${error}`);
    }
    process.exit(1);
  }

  if (jsonMode) {
    printJson(rows, errors);
    return;
  }

  const summary = Object.entries(summarize(rows)).map(([area, count]) => `${area}=${count}`).join(", ");
  console.log(`bpmn-coverage: OK (${EXPECTED.length} BPMN bindings checked; ${summary})`);
}

main();
