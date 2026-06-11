// browser/emit-lexicon.ts — L1 emitter for browser-only mode.
//
// Phase 3 (ADR-2605211900) ships only the L1 lexicon for browser-only
// yorishiri. The lexicon carries enough manifest detail
// (x-yorishiro-browser block) that a future L2/L3 driver can replay the
// step sequence without re-parsing the kami manifest.

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { BrowserKamiManifest, BrowserOp } from "./types.js";

export interface EmitArgs {
  repoRoot: string;
  name: string;
  purposes: readonly string[];
  manifest: BrowserKamiManifest;
}

export interface Emitted {
  nsid: string;
  path: string;
}

export function emitBrowserLexicons(args: EmitArgs): Emitted[] {
  const outDir = join(args.repoRoot, "00-contracts/lexicons/ai/etzhayyim/yorishiro", args.name);
  mkdirSync(outDir, { recursive: true });
  const out: Emitted[] = [];
  for (const op of args.manifest.ops) {
    const nsid = `ai.etzhayyim.yorishiro.${args.name}.${op.name}`;
    const lex = buildBrowserLexicon(args.manifest, op, args.purposes, nsid);
    const file = join(outDir, `${op.name}.json`);
    writeFileSync(file, JSON.stringify(lex, null, 2) + "\n", "utf-8");
    out.push({ nsid, path: file });
  }
  return out;
}

function buildBrowserLexicon(
  manifest: BrowserKamiManifest,
  op: BrowserOp,
  purposes: readonly string[],
  nsid: string,
): unknown {
  // Derive input properties from the step value_input_keys (any step
  // that fills or selects from input requires that key in the input).
  const requiredKeys = new Set<string>();
  for (const step of op.steps) {
    if (step.kind === "fill" || step.kind === "select") {
      requiredKeys.add(step.value_input_key);
    }
  }
  const inputProps: Record<string, unknown> = {};
  for (const k of requiredKeys) {
    inputProps[k] = { type: "string", description: `Value bound to a DOM step input.` };
  }

  // Output schema mirrors the extract array — each extract emits one
  // top-level key. Without extracts, the op returns { ok: true }.
  const outputProps: Record<string, unknown> = {
    ok: { type: "boolean" },
    error: { type: "string" },
  };
  if (op.extract) {
    for (const e of op.extract) {
      outputProps[e.output_key] = e.multiple
        ? { type: "array", items: { type: "string" }, description: `DOM extract ${e.selector}` }
        : { type: "string", description: `DOM extract ${e.selector}` };
    }
  }

  return {
    lexicon: 1,
    id: nsid,
    defs: {
      main: {
        type: "procedure",
        description: op.description || op.summary || nsid,
        "x-yorishiro-external": true,
        "x-yorishiro-kami": manifest.kami.id,
        "x-yorishiro-transport": "browser-only",
        "x-yorishiro-browser": {
          base_url: manifest.kami.base_url,
          auth_hint: manifest.kami.auth_hint ?? "none",
          steps: op.steps,
          extract: op.extract ?? [],
        },
        "x-charter-purpose": [...purposes],
        input: {
          encoding: "application/json",
          schema: { type: "object", required: [...requiredKeys], properties: inputProps },
        },
        output: {
          encoding: "application/json",
          schema: { type: "object", required: ["ok"], properties: outputProps },
        },
      },
    },
  };
}
