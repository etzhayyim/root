/**
 * @etzhayyim/lexicon-to-openapi — transform tests (coverage loop iteration 14).
 *
 * Converts AT Protocol Lexicon JSON → OpenAPI 3.0. Sibling of lexicon-to-zod
 * (iter 13); this side produces the public API spec, so a transform bug ships
 * a wrong contract to consumers. Zero tests before. Dependency-free pure
 * transform; isolated island keeps the root pnpm-lock untouched.
 */
import { describe, it, expect } from "vitest";
import { lexiconsToOpenApi } from "../src/index.ts";

const OPTS = { title: "Test API", version: "1.0.0", baseUrl: "https://x.etzhayyim.com" };

function gen(lexicons: unknown[]) {
  return lexiconsToOpenApi(lexicons as never, OPTS) as {
    openapi: string;
    info: { title: string; version: string };
    servers: { url: string }[];
    paths: Record<string, any>;
    components: { schemas: Record<string, any> };
  };
}

// ── top-level document shape ─────────────────────────────────────────────────

describe("document envelope", () => {
  it("emits openapi 3.0.3 + info + server from opts", () => {
    const doc = gen([]);
    expect(doc.openapi).toBe("3.0.3");
    expect(doc.info).toEqual({ title: "Test API", version: "1.0.0" });
    expect(doc.servers).toEqual([{ url: "https://x.etzhayyim.com" }]);
    expect(doc.paths).toEqual({});
  });

  it("skips a lexicon with no main def", () => {
    const doc = gen([{ id: "com.x.nomain", defs: {} }]);
    expect(doc.paths).toEqual({});
  });
});

// ── query → GET with query params ────────────────────────────────────────────

describe("query → GET", () => {
  const lex = {
    id: "com.example.getThing",
    defs: { main: {
      type: "query",
      description: "Get a thing",
      parameters: { type: "params", required: ["id"], properties: {
        id: { type: "string", description: "the id" },
        limit: { type: "integer", minimum: 1, maximum: 100 },
      } },
      output: { encoding: "application/json", schema: { type: "object", required: ["name"], properties: { name: { type: "string" } } } },
    } },
  };

  it("maps to /xrpc/<id> GET with in:query parameters + required flags", () => {
    const doc = gen([lex]);
    const op = doc.paths["/xrpc/com.example.getThing"].get;
    expect(op.summary).toBe("Get a thing");
    expect(op.operationId).toBe("com.example.getThing");
    const byName = Object.fromEntries(op.parameters.map((p: any) => [p.name, p]));
    expect(byName.id.in).toBe("query");
    expect(byName.id.required).toBe(true);
    expect(byName.limit.required).toBe(false);
    expect(byName.limit.schema).toMatchObject({ type: "integer", minimum: 1, maximum: 100 });
    // 200 response carries the output object schema under its encoding
    const ok = op.responses["200"].content["application/json"].schema;
    expect(ok).toMatchObject({ type: "object", required: ["name"] });
    expect(op.responses.default.description).toBe("Error");
  });

  it("a parameterless query yields an empty parameters array", () => {
    const doc = gen([{ id: "com.x.ping", defs: { main: { type: "query" } } }]);
    expect(doc.paths["/xrpc/com.x.ping"].get.parameters).toEqual([]);
  });
});

// ── procedure → POST with requestBody ────────────────────────────────────────

describe("procedure → POST", () => {
  const lex = {
    id: "com.example.doThing",
    defs: { main: {
      type: "procedure",
      input: { encoding: "application/json", schema: { type: "object", required: ["amount"], properties: { amount: { type: "integer" } } } },
      output: { encoding: "application/json", schema: { type: "object", properties: { ok: { type: "boolean" } } } },
    } },
  };

  it("maps to POST with a required requestBody under the input encoding", () => {
    const op = gen([lex]).paths["/xrpc/com.example.doThing"].post;
    expect(op.requestBody.required).toBe(true);
    const body = op.requestBody.content["application/json"].schema;
    expect(body).toMatchObject({ type: "object", required: ["amount"] });
    expect(op.responses["200"].content["application/json"].schema)
      .toMatchObject({ type: "object", properties: { ok: { type: "boolean" } } });
  });

  it("a procedure with no input omits requestBody", () => {
    const op = gen([{ id: "com.x.noinput", defs: { main: { type: "procedure" } } }]).paths["/xrpc/com.x.noinput"].post;
    expect(op.requestBody).toBeUndefined();
  });
});

// ── record → component schema (not an endpoint) ──────────────────────────────

describe("record → component schema", () => {
  it("registers under components.schemas with a sanitized name, no path", () => {
    const doc = gen([{
      id: "com.example.profile",
      defs: { main: { type: "record", record: { type: "object", required: ["did"], properties: { did: { type: "string" } } } } },
    }]);
    expect(doc.paths["/xrpc/com.example.profile"]).toBeUndefined();
    expect(doc.components.schemas["com_example_profile"]).toMatchObject({ type: "object", required: ["did"] });
  });
});

// ── property → schema (via a procedure input that exercises each branch) ─────

describe("property → OpenAPI schema branches", () => {
  function schemaFor(properties: Record<string, unknown>) {
    const doc = gen([{
      id: "com.x.p",
      defs: { main: { type: "procedure", input: { encoding: "application/json", schema: { type: "object", properties } } } },
    }]);
    return doc.paths["/xrpc/com.x.p"].post.requestBody.content["application/json"].schema.properties;
  }

  it("ref → $ref, union refs → oneOf", () => {
    const p = schemaFor({
      r: { type: "ref", ref: "com.x.other" },
      u: { type: "union", refs: ["com.x.a", "com.x.b"] },
    });
    expect(p.r).toEqual({ $ref: "#/components/schemas/com_x_other" });
    expect(p.u).toEqual({ oneOf: [
      { $ref: "#/components/schemas/com_x_a" },
      { $ref: "#/components/schemas/com_x_b" },
    ] });
  });

  it("array carries items + maxItems; nested object recurses", () => {
    const p = schemaFor({
      xs: { type: "array", items: { type: "string" }, maxLength: 5 },
      o: { type: "object", required: ["k"], properties: { k: { type: "boolean" } } },
    });
    expect(p.xs).toMatchObject({ type: "array", items: { type: "string" }, maxItems: 5 });
    expect(p.o).toMatchObject({ type: "object", required: ["k"] });
  });

  it("string carries format/enum/knownValues/pattern/length constraints", () => {
    const p = schemaFor({
      s: { type: "string", format: "uri", maxLength: 10, minLength: 2, pattern: "^a" },
      e: { type: "string", enum: ["a", "b"] },
      k: { type: "string", knownValues: ["x", "y"] },
      n: { type: "integer", minimum: 0, maximum: 9, default: 1 },
    });
    expect(p.s).toMatchObject({ type: "string", format: "uri", maxLength: 10, minLength: 2, pattern: "^a" });
    expect(p.e.enum).toEqual(["a", "b"]);
    expect(p.k["x-knownValues"]).toEqual(["x", "y"]);
    expect(p.n).toMatchObject({ type: "integer", minimum: 0, maximum: 9, default: 1 });
  });

  it("unknown / untyped property → empty schema", () => {
    const p = schemaFor({ a: { type: "unknown" }, b: {} });
    expect(p.a).toEqual({});
    expect(p.b).toEqual({});
  });
});
