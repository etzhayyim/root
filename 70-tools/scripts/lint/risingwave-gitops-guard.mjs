#!/usr/bin/env node
import { readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const requiredFiles = [
  "50-infra/vultr/risingwave/gitops/flux/kustomization.yaml",
  "50-infra/vultr/risingwave/gitops/migrations/crd.yaml",
  "50-infra/vultr/risingwave/gitops/migrations/controller-rbac.yaml",
  "50-infra/vultr/risingwave/gitops/migrations/controller-configmap.yaml",
  "50-infra/vultr/risingwave/gitops/migrations/controller-deployment.yaml",
  "50-infra/vultr/risingwave/gitops/migrations/runner/Dockerfile",
  "50-infra/vultr/risingwave/gitops/flux-system/gitrepository.yaml",
  "50-infra/vultr/risingwave/gitops/flux-system/kustomization-migrations.yaml",
];

function read(file) {
  return readFileSync(path.join(repoRoot, file), "utf8");
}

const findings = [];

for (const file of requiredFiles) {
  try {
    read(file);
  } catch {
    findings.push(`${file}: missing`);
  }
}

if (findings.length === 0) {
  const flux = read("50-infra/vultr/risingwave/gitops/flux/kustomization.yaml");
  if (!flux.includes("../migrations")) {
    findings.push("flux/kustomization.yaml: must include ../migrations");
  }

  const crd = read("50-infra/vultr/risingwave/gitops/migrations/crd.yaml");
  for (const token of [
    "kind: RisingWaveMigration",
    "risingwavemigrations.etzhayyim.com",
    "subresources:",
    "status: {}",
    "migrationName:",
  ]) {
    if (!crd.includes(token)) {
      findings.push(`migrations/crd.yaml: missing ${token}`);
    }
  }

  const controller = read("50-infra/vultr/risingwave/gitops/migrations/controller-configmap.yaml");
  for (const token of [
    "rw-run-migration-single.sh",
    "RW_LEDGER_IMPLICIT_FLUSH",
    "RW_APPLY_SINGLE_IMPLICIT_FLUSH",
    "imagePullSecrets:",
    "risingwavemigrations.etzhayyim.com",
    "--subresource=status",
  ]) {
    if (!controller.includes(token)) {
      findings.push(`migrations/controller-configmap.yaml: missing ${token}`);
    }
  }

  const rbac = read("50-infra/vultr/risingwave/gitops/migrations/controller-rbac.yaml");
  for (const token of [
    "risingwavemigrations",
    "risingwavemigrations/status",
    "leases",
    "jobs",
  ]) {
    if (!rbac.includes(token)) {
      findings.push(`migrations/controller-rbac.yaml: missing ${token}`);
    }
  }

  const dockerfile = read("50-infra/vultr/risingwave/gitops/migrations/runner/Dockerfile");
  for (const token of [
    "postgresql-client",
    "kubectl",
    "30-graph/graph-schema",
    "70-tools/scripts/risingwave",
    "rw-run-migration-single.sh",
  ]) {
    if (!dockerfile.includes(token)) {
      findings.push(`migrations/runner/Dockerfile: missing ${token}`);
    }
  }

  const gitSource = read("50-infra/vultr/risingwave/gitops/flux-system/gitrepository.yaml");
  for (const token of [
    "kind: GitRepository",
    "ssh://git@github.com/etzhayyim/root.git",
    "branch: 240424-open",
    "etzhayyim/root-git",
    "!/50-infra/vultr/risingwave/gitops/migrations/**",
  ]) {
    if (!gitSource.includes(token)) {
      findings.push(`flux-system/gitrepository.yaml: missing ${token}`);
    }
  }

  const migrationKs = read("50-infra/vultr/risingwave/gitops/flux-system/kustomization-migrations.yaml");
  for (const token of [
    "kind: Kustomization",
    "suspend: true",
    "name: risingwave-migrations",
    "path: ./50-infra/vultr/risingwave/gitops/migrations",
    "risingwave-migration-controller",
  ]) {
    if (!migrationKs.includes(token)) {
      findings.push(`flux-system/kustomization-migrations.yaml: missing ${token}`);
    }
  }
}

if (findings.length > 0) {
  console.error("[risingwave-gitops-guard] invalid RisingWave GitOps migration control plane");
  for (const finding of findings) console.error(`  ${finding}`);
  process.exit(1);
}

console.log("[risingwave-gitops-guard] OK");
