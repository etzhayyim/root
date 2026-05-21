#!/usr/bin/env node
// yorishiro CLI — generator entry point. Per ADR-2605211900 Phase 1.
//
// Phase 1 commands:
//   yorishiro create <name> --from openapi-v3 --source <url-or-path>
//                           --kami <fqdn> --purpose <csv> [--base-url <url>]
//   yorishiro regen  <name>                          (re-reads stored config)
//   yorishiro list
//   yorishiro audit
//
// Source modes other than openapi-v3 are stubbed and will error out with
// a "Phase N pending" message — they're explicitly out of Phase 1 scope.

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

import { audit as runAudit } from "./audit.js";
import { emitCell } from "./emit/cell-py.js";
import { emitLexicons } from "./emit/lexicon.js";
import { emitMcpServer } from "./emit/mcp-server.js";
import { emitSkill } from "./emit/skill-md.js";
import { normalize, readOpenApi } from "./openapi/parse.js";
import { parsePurposeCsv, validateExternalPurposes } from "./purpose.js";

const VERSION = "0.1.0";

interface CreateArgs {
  name: string;
  from: string;
  source: string;
  kami: string;
  purpose: string;
  baseUrl?: string;
  dryRun: boolean;
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const sub = args[0];

  switch (sub) {
    case "create":
      await cmdCreate(args.slice(1));
      return;
    case "regen":
      await cmdRegen(args.slice(1));
      return;
    case "list":
      cmdList();
      return;
    case "audit":
      cmdAudit();
      return;
    case "version":
    case "--version":
    case "-v":
      console.log(`yorishiro ${VERSION}`);
      return;
    case undefined:
    case "help":
    case "--help":
    case "-h":
      printUsage();
      return;
    default:
      console.error(`yorishiro: unknown subcommand '${sub}'`);
      printUsage();
      process.exit(1);
  }
}

function printUsage(): void {
  console.log(`yorishiro ${VERSION} — external app/webservice → 3-layer etzhayyim actor generator
Per ADR-2605211900. See ../README.md.

USAGE:
  yorishiro create <name> --from openapi-v3 --source <url-or-path>
                          --kami <fqdn>      --purpose <csv>
                         [--base-url <url>] [--dry-run]
  yorishiro regen <name>
  yorishiro list
  yorishiro audit
  yorishiro version

Phase 1 supports --from=openapi-v3 only. source-repo / browser-only /
binary-cli will land in Phase 2/3.
`);
}

async function cmdCreate(rest: string[]): Promise<void> {
  const parsed = parseFlags(rest);
  if (!parsed.positional[0]) fail("yorishiro create: name is required");
  const args: CreateArgs = {
    name: parsed.positional[0]!,
    from: parsed.flags["from"] ?? "openapi-v3",
    source: parsed.flags["source"] ?? "",
    kami: parsed.flags["kami"] ?? "",
    purpose: parsed.flags["purpose"] ?? "",
    baseUrl: parsed.flags["base-url"],
    dryRun: parsed.boolFlags.has("dry-run"),
  };
  if (!args.source) fail("--source is required");
  if (!args.kami) fail("--kami is required");
  if (!args.purpose) fail("--purpose is required (csv, e.g. grant,kisha)");
  if (args.from !== "openapi-v3") {
    fail(`--from ${args.from} not supported in Phase 1 (only openapi-v3). See ADR-2605211900 D7.`);
  }
  await createFromOpenApi(args);
}

async function createFromOpenApi(args: CreateArgs): Promise<void> {
  const repoRoot = findRepoRoot();
  const purposes = parsePurposeCsv(args.purpose);
  const check = validateExternalPurposes(purposes);
  if (!check.ok) {
    console.error(`yorishiro: invalid --purpose values`);
    if (check.forbidden.length > 0) {
      console.error(`  forbidden (ADR-2605192115 §4): ${check.forbidden.join(", ")}`);
    }
    if (check.invalid.length > 0) {
      console.error(`  unknown : ${check.invalid.join(", ")}`);
    }
    process.exit(1);
  }

  console.error(`[yorishiro] reading OpenAPI spec from ${args.source}`);
  const spec = await readOpenApi(args.source);
  const ops = normalize(spec);
  if (ops.length === 0) fail(`OpenAPI spec has no operations to emit`);

  const baseUrl = args.baseUrl ?? spec.servers?.[0]?.url ?? "";
  if (!baseUrl) fail(`could not derive base URL; pass --base-url or set servers[] in the spec`);

  console.error(`[yorishiro] kami=${args.kami}  base=${baseUrl}  ops=${ops.length}  purposes=[${purposes.join(",")}]`);

  if (args.dryRun) {
    for (const op of ops) {
      console.error(`  (dry-run) ${op.httpMethod.padEnd(6)} ${op.pathTemplate}  → ${op.opName}`);
    }
    return;
  }

  // Persist config so `yorishiro regen` can re-run without all the flags.
  const cfgDir = join(repoRoot, "70-tools/etzhayyim-cli/yorishiro/registry");
  mkdirSync(cfgDir, { recursive: true });
  const cfg = {
    name: args.name,
    from: args.from,
    source: resolveSource(args.source, repoRoot),
    kami: args.kami,
    baseUrl,
    purposes,
    generatedAt: new Date().toISOString(),
    generator: `@etzhayyim/yorishiro@${VERSION}`,
  };
  writeFileSync(join(cfgDir, `${args.name}.json`), JSON.stringify(cfg, null, 2) + "\n", "utf-8");

  const lexicons = emitLexicons({
    repoRoot,
    name: args.name,
    kami: args.kami,
    transport: "openapi-v3",
    purposes,
    ops,
  });
  console.error(`[yorishiro] L1: emitted ${lexicons.length} lexicon(s)`);

  const cell = emitCell({
    repoRoot,
    name: args.name,
    kami: args.kami,
    baseUrl,
    transport: "openapi-v3",
    purposes,
    ops,
  });
  console.error(`[yorishiro] L2: wrote ${cell.path}`);

  const mcp = emitMcpServer({
    repoRoot,
    name: args.name,
    kami: args.kami,
    baseUrl,
    transport: "openapi-v3",
    purposes,
    ops,
  });
  console.error(`[yorishiro] L3: wrote ${mcp.files.length} file(s) under ${mcp.packageDir}`);

  const skill = emitSkill({
    repoRoot,
    name: args.name,
    kami: args.kami,
    purposes,
    ops,
  });
  console.error(`[yorishiro] SKILL.md: ${skill}`);

  console.error(`[yorishiro] done. Run \`yorishiro audit\` to verify Charter compliance.`);
}

async function cmdRegen(rest: string[]): Promise<void> {
  const name = rest[0];
  if (!name) fail("yorishiro regen: name required");
  const repoRoot = findRepoRoot();
  const cfgPath = join(repoRoot, "70-tools/etzhayyim-cli/yorishiro/registry", `${name}.json`);
  if (!existsSync(cfgPath)) fail(`no registry entry for ${name} at ${cfgPath}`);
  const cfg = JSON.parse(readFileSync(cfgPath, "utf-8"));
  // registry entries authored before the resolveSource() landing carry
  // relative paths; rewrite them against repoRoot so the regen works
  // from any cwd.
  const sourceResolved = resolveSource(cfg.source, repoRoot);
  await createFromOpenApi({
    name: cfg.name,
    from: cfg.from,
    source: sourceResolved,
    kami: cfg.kami,
    purpose: cfg.purposes.join(","),
    baseUrl: cfg.baseUrl,
    dryRun: false,
  });
}

function cmdList(): void {
  const repoRoot = findRepoRoot();
  const dir = join(repoRoot, "70-tools/etzhayyim-cli/yorishiro/registry");
  if (!existsSync(dir)) {
    console.log("(no yorishiri registered)");
    return;
  }
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".json")) continue;
    const cfg = JSON.parse(readFileSync(join(dir, f), "utf-8"));
    console.log(`${cfg.name.padEnd(20)} kami=${cfg.kami}  purposes=[${cfg.purposes.join(",")}]  base=${cfg.baseUrl}`);
  }
}

function cmdAudit(): void {
  const repoRoot = findRepoRoot();
  const findings = runAudit(repoRoot);
  if (findings.length === 0) {
    console.log("yorishiro audit: ok (no findings)");
    return;
  }
  for (const f of findings) {
    console.error(`✘ ${f.file}\n    ${f.nsid}  ${f.reason}`);
  }
  console.error(`\nyorishiro audit: ${findings.length} finding(s)`);
  process.exit(1);
}

function fail(msg: string): never {
  console.error(`yorishiro: ${msg}`);
  process.exit(1);
}

interface ParsedFlags {
  positional: string[];
  flags: Record<string, string>;
  boolFlags: Set<string>;
}

function parseFlags(argv: string[]): ParsedFlags {
  const positional: string[] = [];
  const flags: Record<string, string> = {};
  const boolFlags = new Set<string>();
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        boolFlags.add(key);
      } else {
        flags[key] = next;
        i++;
      }
    } else {
      positional.push(a);
    }
  }
  return { positional, flags, boolFlags };
}

function findRepoRoot(): string {
  let dir = process.cwd();
  while (true) {
    if (existsSync(join(dir, "CLAUDE.md")) && existsSync(join(dir, "90-docs"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) {
      console.error("yorishiro: could not locate repo root (looked for CLAUDE.md + 90-docs/)");
      process.exit(1);
    }
    dir = parent;
  }
}

function resolveSource(src: string, repoRoot: string): string {
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  // Path resolution: absolute paths pass through, relative paths resolve
  // against the user's cwd (where they typed the `yorishiro` command).
  // repoRoot is unused for source resolution but is the right anchor for
  // the *output* tree (handled by the emitters).
  return resolve(src);
}

main().catch((err) => {
  console.error("yorishiro: fatal:", err);
  process.exit(1);
});
