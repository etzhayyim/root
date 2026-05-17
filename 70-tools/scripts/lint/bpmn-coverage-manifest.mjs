import { readFileSync } from "node:fs";
import path from "node:path";

export const BPMN_COVERAGE_MANIFEST_PATH = "70-tools/config/bpmn-coverage-manifest.json";

export function loadBpmnCoverageManifest(root = process.cwd()) {
  const manifestPath = path.join(root, BPMN_COVERAGE_MANIFEST_PATH);
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const bindings = Array.isArray(manifest.bindings) ? manifest.bindings : [];
  const migrations = Array.isArray(manifest.migrations) ? manifest.migrations : [];
  return { ...manifest, bindings, migrations };
}

export function coveredBpmnBindings(root = process.cwd()) {
  return loadBpmnCoverageManifest(root).bindings;
}

export function coveredBpmnPaths(root = process.cwd()) {
  const paths = [];
  const seen = new Set();
  for (const binding of coveredBpmnBindings(root)) {
    if (!binding.sourcePath || seen.has(binding.sourcePath)) continue;
    seen.add(binding.sourcePath);
    paths.push(binding.sourcePath);
  }
  return paths;
}
