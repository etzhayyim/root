/**
 * @etzhayyim/lexicon-to-zod
 *
 * Converts AT Protocol Lexicon JSON schemas to Zod validators for runtime
 * input/output validation in XRPC handlers.
 */

import { z, type ZodTypeAny } from "zod";
import type { LexiconDoc, LexiconObjectDef, LexiconProperty } from "./types.js";

/**
 * Convert a Lexicon object schema to a Zod object schema.
 */
export function lexiconObjectToZod(obj: LexiconObjectDef): ZodTypeAny {
  const shape: Record<string, ZodTypeAny> = {};
  const required = new Set(obj.required ?? []);

  for (const [name, p] of Object.entries(obj.properties ?? {})) {
    const z1 = lexiconPropertyToZod(p);
    shape[name] = required.has(name) ? z1 : z1.optional();
  }

  return z.object(shape);
}

/**
 * Convert a Lexicon property to a Zod schema.
 * Handles primitives, arrays, objects, enums, and formats.
 */
function lexiconPropertyToZod(p: LexiconProperty): ZodTypeAny {
  if (p.type === "string") {
    let s: z.ZodString = z.string();

    if (p.minLength !== undefined) s = s.min(p.minLength);
    if (p.maxLength !== undefined) s = s.max(p.maxLength);

    if (p.format === "uri") s = s.url();
    if (p.format === "datetime") s = s.datetime();

    // Enum or knownValues
    if (p.enum && p.enum.length > 0) {
      const values = p.enum.filter((v) => typeof v === "string") as string[];
      if (values.length > 0) {
        return z.enum(values as [string, ...string[]]).describe(p.description ?? "");
      }
    }
    if (p.knownValues && p.knownValues.length > 0) {
      return z.enum(p.knownValues as [string, ...string[]]).describe(p.description ?? "");
    }

    return p.description ? s.describe(p.description) : s;
  }

  if (p.type === "integer") {
    let n: z.ZodNumber = z.number().int();

    if (p.minimum !== undefined) n = n.min(p.minimum);
    if (p.maximum !== undefined) n = n.max(p.maximum);

    return p.description ? n.describe(p.description) : n;
  }

  if (p.type === "boolean") {
    return p.description ? z.boolean().describe(p.description) : z.boolean();
  }

  if (p.type === "array") {
    const inner = p.items ? lexiconPropertyToZod(p.items) : z.unknown();
    let a: z.ZodArray<ZodTypeAny> = z.array(inner);

    if (p.maxLength !== undefined) a = a.max(p.maxLength);
    if (p.minLength !== undefined) a = a.min(p.minLength);

    return p.description ? a.describe(p.description) : a;
  }

  if (p.type === "object") {
    const schema = lexiconObjectToZod(p as LexiconObjectDef);
    return p.description ? schema.describe(p.description) : schema;
  }

  if (p.type === "bytes") {
    let b: z.ZodType = z.instanceof(Uint8Array);
    return p.description ? b.describe(p.description) : b;
  }

  // ref, union, unknown — fall through to passthrough
  // Consumer is responsible for wiring schema resolution via context
  return z.unknown();
}

/**
 * Build a validator map from a list of lexicons.
 * Returns `{ [lexId]: { input?, output? } }` where each slot
 * contains the Zod schema for that direction.
 *
 * @example
 * const lexicons = [...];
 * const validators = buildValidatorMap(lexicons);
 * const v = validators["com.etzhayyim.apps.openBanking.transfer"];
 * if (v.input) {
 *   const parsed = v.input.safeParse(userInput);
 * }
 */
export function buildValidatorMap(
  lexicons: LexiconDoc[]
): Record<string, { input?: ZodTypeAny; output?: ZodTypeAny }> {
  const out: Record<string, { input?: ZodTypeAny; output?: ZodTypeAny }> = {};

  for (const lex of lexicons) {
    const main = lex.defs.main;
    if (!main) continue;

    const slot: { input?: ZodTypeAny; output?: ZodTypeAny } = {};

    // Query: extract input parameters
    if (main.type === "query" && main.parameters) {
      slot.input = lexiconObjectToZod({
        type: "object",
        properties: main.parameters.properties,
        required: main.parameters.required,
      });
    }

    // Procedure: extract input/output schemas
    if (main.type === "procedure") {
      if (main.input?.schema && typeof main.input.schema === "object" && "type" in main.input.schema) {
        slot.input = lexiconObjectToZod(main.input.schema as LexiconObjectDef);
      }
      if (main.output?.schema && typeof main.output.schema === "object" && "type" in main.output.schema) {
        slot.output = lexiconObjectToZod(main.output.schema as LexiconObjectDef);
      }
    }

    out[lex.id] = slot;
  }

  return out;
}

/**
 * Validate input against a lexicon validator.
 * Returns `{ data: T }` on success, `{ error: ZodError }` on failure.
 *
 * @example
 * const v = validateInput(validators, "com.etzhayyim.apps.openBanking.transfer", userInput);
 * if ("error" in v) {
 *   console.error(v.error.issues);
 * } else {
 *   await transfer(v.data);
 * }
 */
export function validateInput<T = unknown>(
  validators: Record<string, { input?: ZodTypeAny }>,
  lexId: string,
  input: unknown
): { data: T } | { error: z.ZodError } {
  const v = validators[lexId];
  if (!v?.input) return { data: input as T };

  const result = v.input.safeParse(input);
  if (!result.success) {
    return { error: result.error };
  }

  return { data: result.data as T };
}

export type { LexiconDoc, LexiconProperty } from "./types.js";
