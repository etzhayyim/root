#!/usr/bin/env node

import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();

function firstExisting(...candidates) {
  for (const rel of candidates) {
    const full = path.join(root, rel);
    if (existsSync(full)) return full;
  }
  return null;
}

function runTsc(tsconfigPath, label) {
  try {
    execFileSync("pnpm", ["exec", "tsc", "-p", tsconfigPath, "--noEmit"], {
      stdio: "inherit",
      cwd: root,
    });
  } catch (error) {
    const tagged = new Error(`dependency boundary type-check failed (${label})`);
    tagged.label = label;
    throw tagged;
  }
}

const tmpDir = await mkdtemp(path.join(os.tmpdir(), "etzhayyim-boundary-typecheck-"));
const pdsSuffix = ".__etzhayyim_boundary_forbidden__";
const pdsForbiddenModuleBody = "export const FORBIDDEN_INDEX_IMPORT = ;\n";
const pdsForbiddenSrcIndexPath = firstExisting(
  `50-infra/cloudflare/workers/atproto/src/index${pdsSuffix}.ts`,
  `infra/cloudflare/workers/atproto/src/index${pdsSuffix}.ts`,
);
const pdsForbiddenParentIndexPath = firstExisting(
  `50-infra/cloudflare/workers/atproto/index${pdsSuffix}.ts`,
  `infra/cloudflare/workers/atproto/index${pdsSuffix}.ts`,
);

let failedLabel = null;

try {
  const runtimeConfigPath = path.join(tmpDir, "runtime-boundary-check.tsconfig.json");
  const contractConfigPath = path.join(tmpDir, "contract-boundary-check.tsconfig.json");
  const pdsConfigPath = path.join(tmpDir, "pds-app-boundary-check.tsconfig.json");
  const forbiddenModulePath = path.join(tmpDir, "forbidden-import.ts");

  // Any disallowed import that resolves to this file becomes a hard syntax failure.
  await writeFile(forbiddenModulePath, "export const FORBIDDEN_IMPORT = ;\n");
  if (pdsForbiddenSrcIndexPath) await writeFile(pdsForbiddenSrcIndexPath, pdsForbiddenModuleBody);
  if (pdsForbiddenParentIndexPath) await writeFile(pdsForbiddenParentIndexPath, pdsForbiddenModuleBody);

  const runtimeTsconfigBase = firstExisting(
    "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/tsconfig.json",
    "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/tsconfig.json",
  );
  const runtimeIncludeRoot = firstExisting(
    "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src",
    "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src",
  );
  const contractIncludeRoot = firstExisting(
    "00-contracts/kotodama-host-contract/src",
    "packages/contract/kotodama-host-contract/src",
  );
  const pdsTsconfigBase = firstExisting(
    "50-infra/cloudflare/workers/atproto/tsconfig.json",
    "infra/cloudflare/workers/atproto/tsconfig.json",
  );
  const pdsAppPath = firstExisting(
    "50-infra/cloudflare/workers/atproto/src/pds-app.ts",
    "infra/cloudflare/workers/atproto/src/pds-app.ts",
  );

  if (!runtimeTsconfigBase || !runtimeIncludeRoot) {
    throw new Error("dependency boundary check paths not found");
  }

  const runtimeTsconfig = {
    extends: runtimeTsconfigBase,
    compilerOptions: {
      noEmit: true,
      noCheck: true,
      types: [],
      ignoreDeprecations: "6.0",
      baseUrl: tmpDir,
      paths: {
        "infra": ["./forbidden-import.ts"],
        "infra/*": ["./forbidden-import.ts"],
      },
    },
    include: [path.join(runtimeIncludeRoot, "**/*")],
  };

  if (contractIncludeRoot) {
    const contractTsconfig = {
      compilerOptions: {
        target: "ES2022",
        module: "ES2022",
        moduleResolution: "bundler",
        strict: true,
        noEmit: true,
        noCheck: true,
        skipLibCheck: true,
        esModuleInterop: true,
        ignoreDeprecations: "6.0",
        baseUrl: tmpDir,
        paths: {
          "infra": ["./forbidden-import.ts"],
          "infra/*": ["./forbidden-import.ts"],
          "packages/runtime": ["./forbidden-import.ts"],
          "packages/runtime/*": ["./forbidden-import.ts"],
          "@etzhayyim/kotodama-host-sdk": ["./forbidden-import.ts"],
          "@etzhayyim/kotodama-host-sdk/*": ["./forbidden-import.ts"],
        },
      },
      include: [path.join(contractIncludeRoot, "**/*.ts")],
    };
    await writeFile(contractConfigPath, JSON.stringify(contractTsconfig, null, 2));
  }

  if (pdsTsconfigBase && pdsAppPath) {
    const pdsTsconfig = {
      extends: pdsTsconfigBase,
      compilerOptions: {
        noEmit: true,
        noCheck: true,
        types: [],
        ignoreDeprecations: "6.0",
        moduleSuffixes: [pdsSuffix, ""],
      },
      include: [pdsAppPath],
    };
    await writeFile(pdsConfigPath, JSON.stringify(pdsTsconfig, null, 2));
  }

  await writeFile(runtimeConfigPath, JSON.stringify(runtimeTsconfig, null, 2));

  runTsc(runtimeConfigPath, "runtime->infra");
  if (contractIncludeRoot) runTsc(contractConfigPath, "contract->runtime/infra");
  if (pdsTsconfigBase && pdsAppPath) runTsc(pdsConfigPath, "pds-app->index");
} catch (error) {
  failedLabel = error?.label ?? "unknown";
} finally {
  if (pdsForbiddenSrcIndexPath) await rm(pdsForbiddenSrcIndexPath, { force: true });
  if (pdsForbiddenParentIndexPath) await rm(pdsForbiddenParentIndexPath, { force: true });
  await rm(tmpDir, { recursive: true, force: true });
}

if (failedLabel) {
  console.error(`\nBUILD BLOCKER: dependency boundary type-check failed (${failedLabel})`);
  process.exit(1);
}

console.log("dependency boundary type-checks: OK");
