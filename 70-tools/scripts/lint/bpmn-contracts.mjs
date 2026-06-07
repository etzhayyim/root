#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";

const jsonMode = process.argv.includes("--json");
const changedFromStdin = process.argv.includes("--changed-from-stdin");

const gates = [
  {
    key: "manifest",
    label: "BPMN coverage manifest",
    command: ["node", "70-tools/scripts/lint/bpmn-coverage-manifest-lint.mjs"],
    jsonCommand: ["node", "70-tools/scripts/lint/bpmn-coverage-manifest-lint.mjs", "--json"],
  },
  {
    key: "nsidExists",
    label: "NSID lexicon existence",
    command: ["node", "70-tools/scripts/lint/nsid-lexicon-exists.mjs"],
  },
  {
    key: "coverage",
    label: "BPMN registry coverage",
    command: ["node", "70-tools/scripts/lint/bpmn-coverage.mjs"],
    jsonCommand: ["node", "70-tools/scripts/lint/bpmn-coverage.mjs", "--json"],
  },
  {
    key: "structural",
    label: "BPMN structural validation",
    command: ["node", "70-tools/scripts/lint/bpmn-structural-validation.mjs"],
    jsonCommand: ["node", "70-tools/scripts/lint/bpmn-structural-validation.mjs", "--json"],
  },
  {
    key: "lexiconContract",
    label: "BPMN lexicon contract",
    command: ["node", "70-tools/scripts/lint/bpmn-lexicon-contract.mjs"],
    jsonCommand: ["node", "70-tools/scripts/lint/bpmn-lexicon-contract.mjs", "--json"],
  },
  {
    key: "workerTasks",
    label: "BPMN worker task coverage",
    command: ["node", "70-tools/scripts/lint/bpmn-worker-task-coverage.mjs"],
    jsonCommand: ["node", "70-tools/scripts/lint/bpmn-worker-task-coverage.mjs", "--json"],
  },
];

function normalizeFile(file) {
  return file.trim().replace(/^"\s*|\s*"$/gu, "").replace(/\\/gu, "/");
}

function changedFilesFromStdin() {
  const input = readFileSync(0, "utf8");
  return input
    .split(/\r?\n/u)
    .map(normalizeFile)
    .filter(Boolean);
}

function isBpmnFile(file) {
  return file.startsWith("00-contracts/bpmn/") && file.endsWith(".bpmn");
}

function isLexiconFile(file) {
  return file.startsWith("00-contracts/lexicons/") && file.endsWith(".json");
}

function isBpmnMigration(file) {
  return file.startsWith("30-graph/graph-schema/migrations/") && /bpmn/i.test(file) && file.endsWith(".ts");
}

function isWorkerFile(file) {
  return (
    file.startsWith("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/") ||
    file.startsWith("50-infra/vultr/") ||
    file.startsWith("60-apps/")
  ) && file.endsWith(".py");
}

function isBpmnLintScript(file) {
  return file.startsWith("70-tools/scripts/lint/bpmn-") && file.endsWith(".mjs");
}

function selectGates(files) {
  if (!changedFromStdin) return gates;
  const normalized = files.map(normalizeFile);
  const forceAll = normalized.some((file) => (
    file === "package.json" ||
    file === "pnpm-lock.yaml" ||
    file === "lefthook.yml" ||
    file === "70-tools/config/bpmn-coverage-manifest.json" ||
    file === "70-tools/scripts/lint/bpmn-contracts.mjs"
  ));
  if (forceAll) return gates;

  const selected = new Set();
  const hasBpmn = normalized.some(isBpmnFile);
  const hasLexicon = normalized.some(isLexiconFile);
  const hasMigration = normalized.some(isBpmnMigration);
  const hasWorker = normalized.some(isWorkerFile);
  const hasBpmnLint = normalized.some(isBpmnLintScript);

  if (hasLexicon || hasBpmnLint) selected.add("nsidExists");
  if (hasBpmn || hasLexicon || hasMigration || hasBpmnLint) selected.add("coverage");
  if (hasBpmn || hasLexicon || hasMigration || hasBpmnLint) selected.add("manifest");
  if (hasBpmn || hasBpmnLint) selected.add("structural");
  if (hasBpmn || hasLexicon || hasBpmnLint) selected.add("lexiconContract");
  if (hasBpmn || hasWorker || hasBpmnLint) selected.add("workerTasks");

  return gates.filter((gate) => selected.has(gate.key));
}

function run(command, options = {}) {
  const [bin, ...args] = command;
  return spawnSync(bin, args, {
    encoding: "utf8",
    stdio: options.stdio ?? "pipe",
    shell: false,
  });
}

function parseJson(stdout, key) {
  try {
    return JSON.parse(stdout);
  } catch (error) {
    return {
      parseError: `failed to parse ${key} JSON output: ${error?.message ?? String(error)}`,
      raw: stdout,
    };
  }
}

function runJson(selectedGates, changedFiles) {
  const results = {};
  const failures = [];

  for (const gate of selectedGates) {
    const command = gate.jsonCommand ?? gate.command;
    const result = run(command);
    const ok = result.status === 0;
    const entry = {
      ok,
      label: gate.label,
      command: command.join(" "),
      exitCode: result.status,
      stderr: result.stderr.trim(),
    };
    if (gate.jsonCommand && ok) {
      entry.report = parseJson(result.stdout, gate.key);
    } else {
      entry.stdout = result.stdout.trim();
    }
    results[gate.key] = entry;
    if (!ok) {
      failures.push({ key: gate.key, label: gate.label, exitCode: result.status });
    }
  }

  const report = {
    ok: failures.length === 0,
    changedFromStdin,
    changedFileCount: changedFiles.length,
    changedFiles,
    gateCount: selectedGates.length,
    failedGateCount: failures.length,
    failures,
    results,
  };
  console.log(JSON.stringify(report, null, 2));
  if (failures.length > 0) {
    process.exitCode = 1;
  }
}

function runText(selectedGates, changedFiles) {
  if (changedFromStdin && selectedGates.length === 0) {
    console.log(`bpmn-contracts: skipped (no BPMN-related files in ${changedFiles.length} changed file(s))`);
    return;
  }
  for (const gate of selectedGates) {
    const result = run(gate.command, { stdio: "inherit" });
    if (result.status !== 0) {
      process.exitCode = result.status ?? 1;
      return;
    }
  }
}

const changedFiles = changedFromStdin ? changedFilesFromStdin() : [];
const selectedGates = selectGates(changedFiles);

if (jsonMode) {
  runJson(selectedGates, changedFiles);
} else {
  runText(selectedGates, changedFiles);
}
