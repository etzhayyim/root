#!/usr/bin/env node

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { coveredBpmnPaths, BPMN_COVERAGE_MANIFEST_PATH } from "./bpmn-coverage-manifest.mjs";

const ROOT = process.cwd();
const jsonMode = process.argv.includes("--json");

const WORKER_ROOTS = [
  "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama",
  "50-infra/k8s",
  "50-infra/vultr",
  "60-apps",
];

const BUILT_IN_TASK_TYPES = new Set([
  "io.camunda.zeebe:userTask",
]);

function rel(filePath) {
  return path.relative(ROOT, filePath).split(path.sep).join("/");
}

function lineOf(text, index) {
  return text.slice(0, index).split(/\r?\n/u).length;
}

function extractBpmnTaskTypes(sourcePath) {
  const absPath = path.join(ROOT, sourcePath);
  const xml = readFileSync(absPath, "utf8");
  const entries = [];
  const taskDefinitionPattern = /<zeebe:taskDefinition\b[^>]*\btype=(["'])(.*?)\1/gu;
  for (const match of xml.matchAll(taskDefinitionPattern)) {
    const type = match[2].trim();
    if (!type || BUILT_IN_TASK_TYPES.has(type)) continue;
    entries.push({
      type,
      sourcePath,
      line: lineOf(xml, match.index ?? 0),
    });
  }
  return entries;
}

function walkPythonFiles(rootRelPath) {
  const rootAbsPath = path.join(ROOT, rootRelPath);
  if (!existsSync(rootAbsPath)) return [];

  const files = [];
  const stack = [rootAbsPath];
  while (stack.length > 0) {
    const current = stack.pop();
    const stat = statSync(current);
    if (stat.isDirectory()) {
      for (const entry of readdirSync(current)) {
        if (entry === "__pycache__" || entry === ".venv" || entry === "node_modules") continue;
        stack.push(path.join(current, entry));
      }
      continue;
    }
    if (stat.isFile() && current.endsWith(".py")) {
      files.push(current);
    }
  }
  return files.sort();
}

function extractWorkerTaskTypes() {
  const registered = new Map();
  const taskTypePatterns = [
    /\bworker\.task\(\s*task_type\s*=\s*(["'])(.*?)\1/gu,
    /\btask_type\s*=\s*(["'])(.*?)\1/gu,
    /\bt\(\s*(["'])([a-z][a-z0-9_.-]*\.[a-z0-9_.-]+)\1/gu,
  ];

  for (const root of WORKER_ROOTS) {
    for (const file of walkPythonFiles(root)) {
      const text = readFileSync(file, "utf8");
      for (const pattern of taskTypePatterns) {
        for (const match of text.matchAll(pattern)) {
          const type = match[2].trim();
          if (!type) continue;
          const locations = registered.get(type) ?? [];
          locations.push({
            sourcePath: rel(file),
            line: lineOf(text, match.index ?? 0),
          });
          registered.set(type, locations);
        }
      }
    }
  }

  for (const builtIn of BUILT_IN_TASK_TYPES) {
    registered.set(builtIn, [{ sourcePath: "camunda-zeebe", line: 0 }]);
  }
  return registered;
}

function main() {
  const coveredPaths = coveredBpmnPaths(ROOT);
  const missingFiles = coveredPaths.filter((sourcePath) => !existsSync(path.join(ROOT, sourcePath)));
  const bpmnTaskEntries = coveredPaths
    .filter((sourcePath) => !missingFiles.includes(sourcePath))
    .flatMap(extractBpmnTaskTypes);
  const registeredTaskTypes = extractWorkerTaskTypes();

  const taskTypesByName = new Map();
  for (const entry of bpmnTaskEntries) {
    const entries = taskTypesByName.get(entry.type) ?? [];
    entries.push(entry);
    taskTypesByName.set(entry.type, entries);
  }

  const missingTaskTypes = [...taskTypesByName.entries()]
    .filter(([type]) => !registeredTaskTypes.has(type))
    .map(([type, references]) => ({ type, references }))
    .sort((a, b) => a.type.localeCompare(b.type));

  const report = {
    manifestPath: BPMN_COVERAGE_MANIFEST_PATH,
    coveredBpmnCount: coveredPaths.length,
    coveredBpmnWithTaskDefinitions: new Set(bpmnTaskEntries.map((entry) => entry.sourcePath)).size,
    bpmnTaskReferenceCount: bpmnTaskEntries.length,
    bpmnTaskTypeCount: taskTypesByName.size,
    registeredWorkerTaskTypeCount: registeredTaskTypes.size,
    missingFiles,
    missingTaskTypes,
    coveredTaskTypes: [...taskTypesByName.keys()].sort(),
  };

  if (jsonMode) {
    console.log(JSON.stringify(report, null, 2));
  } else if (missingFiles.length > 0 || missingTaskTypes.length > 0) {
    console.error("BPMN worker task coverage failed.");
    for (const sourcePath of missingFiles) {
      console.error(`- Missing covered BPMN file: ${sourcePath}`);
    }
    for (const missing of missingTaskTypes) {
      const refs = missing.references
        .slice(0, 5)
        .map((ref) => `${ref.sourcePath}:${ref.line}`)
        .join(", ");
      const suffix = missing.references.length > 5 ? ` (+${missing.references.length - 5} more)` : "";
      console.error(`- Unregistered Zeebe task type "${missing.type}" used at ${refs}${suffix}`);
    }
  } else {
    console.log(
      `BPMN worker task coverage OK: ${report.bpmnTaskTypeCount} task types across ${report.coveredBpmnWithTaskDefinitions}/${report.coveredBpmnCount} covered BPMN files are registered in worker code.`,
    );
  }

  if (missingFiles.length > 0 || missingTaskTypes.length > 0) {
    process.exitCode = 1;
  }
}

main();
