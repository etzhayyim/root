#!/usr/bin/env node
/**
 * Guard the Vultr RisingWave control plane.
 *
 * This repo has historical docs and older service runbooks that mention direct
 * helm/migration commands. This guard intentionally scopes enforcement to the
 * Vultr RisingWave control-plane area and its dedicated scripts, where direct
 * topology or DDL mutations must pass through:
 *
 *   - 70-tools/scripts/risingwave/rw-op-lock.sh
 *   - 70-tools/scripts/risingwave/rw-run-migration-single.sh
 *   - 70-tools/scripts/risingwave/rw-helm-upgrade-single.sh
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();

const allowlist = new Set([
  "50-infra/vultr/risingwave/gitops/README.md",
  "50-infra/vultr/risingwave/gitops/migrations/controller-configmap.yaml",
  "50-infra/vultr/risingwave/deps.toml",
  "70-tools/scripts/lint/risingwave-control-plane-guard.mjs",
  "70-tools/scripts/risingwave/rw-helm-upgrade-single.sh",
  "70-tools/scripts/risingwave/rw-op-lock.sh",
  "70-tools/scripts/risingwave/rw-run-migration-single.sh",
]);

const scannedPrefixes = [
  "50-infra/vultr/risingwave/",
  "70-tools/scripts/risingwave/",
];

const ignoredSuffixes = [
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".pdf",
  ".lock",
];

const rules = [
  {
    id: "rw-direct-helm-upgrade",
    reason: "RisingWave Helm changes must use rw-helm-upgrade-single.sh or Flux.",
    pattern: /\bhelm\s+upgrade\b[^\n]*(?:\brisingwave\b|risingwavelabs\/risingwave|50-infra\/vultr\/risingwave|helm\/values\.yaml)/,
  },
  {
    id: "rw-unapproved-chart-bump",
    reason: "RisingWave chart bumps must be explicit and go through rw-helm-upgrade-single.sh with RW_ALLOW_RISINGWAVE_CHART_BUMP=1.",
    pattern: /\b(?:risingwave-0\.2\.50|--version\s+0\.2\.50|RW_HELM_VERSION=0\.2\.50)\b/,
  },
  {
    id: "rw-direct-kubectl-scale",
    reason: "RisingWave topology changes must use the operation lock or GitOps path.",
    pattern: /\bkubectl\b[^\n]*(?:\bscale\b|\bpatch\b)[^\n]*(?:risingwave|compute|compactor|frontend|meta)/,
  },
  {
    id: "rw-direct-compute-rollout",
    reason: "RisingWave compute rollouts reset the Foyer warm gate and must go through rw-helm-upgrade-single.sh.",
    pattern: /\bkubectl\b[^\n]*\brollout\s+restart\b[^\n]*(?:statefulset\/)?risingwave-compute\b/,
  },
  {
    id: "rw-direct-apply-single",
    reason: "Single Kysely migrations must use rw-run-migration-single.sh.",
    pattern: /\bnode\s+scripts\/apply-single\.mjs\b/,
  },
  {
    id: "rw-direct-db-migrate",
    reason: "RisingWave migrations must use rw-run-migration-single.sh.",
    pattern: /\bpnpm\b[^\n]*(?:db:migrate|db:migrate:up|db:migrate:down)\b/,
  },
];

function gitFiles() {
  const out = execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard", "--", ...scannedPrefixes],
    { cwd: repoRoot, encoding: "utf8" },
  );
  return out.split("\n").filter(Boolean);
}

function shouldScan(file) {
  if (allowlist.has(file)) return false;
  if (!scannedPrefixes.some((prefix) => file.startsWith(prefix))) return false;
  return !ignoredSuffixes.some((suffix) => file.endsWith(suffix));
}

function lineNumberForOffset(text, offset) {
  return text.slice(0, offset).split("\n").length;
}

const findings = [];

for (const file of gitFiles().filter(shouldScan)) {
  const abs = path.join(repoRoot, file);
  let text;
  try {
    text = readFileSync(abs, "utf8");
  } catch {
    continue;
  }

  for (const rule of rules) {
    const match = rule.pattern.exec(text);
    if (match) {
      findings.push({
        file,
        line: lineNumberForOffset(text, match.index),
        rule: rule.id,
        reason: rule.reason,
        snippet: match[0].trim(),
      });
    }
  }
}

if (findings.length > 0) {
  console.error("[risingwave-control-plane-guard] direct RisingWave operation found");
  for (const finding of findings) {
    console.error(`\n${finding.file}:${finding.line} ${finding.rule}`);
    console.error(`  ${finding.reason}`);
    console.error(`  ${finding.snippet}`);
  }
  process.exit(1);
}

console.log("[risingwave-control-plane-guard] OK");
