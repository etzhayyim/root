#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";

const root = process.cwd();

async function walk(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name === "node_modules" || e.name === ".git" || e.name.startsWith(".")) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      await walk(full, out);
    } else if (/\.(ts|tsx|mts|cts|js|mjs|cjs)$/.test(e.name)) {
      out.push(full);
    }
  }
  return out;
}

function toPosix(p) {
  return p.split(path.sep).join("/");
}

function extractImports(src) {
  const specs = [];
  const re = /\b(?:import|export)\b[\s\S]*?\bfrom\s*["']([^"']+)["']/g;
  const dyn = /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g;
  for (const m of src.matchAll(re)) specs.push(m[1]);
  for (const m of src.matchAll(dyn)) specs.push(m[1]);
  return specs;
}

function resolveSpecifier(fileAbs, spec) {
  if (!spec.startsWith(".") && !spec.startsWith("/")) return null;
  const resolved = spec.startsWith("/")
    ? path.resolve(root, spec.slice(1))
    : path.resolve(path.dirname(fileAbs), spec);
  return toPosix(path.relative(root, resolved));
}

function isUnder(relPath, prefix) {
  return relPath === prefix || relPath.startsWith(`${prefix}/`);
}

const files = await walk(root);
const violations = [];

for (const abs of files) {
  const rel = toPosix(path.relative(root, abs));
  const src = await fs.readFile(abs, "utf8");
  const specs = extractImports(src);

  for (const spec of specs) {
    const resolvedRel = resolveSpecifier(abs, spec);
    const specPosix = spec.replace(/\\/g, "/");

    if (isUnder(rel, "packages/runtime")) {
      const hit =
        specPosix.startsWith("infra/") ||
        specPosix.includes("/infra/") ||
        (resolvedRel && isUnder(resolvedRel, "infra"));
      if (hit) {
        violations.push(`${rel}: runtime must not depend on infra (${spec})`);
      }
    }

    if (isUnder(rel, "packages/contract")) {
      const hitRuntime =
        specPosix.startsWith("packages/runtime") ||
        specPosix.includes("/packages/runtime/") ||
        specPosix.includes("@etzhayyim/kotodama-host-sdk") ||
        (resolvedRel && isUnder(resolvedRel, "packages/runtime"));
      const hitInfra =
        specPosix.startsWith("infra/") ||
        specPosix.includes("/infra/") ||
        (resolvedRel && isUnder(resolvedRel, "infra"));
      if (hitRuntime || hitInfra) {
        violations.push(`${rel}: contract must not depend on runtime/infra (${spec})`);
      }
    }

    if (rel === "infra/cloudflare/workers/atproto/src/pds-app.ts") {
      if (specPosix === "./index" || specPosix === "./index.ts" || specPosix === "../index" || specPosix === "../index.ts") {
        violations.push(`${rel}: pds-app must not import index (${spec})`);
      }
    }
  }
}

if (violations.length > 0) {
  console.error("Dependency boundary violations:");
  for (const v of violations) console.error(`- ${v}`);
  process.exit(1);
}

console.log("Dependency boundary check passed.");
