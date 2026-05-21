// source-repo/extract.ts — invoke the Python AST helper from cli.ts.
//
// The helper (../../scripts/extract-click.py) emits a kami manifest JSON
// on stdout. We capture, JSON.parse, and validate via the binary-mode
// types since the manifest shape is identical.

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { validateManifest, type KamiManifest } from "../binary/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const EXTRACTOR = join(__dirname, "..", "..", "scripts", "extract-click.py");

export interface ExtractClickArgs {
  source: string; // path to a directory or .py file
  kamiId: string; // e.g. "bin:cookiecutter"
  binary: string; // e.g. "cookiecutter"
  description?: string;
  versionFlag?: string;
}

export function extractClickManifest(args: ExtractClickArgs): KamiManifest {
  const argv: string[] = [
    EXTRACTOR,
    args.source,
    "--kami-id",
    args.kamiId,
    "--binary",
    args.binary,
  ];
  if (args.description) argv.push("--description", args.description);
  if (args.versionFlag) argv.push("--version-flag", args.versionFlag);

  const result = spawnSync("python3", argv, { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
  if (result.error) {
    throw new Error(`extract-click spawn failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const tail = (result.stderr ?? "").trim().split("\n").slice(-10).join("\n");
    throw new Error(`extract-click exited ${result.status}:\n${tail}`);
  }
  const stdout = result.stdout ?? "";
  if (!stdout.trim()) {
    throw new Error("extract-click produced no output");
  }
  const parsed = JSON.parse(stdout);
  return validateManifest(parsed);
}
