#!/usr/bin/env node
/**
 * kg-projector — SSoT → com.etzhayyim.kg.{node,edge} projector.
 *
 * Stage K1 of ADR-2605190900. Writes JSON record files; MST/PDS write is a follow-up.
 *
 *   kg-projector project              # project → out/
 *   kg-projector project --check      # exit 1 if fresh projection differs from out/
 *   kg-projector project --out <dir>  # custom output directory
 *   kg-projector project --repo-root <dir>
 */

import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync, statSync } from "node:fs";

import { projectAdrs } from "./sources/adr.js";
import { projectLexicons } from "./sources/lexicon.js";
import { projectDepsToml } from "./sources/deps-toml.js";
import { mergeProjections, type KgProjection } from "./types.js";
import { diffAgainstExisting, writeOut } from "./emit.js";

interface CliArgs {
  command: "project" | "help";
  check: boolean;
  outDir?: string;
  repoRoot?: string;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { command: "help", check: false };
  if (argv[0] === "project") args.command = "project";
  else if (argv[0] === "help" || argv[0] === "--help") args.command = "help";
  else if (argv[0]) {
    console.error(`kg-projector: unknown command "${argv[0]}"`);
    process.exit(2);
  }
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--check") args.check = true;
    else if (a === "--out") args.outDir = argv[++i];
    else if (a === "--repo-root") args.repoRoot = argv[++i];
    else {
      console.error(`kg-projector: unknown flag "${a}"`);
      process.exit(2);
    }
  }
  return args;
}

function packageRoot(): string {
  // Walk up from this file until we find package.json named @etzhayyim/kg-projector.
  let dir = dirname(fileURLToPath(import.meta.url));
  for (let i = 0; i < 6; i++) {
    try {
      const pkgPath = resolve(dir, "package.json");
      const pkg = JSON.parse(readFileSync(pkgPath, "utf8")) as { name?: string };
      if (pkg.name === "@etzhayyim/kg-projector") return dir;
    } catch {
      /* keep walking */
    }
    dir = resolve(dir, "..");
  }
  // Fallback: assume dist/ layout.
  return resolve(dirname(fileURLToPath(import.meta.url)), "..");
}

function isRepoRoot(dir: string): boolean {
  try {
    return (
      statSync(resolve(dir, "deps.toml")).isFile() &&
      statSync(resolve(dir, "90-docs", "adr")).isDirectory()
    );
  } catch {
    return false;
  }
}

function defaultRepoRoot(): string {
  let dir = packageRoot();
  for (let i = 0; i < 8; i++) {
    if (isRepoRoot(dir)) return dir;
    dir = resolve(dir, "..");
  }
  throw new Error(
    "kg-projector: could not locate repo root (deps.toml + 90-docs/adr) by walking up from package root. Pass --repo-root.",
  );
}

function defaultOutDir(): string {
  return resolve(packageRoot(), "out");
}

function printHelp(): void {
  console.log(
    `kg-projector — Stage K1 of ADR-2605190900

Usage:
  kg-projector project [--check] [--out <dir>] [--repo-root <dir>]
  kg-projector help

Flags:
  --check       Compare a fresh projection against existing out/. Exit 1 on mismatch. Does not write.
  --out <dir>   Output directory (default: <package>/out)
  --repo-root <dir>  Monorepo root (default: ../../.. from the package)
`,
  );
}

async function runProject(args: CliArgs): Promise<void> {
  const repoRoot = args.repoRoot ?? defaultRepoRoot();
  const outDir = args.outDir ?? defaultOutDir();

  const parts: KgProjection[] = [
    await projectDepsToml(repoRoot),
    await projectAdrs(repoRoot),
    await projectLexicons(repoRoot),
  ];
  const proj = mergeProjections(...parts);

  if (args.check) {
    const { matches, fresh, existing } = await diffAgainstExisting(outDir, proj);
    if (matches) {
      console.log(
        `[kg-projector] check OK · nodes=${fresh.node_count} edges=${fresh.edge_count} content_hash=${fresh.content_hash}`,
      );
      return;
    }
    console.error(
      `[kg-projector] check FAILED · fresh content_hash=${fresh.content_hash}` +
        ` existing=${existing ? existing.content_hash : "<none>"}`,
    );
    process.exit(1);
  }

  const manifest = await writeOut(outDir, proj);
  console.log(
    `[kg-projector] wrote nodes=${manifest.node_count} edges=${manifest.edge_count}` +
      ` sources=${Object.entries(manifest.source_counts)
        .map(([k, v]) => `${k}:${v}`)
        .join(",")}` +
      ` content_hash=${manifest.content_hash}`,
  );
  console.log(`[kg-projector] out → ${outDir}`);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (args.command === "help") {
    printHelp();
    return;
  }
  await runProject(args);
}

main().catch((err) => {
  console.error("[kg-projector] fatal:", err);
  process.exit(2);
});
