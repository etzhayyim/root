/**
 * @etzhayyim/lexicon-to-zod — transform tests (coverage loop iteration 13).
 *
 * lexicon-to-zod converts AT Protocol Lexicon JSON into Zod validators used by
 * XRPC handlers for runtime input/output validation. A transform bug here
 * silently weakens validation on every generated handler. Zero tests before
 * this. Isolated island (zod only; outside the pnpm workspace glob → root
 * pnpm-lock untouched).
 */
import { describe, it, expect } from "vitest";
import {
  lexiconObjectToZod,
  buildValidatorMap,
  validateInput,
} from "../src/index.ts";

const ok = (schema: { safeParse: (v: unknown) => { success: boolean } }, v: unknown) =>
  schema.safeParse(v).success;

// ── lexiconObjectToZod: primitives + required/optional ───────────────────────

describe("lexiconObjectToZod required vs optional", () => {
  const obj = {
    type: "object",
    required: ["name"],
    properties: {
      name: { type: "string" },
      age: { type: "integer" },
    },
  };
  it("enforces required and allows optional to be absent", () => {
    const s = lexiconObjectToZod(obj as never);
    expect(ok(s, { name: "a" })).toBe(true);            // optional age omitted
    expect(ok(s, { name: "a", age: 5 })).toBe(true);
    expect(ok(s, { age: 5 })).toBe(false);              // missing required name
  });
});

describe("string constraints + formats", () => {
  it("applies minLength/maxLength", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["h"],
      properties: { h: { type: "string", minLength: 2, maxLength: 4 } },
    } as never);
    expect(ok(s, { h: "ab" })).toBe(true);
    expect(ok(s, { h: "a" })).toBe(false);
    expect(ok(s, { h: "abcde" })).toBe(false);
  });

  it("uri format requires a URL; datetime format requires ISO", () => {
    const u = lexiconObjectToZod({
      type: "object", required: ["u"], properties: { u: { type: "string", format: "uri" } },
    } as never);
    expect(ok(u, { u: "https://x.test" })).toBe(true);
    expect(ok(u, { u: "not a url" })).toBe(false);
    const d = lexiconObjectToZod({
      type: "object", required: ["t"], properties: { t: { type: "string", format: "datetime" } },
    } as never);
    expect(ok(d, { t: "2026-06-12T00:00:00Z" })).toBe(true);
    expect(ok(d, { t: "yesterday" })).toBe(false);
  });

  it("enum and knownValues become a closed string enum", () => {
    const e = lexiconObjectToZod({
      type: "object", required: ["c"], properties: { c: { type: "string", enum: ["a", "b"] } },
    } as never);
    expect(ok(e, { c: "a" })).toBe(true);
    expect(ok(e, { c: "z" })).toBe(false);
    const k = lexiconObjectToZod({
      type: "object", required: ["c"], properties: { c: { type: "string", knownValues: ["x", "y"] } },
    } as never);
    expect(ok(k, { c: "x" })).toBe(true);
    expect(ok(k, { c: "z" })).toBe(false);
  });
});

describe("integer / boolean / array / object / bytes", () => {
  it("integer min/max + int-only", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["n"], properties: { n: { type: "integer", minimum: 0, maximum: 10 } },
    } as never);
    expect(ok(s, { n: 5 })).toBe(true);
    expect(ok(s, { n: -1 })).toBe(false);
    expect(ok(s, { n: 11 })).toBe(false);
    expect(ok(s, { n: 1.5 })).toBe(false);
  });

  it("array items + length bounds", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["xs"],
      properties: { xs: { type: "array", items: { type: "string" }, minLength: 1, maxLength: 2 } },
    } as never);
    expect(ok(s, { xs: ["a"] })).toBe(true);
    expect(ok(s, { xs: [] })).toBe(false);
    expect(ok(s, { xs: ["a", "b", "c"] })).toBe(false);
    expect(ok(s, { xs: [1] })).toBe(false);              // item type
  });

  it("nested object validates recursively", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["inner"],
      properties: {
        inner: { type: "object", required: ["k"], properties: { k: { type: "boolean" } } },
      },
    } as never);
    expect(ok(s, { inner: { k: true } })).toBe(true);
    expect(ok(s, { inner: {} })).toBe(false);
    expect(ok(s, { inner: { k: "no" } })).toBe(false);
  });

  it("bytes accepts a Uint8Array only", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["b"], properties: { b: { type: "bytes" } },
    } as never);
    expect(ok(s, { b: new Uint8Array([1, 2]) })).toBe(true);
    expect(ok(s, { b: [1, 2] })).toBe(false);
  });

  it("ref / unknown types fall through to passthrough (z.unknown)", () => {
    const s = lexiconObjectToZod({
      type: "object", required: ["r"], properties: { r: { type: "ref", ref: "#other" } },
    } as never);
    // unknown accepts anything (consumer wires ref resolution)
    expect(ok(s, { r: { anything: 1 } })).toBe(true);
    expect(ok(s, { r: "string-too" })).toBe(true);
  });
});

// ── buildValidatorMap: query + procedure ─────────────────────────────────────

describe("buildValidatorMap", () => {
  const lexicons = [
    {
      id: "com.example.getThing",
      defs: { main: { type: "query", parameters: { type: "params", required: ["id"], properties: { id: { type: "string" } } } } },
    },
    {
      id: "com.example.doThing",
      defs: { main: {
        type: "procedure",
        input: { schema: { type: "object", required: ["amount"], properties: { amount: { type: "integer", minimum: 1 } } } },
        output: { schema: { type: "object", required: ["ok"], properties: { ok: { type: "boolean" } } } },
      } },
    },
    { id: "com.example.record", defs: { main: { type: "record" } } }, // no input/output
  ];

  it("extracts query input parameters and procedure input/output", () => {
    const v = buildValidatorMap(lexicons as never);
    expect(ok(v["com.example.getThing"].input!, { id: "x" })).toBe(true);
    expect(ok(v["com.example.getThing"].input!, {})).toBe(false);
    expect(ok(v["com.example.doThing"].input!, { amount: 5 })).toBe(true);
    expect(ok(v["com.example.doThing"].input!, { amount: 0 })).toBe(false);
    expect(ok(v["com.example.doThing"].output!, { ok: true })).toBe(true);
  });

  it("a record (no input/output) yields an empty slot", () => {
    const v = buildValidatorMap(lexicons as never);
    expect(v["com.example.record"]).toEqual({});
  });
});

// ── validateInput ────────────────────────────────────────────────────────────

describe("validateInput", () => {
  const validators = buildValidatorMap([
    { id: "com.example.doThing", defs: { main: {
      type: "procedure",
      input: { schema: { type: "object", required: ["amount"], properties: { amount: { type: "integer", minimum: 1 } } } },
    } } },
  ] as never);

  it("returns data on success, error on failure", () => {
    const good = validateInput(validators, "com.example.doThing", { amount: 3 });
    expect("data" in good && (good.data as { amount: number }).amount).toBe(3);
    const bad = validateInput(validators, "com.example.doThing", { amount: 0 });
    expect("error" in bad).toBe(true);
  });

  it("passes the input through unchanged when no validator exists for the lexId", () => {
    const r = validateInput(validators, "com.example.unknown", { whatever: 1 });
    expect("data" in r && (r.data as { whatever: number }).whatever).toBe(1);
  });
});
