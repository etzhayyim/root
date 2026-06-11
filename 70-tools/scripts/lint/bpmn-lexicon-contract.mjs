#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { coveredBpmnBindings, BPMN_COVERAGE_MANIFEST_PATH } from "./bpmn-coverage-manifest.mjs";

const ROOT = process.cwd();
const jsonMode = process.argv.includes("--json");

function readRel(relPath) {
  return readFileSync(path.join(ROOT, relPath), "utf8");
}

function fileExists(relPath) {
  return existsSync(path.join(ROOT, relPath));
}

function snakeCase(name) {
  return name.replace(/[A-Z]/gu, (match) => `_${match.toLowerCase()}`).replace(/^_/u, "");
}

function camelCase(name) {
  return name.replace(/_([a-z0-9])/gu, (_, char) => char.toUpperCase());
}

function fieldVariants(field) {
  return [...new Set([field, camelCase(field), snakeCase(field)])];
}

function mainDefinition(lexicon) {
  return lexicon?.defs?.main ?? null;
}

function inputSchema(definition) {
  return definition?.input?.schema ?? definition?.parameters ?? null;
}

function outputSchema(definition) {
  return definition?.output?.schema ?? null;
}

function validateBinding(binding) {
  const errors = [];
  const checks = {
    bpmnFile: false,
    lexiconFile: false,
    lexiconId: false,
    mainDefinition: false,
    inputContract: false,
    outputContract: false,
    requiredInputsReferenced: false,
  };

  if (!fileExists(binding.sourcePath)) {
    errors.push(`missing BPMN file ${binding.sourcePath}`);
  } else {
    checks.bpmnFile = true;
  }
  if (!fileExists(binding.lexiconPath)) {
    errors.push(`missing lexicon file ${binding.lexiconPath}`);
  } else {
    checks.lexiconFile = true;
  }
  if (errors.length > 0) {
    return { ...binding, ok: false, checks, errors };
  }

  const xml = readRel(binding.sourcePath);
  let lexicon;
  try {
    lexicon = JSON.parse(readRel(binding.lexiconPath));
  } catch (error) {
    errors.push(`lexicon JSON parse failed: ${error?.message ?? String(error)}`);
    return { ...binding, ok: false, checks, errors };
  }

  if (lexicon.id !== binding.nsid) {
    errors.push(`lexicon id ${lexicon.id ?? "<missing>"} does not match ${binding.nsid}`);
  } else {
    checks.lexiconId = true;
  }

  const definition = mainDefinition(lexicon);
  if (!definition || !["procedure", "query"].includes(definition.type)) {
    errors.push("defs.main must exist and have type procedure or query");
  } else {
    checks.mainDefinition = true;
  }

  const inSchema = inputSchema(definition);
  if (!inSchema || inSchema.type !== "object" && inSchema.type !== "params") {
    errors.push("defs.main input schema or parameters must be an object/params contract");
  } else {
    checks.inputContract = true;
  }

  const outSchema = outputSchema(definition);
  if (!outSchema || outSchema.type !== "object") {
    errors.push("defs.main output.schema must be an object contract");
  } else {
    checks.outputContract = true;
  }

  const requiredInputs = Array.isArray(inSchema?.required) ? inSchema.required : [];
  const missingRequiredRefs = [];
  for (const field of requiredInputs) {
    const variants = fieldVariants(String(field));
    if (!variants.some((variant) => xml.includes(variant))) {
      missingRequiredRefs.push(String(field));
    }
  }
  if (missingRequiredRefs.length > 0) {
    errors.push(`required lexicon input(s) not referenced by BPMN: ${missingRequiredRefs.join(", ")}`);
  } else {
    checks.requiredInputsReferenced = true;
  }

  return {
    ...binding,
    ok: errors.length === 0,
    checks,
    errors,
    requiredInputs,
    inputPropertyCount: Object.keys(inSchema?.properties ?? {}).length,
    outputPropertyCount: Object.keys(outSchema?.properties ?? {}).length,
  };
}

function main() {
  const results = coveredBpmnBindings(ROOT).map(validateBinding);
  const failures = results.filter((result) => !result.ok);
  const report = {
    manifestPath: BPMN_COVERAGE_MANIFEST_PATH,
    checkedBindingCount: results.length,
    failedBindingCount: failures.length,
    failures,
    results,
  };

  if (jsonMode) {
    console.log(JSON.stringify(report, null, 2));
  } else if (failures.length > 0) {
    console.error("BPMN lexicon contract validation failed.");
    for (const failure of failures) {
      console.error(`- ${failure.sourcePath} -> ${failure.lexiconPath}`);
      for (const error of failure.errors) {
        console.error(`  - ${error}`);
      }
    }
  } else {
    console.log(`BPMN lexicon contract OK: ${results.length} covered BPMN/lexicon bindings validated.`);
  }

  if (failures.length > 0) {
    process.exitCode = 1;
  }
}

main();
