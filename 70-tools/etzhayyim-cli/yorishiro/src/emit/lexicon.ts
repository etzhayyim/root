// emit/lexicon.ts — L1 emitter. Produces one atproto Lexicon JSON per op.
//
// Lexicon NSID convention (D1 in ADR-2605211900):
//   ai.etzhayyim.yorishiro.<name>.<opName>

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { JsonSchema, NormalizedOp } from "../openapi/parse.js";

export interface EmitLexiconArgs {
  repoRoot: string;
  name: string;
  kami: string;
  transport: "openapi-v3" | "source-repo" | "browser-only" | "binary-cli";
  purposes: readonly string[];
  ops: readonly NormalizedOp[];
}

export interface EmittedLexicon {
  nsid: string;
  path: string;
}

export function emitLexicons(args: EmitLexiconArgs): EmittedLexicon[] {
  const outDir = join(
    args.repoRoot,
    "00-contracts/lexicons/ai/etzhayyim/yorishiro",
    args.name,
  );
  mkdirSync(outDir, { recursive: true });

  const out: EmittedLexicon[] = [];
  for (const op of args.ops) {
    const nsid = `ai.etzhayyim.yorishiro.${args.name}.${op.opName}`;
    const isQuery = op.httpMethod === "GET" || op.httpMethod === "HEAD";
    const lex = buildLexicon({ ...args, op, nsid, isQuery });
    const file = join(outDir, `${op.opName}.json`);
    writeFileSync(file, JSON.stringify(lex, null, 2) + "\n", "utf-8");
    out.push({ nsid, path: file });
  }
  return out;
}

interface BuildArgs extends EmitLexiconArgs {
  op: NormalizedOp;
  nsid: string;
  isQuery: boolean;
}

function buildLexicon(args: BuildArgs): unknown {
  const { op, nsid, isQuery } = args;

  const paramProps: Record<string, JsonSchema> = {};
  const required: string[] = [];
  for (const p of op.parameters) {
    paramProps[p.name] = {
      ...p.schema,
      description: p.description || p.schema.description || "",
    };
    if (p.required) required.push(p.name);
  }

  const main: Record<string, unknown> = {
    type: isQuery ? "query" : "procedure",
    description: op.description || op.summary || nsid,
    "x-yorishiro-external": true,
    "x-yorishiro-kami": args.kami,
    "x-yorishiro-transport": args.transport,
    "x-yorishiro-http": {
      method: op.httpMethod,
      pathTemplate: op.pathTemplate,
      responseContentType: op.responseContentType,
    },
    "x-charter-purpose": [...args.purposes],
  };

  if (isQuery) {
    main.parameters = {
      type: "params",
      required,
      properties: paramProps,
    };
  } else {
    const bodyProps =
      op.requestBodySchema?.properties ?? paramProps;
    const bodyRequired = op.requestBodySchema?.required ?? required;
    main.input = {
      encoding: "application/json",
      schema: {
        type: "object",
        required: bodyRequired,
        properties: bodyProps,
      },
    };
  }

  main.output = {
    encoding: "application/json",
    schema: wrapOutputSchema(op),
  };

  return {
    lexicon: 1,
    id: nsid,
    defs: { main },
  };
}

function wrapOutputSchema(op: NormalizedOp): unknown {
  // Wrap raw responses (e.g. atom+xml, text/plain, octet-stream) as
  //   { body: string, httpStatus: integer, error?: string }
  // JSON responses pass through verbatim alongside the same envelope so
  // callers always know whether the upstream call succeeded.
  if (op.responseContentType === "application/json" && op.responseSchema.type === "object") {
    return {
      type: "object",
      required: ["httpStatus"],
      properties: {
        httpStatus: { type: "integer" },
        json: op.responseSchema,
        error: { type: "string" },
      },
    };
  }
  return {
    type: "object",
    required: ["httpStatus"],
    properties: {
      httpStatus: { type: "integer" },
      body: { type: "string", description: `Raw ${op.responseContentType} body from kami.` },
      error: { type: "string" },
    },
  };
}
