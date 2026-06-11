#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { BpmnModdle } from "bpmn-moddle";
import { coveredBpmnBindings, BPMN_COVERAGE_MANIFEST_PATH } from "./bpmn-coverage-manifest.mjs";

const ROOT = process.cwd();
const jsonMode = process.argv.includes("--json");

function lineOf(text, index) {
  return text.slice(0, index).split(/\r?\n/u).length;
}

function findTaskDefinitionTypes(xml, taskId) {
  const taskPattern = new RegExp(
    `<bpmn:serviceTask\\b[^>]*\\bid=(["'])${taskId}\\1[\\s\\S]*?</bpmn:serviceTask>`,
    "u",
  );
  const taskMatch = xml.match(taskPattern);
  if (!taskMatch) return [];
  const taskXml = taskMatch[0];
  return [...taskXml.matchAll(/<zeebe:taskDefinition\b[^>]*\btype=(["'])(.*?)\1/gu)]
    .map((match) => match[2].trim())
    .filter(Boolean);
}

async function validateBinding(moddle, binding) {
  const errors = [];
  const warnings = [];
  const absPath = path.join(ROOT, binding.sourcePath);
  if (!existsSync(absPath)) {
    return {
      ...binding,
      ok: false,
      errors: [`missing BPMN file: ${binding.sourcePath}`],
      warnings,
      metrics: {},
    };
  }

  const xml = readFileSync(absPath, "utf8");
  let rootElement;
  try {
    const parsed = await moddle.fromXML(xml);
    rootElement = parsed.rootElement;
    for (const warning of parsed.warnings ?? []) {
      warnings.push(warning.message ?? String(warning));
    }
  } catch (error) {
    return {
      ...binding,
      ok: false,
      errors: [`BPMN XML parse failed: ${error?.message ?? String(error)}`],
      warnings,
      metrics: {},
    };
  }

  if (rootElement?.$type !== "bpmn:Definitions") {
    errors.push(`root element is ${rootElement?.$type ?? "unknown"}, expected bpmn:Definitions`);
  }
  for (const warning of warnings) {
    errors.push(`BPMN parser warning: ${warning}`);
  }

  const process = (rootElement.rootElements ?? []).find(
    (element) => element.$type === "bpmn:Process" && element.id === binding.bpmnProcessId,
  );
  if (!process) {
    errors.push(`missing bpmn:Process id=${binding.bpmnProcessId}`);
  } else if (process.isExecutable !== true) {
    errors.push(`process ${binding.bpmnProcessId} must set isExecutable="true"`);
  }

  const flowElements = process?.flowElements ?? [];
  const startEvents = flowElements.filter((element) => element.$type === "bpmn:StartEvent");
  const endEvents = flowElements.filter((element) => element.$type === "bpmn:EndEvent");
  const serviceTasks = flowElements.filter((element) => element.$type === "bpmn:ServiceTask");
  const sequenceFlows = flowElements.filter((element) => element.$type === "bpmn:SequenceFlow");

  if (process) {
    if (startEvents.length < 1) errors.push(`process ${binding.bpmnProcessId} has no start event`);
    if (endEvents.length < 1) errors.push(`process ${binding.bpmnProcessId} has no end event`);
  }

  for (const task of serviceTasks) {
    const taskDefinitionTypes = findTaskDefinitionTypes(xml, task.id);
    if (taskDefinitionTypes.length !== 1) {
      const taskIndex = xml.indexOf(`id="${task.id}"`);
      const location = taskIndex >= 0 ? `:${lineOf(xml, taskIndex)}` : "";
      errors.push(
        `${binding.sourcePath}${location}: serviceTask ${task.id} must define exactly one zeebe:taskDefinition type`,
      );
    }
  }

  for (const flow of sequenceFlows) {
    if (!flow.sourceRef) {
      errors.push(`sequenceFlow ${flow.id} is missing sourceRef`);
    }
    if (!flow.targetRef) {
      errors.push(`sequenceFlow ${flow.id} is missing targetRef`);
    }
  }

  return {
    ...binding,
    ok: errors.length === 0,
    errors,
    warnings,
    metrics: {
      flowElementCount: flowElements.length,
      serviceTaskCount: serviceTasks.length,
      sequenceFlowCount: sequenceFlows.length,
      startEventCount: startEvents.length,
      endEventCount: endEvents.length,
    },
  };
}

async function main() {
  const moddle = new BpmnModdle();
  const bindings = coveredBpmnBindings(ROOT);
  const results = [];
  for (const binding of bindings) {
    results.push(await validateBinding(moddle, binding));
  }
  const failures = results.filter((result) => !result.ok);
  const report = {
    manifestPath: BPMN_COVERAGE_MANIFEST_PATH,
    checkedBpmnCount: results.length,
    failedBpmnCount: failures.length,
    failures,
    results,
  };

  if (jsonMode) {
    console.log(JSON.stringify(report, null, 2));
  } else if (failures.length > 0) {
    console.error("BPMN structural validation failed.");
    for (const failure of failures) {
      console.error(`- ${failure.sourcePath} (${failure.bpmnProcessId})`);
      for (const error of failure.errors) {
        console.error(`  - ${error}`);
      }
    }
  } else {
    console.log(`BPMN structural validation OK: ${results.length} covered BPMN files parsed and validated.`);
  }

  if (failures.length > 0) {
    process.exitCode = 1;
  }
}

main();
