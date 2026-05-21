// source-repo/extract.ts — invoke a Python AST helper from cli.ts.
//
// Dispatches on the `framework` field:
//   click / argparse / auto → scripts/extract-click.py (polyglot Python walker)
//   cobra                   → scripts/extract-cobra.py  (Go heuristic)
//   clap                    → scripts/extract-clap.py   (Rust heuristic)
//
// All three helpers emit a kami manifest JSON (binary-mode shape) on
// stdout. We capture, JSON.parse, and validate.

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { validateManifest, type KamiManifest } from "../binary/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SCRIPTS_DIR = join(__dirname, "..", "..", "scripts");

export type SourceFramework = "click" | "argparse" | "auto" | "cobra" | "clap";

export interface ExtractClickArgs {
  source: string;
  kamiId: string;
  binary: string;
  framework?: SourceFramework;
  description?: string;
  versionFlag?: string;
}

export function extractClickManifest(args: ExtractClickArgs): KamiManifest {
  const fw: SourceFramework = args.framework ?? "auto";
  const extractor =
    fw === "cobra"
      ? join(SCRIPTS_DIR, "extract-cobra.py")
      : fw === "clap"
        ? join(SCRIPTS_DIR, "extract-clap.py")
        : join(SCRIPTS_DIR, "extract-click.py");

  const argv: string[] = [extractor, args.source, "--kami-id", args.kamiId, "--binary", args.binary];
  if (args.description) argv.push("--description", args.description);
  if (args.versionFlag) argv.push("--version-flag", args.versionFlag);
  // Only the polyglot Python walker accepts --framework (it dispatches
  // click vs argparse internally). Cobra / clap have no such flag.
  if (fw === "click" || fw === "argparse" || fw === "auto") {
    argv.push("--framework", fw);
  }

  const result = spawnSync("python3", argv, { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
  if (result.error) {
    throw new Error(`extract spawn failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const tail = (result.stderr ?? "").trim().split("\n").slice(-10).join("\n");
    throw new Error(`extract exited ${result.status}:\n${tail}`);
  }
  const stdout = result.stdout ?? "";
  if (!stdout.trim()) {
    throw new Error("extract produced no output");
  }
  const parsed = JSON.parse(stdout);
  return validateManifest(parsed);
}
