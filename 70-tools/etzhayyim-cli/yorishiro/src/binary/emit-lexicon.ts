// binary/emit-lexicon.ts — L1 emitter for binary-cli mode.

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { BinaryArg, BinaryOp, KamiManifest } from "./types.js";

export interface EmitArgs {
  repoRoot: string;
  name: string;
  purposes: readonly string[];
  manifest: KamiManifest;
}

export interface Emitted {
  nsid: string;
  path: string;
}

export function emitBinaryLexicons(args: EmitArgs): Emitted[] {
  const outDir = join(args.repoRoot, "00-contracts/lexicons/ai/etzhayyim/yorishiro", args.name);
  mkdirSync(outDir, { recursive: true });
  const out: Emitted[] = [];
  for (const op of args.manifest.ops) {
    const nsid = `ai.etzhayyim.yorishiro.${args.name}.${op.name}`;
    const lex = buildBinaryLexicon(args.name, args.manifest, op, args.purposes, nsid);
    const file = join(outDir, `${op.name}.json`);
    writeFileSync(file, JSON.stringify(lex, null, 2) + "\n", "utf-8");
    out.push({ nsid, path: file });
  }
  return out;
}

function buildBinaryLexicon(
  _name: string,
  manifest: KamiManifest,
  op: BinaryOp,
  purposes: readonly string[],
  nsid: string,
): unknown {
  const props: Record<string, unknown> = {};
  const required: string[] = [];
  for (const a of op.argv) {
    props[a.name] = argSchema(a);
    if (a.kind === "positional" && (a.required ?? true)) required.push(a.name);
    if (a.kind === "flag" && a.required) required.push(a.name);
  }

  const main: Record<string, unknown> = {
    type: "procedure",
    description: op.description || op.summary || nsid,
    "x-yorishiro-external": true,
    "x-yorishiro-kami": manifest.kami.id,
    "x-yorishiro-transport": "binary-cli",
    "x-yorishiro-binary": {
      binary: manifest.kami.binary,
      argv: op.argv,
      stdout_capture: op.stdout_capture ?? true,
      stderr_capture: op.stderr_capture ?? true,
      exit_code_ok: op.exit_code_ok ?? [0],
      timeout_seconds: op.timeout_seconds ?? 60,
    },
    "x-charter-purpose": [...purposes],
    input: {
      encoding: "application/json",
      schema: { type: "object", required, properties: props },
    },
    output: {
      encoding: "application/json",
      schema: {
        type: "object",
        required: ["exitCode"],
        properties: {
          exitCode: { type: "integer", description: "Exit code of the binary." },
          stdout: { type: "string", description: "Captured stdout (UTF-8 best-effort)." },
          stderr: { type: "string", description: "Captured stderr (UTF-8 best-effort)." },
          error: { type: "string", description: "Set when the binary could not be launched at all." },
        },
      },
    },
  };

  return { lexicon: 1, id: nsid, defs: { main } };
}

function argSchema(a: BinaryArg): unknown {
  const t = a.type ?? (a.kind === "flag" ? "string" : "string");
  const out: Record<string, unknown> = { type: t };
  if (a.description) out.description = a.description;
  if (a.default !== undefined) out.default = a.default;
  return out;
}
