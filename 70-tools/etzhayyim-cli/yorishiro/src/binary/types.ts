// binary/types.ts — kami manifest shape for the `binary-cli` mode.
//
// A kami manifest describes a local binary's CLI surface in enough detail
// for the generator to emit a yorishiro that invokes it safely (no shell
// interpolation; argv-as-list only).

export interface KamiManifest {
  kami: {
    id: string; // e.g. "bin:pdftotext"
    binary: string; // binary name (must be on PATH at cell runtime) or absolute path
    description?: string;
    version_flag?: string; // e.g. "--version" or "-v" — liveness probe
  };
  ops: BinaryOp[];
}

export interface BinaryOp {
  name: string; // op name, becomes the lexicon NSID tail
  summary?: string;
  description?: string;
  argv: BinaryArg[];
  stdout_capture?: boolean; // default true
  stderr_capture?: boolean; // default true
  exit_code_ok?: number[]; // default [0]
  timeout_seconds?: number; // default 60
}

export type BinaryArg = PositionalArg | FlagArg;

export interface PositionalArg {
  kind: "positional";
  name: string;
  position: number; // 0-based positional index
  required?: boolean; // default true
  type?: "string" | "integer" | "number";
  default?: string | number;
  description?: string;
}

export interface FlagArg {
  kind: "flag";
  name: string; // input JSON key
  flag: string; // CLI literal flag, e.g. "-f" or "--first-page"
  type?: "string" | "integer" | "number" | "boolean";
  required?: boolean; // default false
  default?: string | number | boolean;
  separator?: " " | "="; // default " " — boolean flags ignore this
  description?: string;
}

export function validateManifest(m: unknown): KamiManifest {
  if (!m || typeof m !== "object") throw new Error("manifest must be an object");
  const km = m as KamiManifest;
  if (!km.kami || typeof km.kami !== "object") throw new Error("manifest.kami missing");
  if (!km.kami.id || typeof km.kami.id !== "string") throw new Error("manifest.kami.id missing");
  if (!km.kami.binary || typeof km.kami.binary !== "string") throw new Error("manifest.kami.binary missing");
  if (!Array.isArray(km.ops) || km.ops.length === 0) throw new Error("manifest.ops must be a non-empty array");
  for (const op of km.ops) {
    if (!op.name || typeof op.name !== "string") throw new Error(`op.name missing on ${JSON.stringify(op)}`);
    if (!Array.isArray(op.argv)) throw new Error(`op.argv missing on op ${op.name}`);
    for (const a of op.argv) {
      if (a.kind !== "positional" && a.kind !== "flag") throw new Error(`unknown arg.kind on op ${op.name}: ${(a as { kind?: string }).kind}`);
      if (!a.name) throw new Error(`arg.name missing on op ${op.name}`);
      if (a.kind === "flag" && !a.flag) throw new Error(`flag arg without .flag literal on op ${op.name} arg ${a.name}`);
    }
  }
  return km;
}
