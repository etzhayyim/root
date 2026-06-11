#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const IGNORE_DIRS = new Set([
  ".git",
  "node_modules",
  ".pnpm-store",
  ".nx",
  ".turbo",
  ".wrangler",
  "_archive",
  ".venv",
  "target",
  ".claude"
]);

function toPosix(value) {
  return value.split(path.sep).join("/");
}

async function walkForDeps(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walkForDeps(full, out);
      continue;
    }
    if (entry.isFile() && entry.name === "deps.toml") {
      out.push(full);
    }
  }
  return out;
}

function parseToml(file) {
  const py = [
    "import json, sys, tomllib",
    "with open(sys.argv[1], 'rb') as f:",
    "    data = tomllib.load(f)",
    "print(json.dumps(data))",
  ].join("\n");
  const raw = execFileSync("python3", ["-c", py, file], { encoding: "utf8", maxBuffer: 100 * 1024 * 1024 });
  return JSON.parse(raw);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function hasFlag(entry, flag) {
  return Array.isArray(entry?.flags) && entry.flags.includes(flag);
}

function classifyPathKey(key) {
  const normalized = key.replace(/\\/g, "/");
  const parts = normalized.split("/");
  const last = parts.at(-1);

  if (last === "package.json") return "package-json";
  if (last === "pnpm-workspace.yaml") return "pnpm-workspace";
  if (last === "go.mod") return "go-mod";
  if (parts.includes("dist")) return "dist";
  if (parts.includes("generated")) return "generated";
  if (parts.includes("e2e")) return "e2e";
  if (parts.includes("tests") || parts.includes("test")) return "tests";
  if (parts.includes("perf") || parts.includes("benchmark") || parts.includes("bench")) return "benchmark";
  if (parts.includes("poc")) return "poc";
  return null;
}

function isAllowed(value, allowed) {
  return value == null || allowed.has(value);
}

function validateEntry({
  depsFile,
  sectionName,
  entryKey,
  entry,
  allowedKinds,
  allowedToolchains,
  allowedMaturities,
  allowedWorkspaces,
  allowedProfiles,
  errors,
}) {
  const label = `${toPosix(path.relative(root, depsFile))} [${sectionName}."${entryKey}"]`;
  const kind = entry.kind;
  const toolchain = entry.toolchain;
  const maturity = entry.maturity;
  const workspace = entry.workspace;
  const profiles = asArray(entry.execution_profiles);

  if (!isAllowed(kind, allowedKinds)) {
    errors.push(`${label}: unknown kind=${JSON.stringify(kind)}`);
  }
  if (!isAllowed(toolchain, allowedToolchains)) {
    errors.push(`${label}: unknown toolchain=${JSON.stringify(toolchain)}`);
  }
  if (!isAllowed(maturity, allowedMaturities)) {
    errors.push(`${label}: unknown maturity=${JSON.stringify(maturity)}`);
  }
  if (!isAllowed(workspace, allowedWorkspaces)) {
    errors.push(`${label}: unknown workspace=${JSON.stringify(workspace)}`);
  }
  for (const profile of profiles) {
    if (!allowedProfiles.has(profile)) {
      errors.push(`${label}: unknown execution_profiles entry=${JSON.stringify(profile)}`);
    }
  }

  const requiresToolchain = new Set([
    "workspace-root",
    "workspace-root-manifest",
    "workspace-membership-map",
    "package",
    "service",
    "library",
    "app",
    "tool",
    "script",
    "benchmark",
    "generated",
    "lockfile",
  ]);

  const requiresWorkspace = new Set([
    "workspace-root",
    "workspace-root-manifest",
    "workspace-membership-map",
    "package",
    "service",
    "library",
    "app",
    "tool",
    "lockfile",
  ]);

  if (kind && requiresToolchain.has(kind) && !toolchain) {
    errors.push(`${label}: kind=${kind} requires toolchain`);
  }
  if (kind && requiresWorkspace.has(kind) && !workspace) {
    errors.push(`${label}: kind=${kind} requires workspace`);
  }
  if (kind === "generated" && !hasFlag(entry, "generated")) {
    errors.push(`${label}: kind=generated must include flags=[\"generated\"]`);
  }
  if (kind === "lockfile" && !hasFlag(entry, "generated")) {
    errors.push(`${label}: kind=lockfile must include flags=[\"generated\"]`);
  }

  const pathClass = classifyPathKey(entryKey);
  if (pathClass === "package-json") {
    if (!["package", "workspace-root-manifest"].includes(kind)) {
      errors.push(`${label}: package.json must use kind=package or workspace-root-manifest`);
    }
    if (toolchain !== "pnpm") {
      errors.push(`${label}: package.json must use toolchain=pnpm`);
    }
  }
  if (pathClass === "pnpm-workspace") {
    if (kind !== "workspace-membership-map") {
      errors.push(`${label}: pnpm-workspace.yaml must use kind=workspace-membership-map`);
    }
    if (toolchain !== "pnpm") {
      errors.push(`${label}: pnpm-workspace.yaml must use toolchain=pnpm`);
    }
  }
  if (pathClass === "go-mod") {
    if (kind !== "package") {
      errors.push(`${label}: go.mod must use kind=package`);
    }
    if (toolchain !== "go") {
      errors.push(`${label}: go.mod must use toolchain=go`);
    }
  }
  if (pathClass === "dist" && !["generated", "report"].includes(kind)) {
    errors.push(`${label}: dist paths should use kind=generated or kind=report`);
  }
  if (pathClass === "generated" && !["generated", "poc"].includes(kind)) {
    errors.push(`${label}: generated paths should use kind=generated or kind=poc`);
  }
  if (pathClass === "e2e" && kind !== "e2e") {
    errors.push(`${label}: e2e paths should use kind=e2e`);
  }
  if (pathClass === "tests" && !["test", "e2e"].includes(kind)) {
    errors.push(`${label}: test paths should use kind=test or kind=e2e`);
  }
  if (pathClass === "benchmark" && !["benchmark", "report"].includes(kind)) {
    errors.push(`${label}: benchmark paths should use kind=benchmark or kind=report`);
  }
  if (pathClass === "poc" && !["poc", "generated"].includes(kind)) {
    errors.push(`${label}: poc paths should use kind=poc or kind=generated`);
  }
}

const depsFiles = (await walkForDeps(root)).sort();
const parsed = depsFiles.map((file) => ({ file, data: parseToml(file) }));
const rootDeps = parsed.find((item) => path.resolve(item.file) === path.resolve(root, "deps.toml"));

if (!rootDeps) {
  console.error("lint:deps:metadata failed: root deps.toml not found");
  process.exit(1);
}

const metadataAxes = rootDeps.data.metadata_axes ?? {};
const allowedKinds = new Set(asArray(metadataAxes.kind?.allowed));
const allowedToolchains = new Set(asArray(metadataAxes.toolchain?.allowed));
const allowedMaturities = new Set(asArray(metadataAxes.maturity?.allowed));
const allowedWorkspaces = new Set(asArray(metadataAxes.workspace?.allowed));
const allowedProfiles = new Set(asArray(metadataAxes.execution_profiles?.allowed));

const errors = [];

async function walkForSymlinks(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isSymbolicLink()) {
      out.push(toPosix(path.relative(root, full)));
      continue;
    }
    if (entry.isDirectory()) {
      await walkForSymlinks(full, out);
    }
  }
  return out;
}

for (const symlinkPath of await walkForSymlinks(root)) {
  errors.push(`repo symlink is not allowed: ${symlinkPath}`);
}

for (const { file, data } of parsed) {
  const sections = [
    ["files", data.files ?? {}],
    ["subdirs", data.subdirs ?? {}],
    ["standalone", data.standalone ?? {}],
  ];

  if (data.kind && !allowedKinds.has(data.kind)) {
    errors.push(`${toPosix(path.relative(root, file))}: unknown top-level kind=${JSON.stringify(data.kind)}`);
  }
  if (data.toolchain && !allowedToolchains.has(data.toolchain)) {
    errors.push(`${toPosix(path.relative(root, file))}: unknown top-level toolchain=${JSON.stringify(data.toolchain)}`);
  }
  if (data.maturity && !allowedMaturities.has(data.maturity)) {
    errors.push(`${toPosix(path.relative(root, file))}: unknown top-level maturity=${JSON.stringify(data.maturity)}`);
  }
  if (data.workspace && !allowedWorkspaces.has(data.workspace)) {
    errors.push(`${toPosix(path.relative(root, file))}: unknown top-level workspace=${JSON.stringify(data.workspace)}`);
  }
  for (const profile of asArray(data.execution_profiles)) {
    if (!allowedProfiles.has(profile)) {
      errors.push(`${toPosix(path.relative(root, file))}: unknown top-level execution_profiles entry=${JSON.stringify(profile)}`);
    }
  }

  for (const [sectionName, entries] of sections) {
    for (const [entryKey, entry] of Object.entries(entries)) {
      validateEntry({
        depsFile: file,
        sectionName,
        entryKey,
        entry,
        allowedKinds,
        allowedToolchains,
        allowedMaturities,
        allowedWorkspaces,
        allowedProfiles,
        errors,
      });
    }
  }
}

if (errors.length > 0) {
  console.error("lint:deps:metadata failed");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`lint:deps:metadata ok (${depsFiles.length} deps.toml files checked)`);
