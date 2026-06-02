#!/usr/bin/env node

/**
 * lexicon-codegen.test.mjs — Integration + schema + regression tests for Lexicon → service-generated.ts
 *
 * Tests:
 * 1. Schema completeness: all 84 Lexicons have typed properties (no empty schemas)
 * 2. AT Protocol Lexicon format compliance
 * 3. Codegen integration: Lexicon → service-generated.ts roundtrip
 * 4. Regression: generated output matches expected structure
 * 5. NSID consistency: Lexicon id matches file path
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const LEXICON_DIR = path.join(ROOT, "00-contracts/lexicons");
const SERVICE_FILE = path.join(ROOT, "10-protocol/wproto/src/service-generated.ts");
const GENERATOR = path.join(ROOT, "70-tools/scripts/contract/gen-service-from-lexicon.mjs");

let passed = 0;
let failed = 0;
const failures = [];

function assert(condition, message) {
  if (condition) {
    passed++;
  } else {
    failed++;
    failures.push(message);
  }
}

function collectLexicons(dir) {
  const results = [];
  function walk(d) {
    for (const entry of readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".json")) {
        try {
          const json = JSON.parse(readFileSync(full, "utf8"));
          if (json.lexicon === 1) results.push({ path: full, rel: path.relative(LEXICON_DIR, full), ...json });
        } catch { /* skip */ }
      }
    }
  }
  walk(dir);
  return results;
}

// ── Test 1: Schema Completeness ──

function testSchemaCompleteness(lexicons) {
  console.log("\n── Test 1: Schema Completeness ──");

  // Only check query/procedure (not record/subscription which have different structure)
  const xrpcLexicons = lexicons.filter((l) => {
    const mainType = l.defs?.main?.type;
    return mainType === "query" || mainType === "procedure";
  });
  let untypedCount = 0;
  for (const lex of xrpcLexicons) {
    const main = lex.defs?.main;
    const hasTypedParams =
      (main.type === "query" && main.parameters?.properties && Object.keys(main.parameters.properties).length > 0) ||
      (main.type === "procedure" && main.input?.schema?.properties && Object.keys(main.input.schema.properties).length > 0);
    const hasTypedResponse =
      main.output?.schema?.properties && Object.keys(main.output.schema.properties).length > 0;

    if (!hasTypedParams && !hasTypedResponse) {
      untypedCount++;
    }
  }

  assert(untypedCount === 0, `${untypedCount} XRPC Lexicon(s) have no typed properties (params or response)`);
  console.log(`  completeness: ${xrpcLexicons.length - untypedCount}/${xrpcLexicons.length} XRPC typed`);
}

// ── Test 2: AT Protocol Lexicon Format Compliance ──

function testLexiconFormat(lexicons) {
  console.log("\n── Test 2: AT Protocol Lexicon Format ──");

  const PRIMARY_TYPES = new Set(["query", "procedure", "subscription", "record", "permission-set"]);
  const ALLOWED_TYPES = new Set([
    ...PRIMARY_TYPES,
    "boolean", "integer", "string", "bytes", "cid-link", "blob",
    "array", "object",
    "params", "permission",
    "token", "ref", "union", "unknown",
    "number", // extended for TS compat
  ]);

  for (const lex of lexicons) {
    const main = lex.defs?.main;

    // lexicon version
    assert(lex.lexicon === 1, `${lex.id}: lexicon must be 1`);

    // id exists
    assert(typeof lex.id === "string" && lex.id.length > 0, `${lex.rel}: missing id`);

    // main type
    const mainType = lex.defs?.main?.type;
    assert(PRIMARY_TYPES.has(mainType), `${lex.id}: defs.main.type="${mainType}" not in primary types`);

    // query must have parameters with type "params"
    if (mainType === "query") {
      assert(
        main?.parameters?.type === "params",
        `${lex.id}: query must have parameters.type="params"`
      );
      assert(main?.output != null, `${lex.id}: query must have output`);
    }

    // procedure must have input and output
    if (mainType === "procedure") {
      assert(main?.input != null, `${lex.id}: procedure must have input`);
      assert(main?.output != null, `${lex.id}: procedure must have output`);
      if (main?.input) {
        assert(
          main.input.encoding === "application/json",
          `${lex.id}: input.encoding must be "application/json"`
        );
      }
    }

    // output encoding
    if (main?.output) {
      assert(
        main.output.encoding === "application/json",
        `${lex.id}: output.encoding must be "application/json"`
      );
    }

    // type validation: walk all type nodes
    const typeErrors = validateTypes(lex.defs, ALLOWED_TYPES);
    assert(typeErrors.length === 0, `${lex.id}: disallowed types: ${typeErrors.join(", ")}`);

    // required array consistency
    validateRequired(lex);
  }
}

function validateTypes(obj, allowed, path = "$", errors = []) {
  if (!obj || typeof obj !== "object") return errors;
  if (Array.isArray(obj)) {
    obj.forEach((v, i) => validateTypes(v, allowed, `${path}[${i}]`, errors));
    return errors;
  }
  if (typeof obj.type === "string" && !allowed.has(obj.type)) {
    errors.push(`${obj.type} at ${path}`);
  }
  for (const [k, v] of Object.entries(obj)) {
    validateTypes(v, allowed, `${path}.${k}`, errors);
  }
  return errors;
}

function validateRequired(lex) {
  const schemas = [];
  if (lex.defs?.main?.parameters) schemas.push({ schema: lex.defs.main.parameters, loc: "parameters" });
  if (lex.defs?.main?.input?.schema) schemas.push({ schema: lex.defs.main.input.schema, loc: "input.schema" });
  if (lex.defs?.main?.output?.schema) schemas.push({ schema: lex.defs.main.output.schema, loc: "output.schema" });

  for (const { schema, loc } of schemas) {
    if (schema.required && Array.isArray(schema.required)) {
      const props = schema.properties ? Object.keys(schema.properties) : [];
      for (const req of schema.required) {
        assert(
          props.includes(req),
          `${lex.id}: required field "${req}" in ${loc} not in properties`
        );
      }
    }
  }
}

// ── Test 3: NSID ↔ File Path Consistency ──

function testNsidPathConsistency(lexicons) {
  console.log("\n── Test 3: NSID ↔ File Path Consistency ──");

  for (const lex of lexicons) {
    const parts = lex.id.split(".");
    const expectedPath = parts.join("/") + ".json";
    const actualPath = lex.rel.replace(/\\/g, "/");
    assert(actualPath === expectedPath, `${lex.id}: path mismatch — expected ${expectedPath}, got ${actualPath}`);
  }
}

// ── Test 4: Codegen Integration ──

function testCodegenIntegration(lexicons) {
  console.log("\n── Test 4: Codegen Integration ──");

  // Run generator in dry-run mode
  let output;
  try {
    output = execFileSync("node", [GENERATOR, "--dry-run"], {
      cwd: ROOT,
      encoding: "utf8",
      timeout: 30000,
    });
  } catch (error) {
    assert(false, `Codegen failed: ${error.message}`);
    return;
  }

  assert(output.includes("service-generated.ts"), "Output contains header");
  assert(output.includes("defineService"), "Output contains defineService");
  assert(output.includes("defineQuery"), "Output contains defineQuery");
  assert(output.includes("defineProcedure"), "Output contains defineProcedure");
  assert(output.includes("createServiceProxy"), "Output contains createServiceProxy");

  // Check all NSIDs appear in output
  const xrpcLexicons = lexicons.filter((l) => {
    const mainType = l.defs?.main?.type;
    return mainType === "query" || mainType === "procedure";
  });
  for (const lex of xrpcLexicons) {
    assert(output.includes(`nsid: '${lex.id}'`), `${lex.id}: NSID missing from generated output`);
  }

  // Check no `{ params: string }, string>` patterns remain (all should be typed)
  const untypedMatches = output.match(/defineQuery<\{ params: string \}, string>/g) || [];
  const untypedProcMatches = output.match(/defineProcedure<\{ params: string \}, string>/g) || [];
  const totalUntyped = untypedMatches.length + untypedProcMatches.length;

  console.log(`  untyped fallback methods: ${totalUntyped}`);
  assert(totalUntyped === 0, `${totalUntyped} methods still using untyped { params: string } fallback`);
}

// ── Test 5: Regression — Structure Check ──

function testRegressionStructure() {
  console.log("\n── Test 5: Regression Structure ──");

  if (!existsSync(SERVICE_FILE)) {
    assert(false, "service-generated.ts does not exist");
    return;
  }

  const content = readFileSync(SERVICE_FILE, "utf8");

  // Header
  assert(content.startsWith("// service-generated.ts"), "Header starts with service-generated.ts");
  assert(content.includes("Lexicon JSON"), "Header references Lexicon JSON as SSoT");
  assert(!content.includes("WIT is the Single Source of Truth"), "No longer references WIT as SSoT");

  // Imports
  assert(content.includes("import { atQuery, atProcedure }"), "Imports atQuery/atProcedure");
  assert(!content.includes("from '@etzhayyim/xrpc'"), "No longer imports from @etzhayyim/xrpc");

  // Structure
  assert(!content.includes("generatedTransport"), "No generatedTransport wrapper");
  assert(!content.includes("generatedService"), "No generatedService registry");
  assert(!content.includes("generatedClient"), "No generatedClient proxy");
  assert(content.includes("return atQuery<") || content.includes("return atProcedure<"), "Calls atQuery/atProcedure directly");

  // Namespace sections
  const expectedNamespaces = [
    "com.etzhayyim.consent",
    "com.etzhayyim.convo",
    "com.etzhayyim.governance",
    "com.etzhayyim.kagami",
    "com.etzhayyim.projector",
    "com.etzhayyim.rtc",
    "com.etzhayyim.signal",
  ];
  for (const ns of expectedNamespaces) {
    assert(content.includes(`── ${ns} ──`), `Has namespace section: ${ns}`);
  }

  // Export functions exist
  assert(content.includes("export async function"), "Has exported async functions");

  // Typed methods (spot check)
  assert(
    content.includes("convoId: string") || content.includes("convoId: string;"),
    "Has typed convoId param"
  );
  assert(content.includes("rkey: string"), "Has typed rkey response");
}

// ── Test 6: Count Check ──

function testCountCheck(lexicons) {
  console.log("\n── Test 6: Count Check ──");

  const queries = lexicons.filter((l) => l.defs?.main?.type === "query");
  const procedures = lexicons.filter((l) => l.defs?.main?.type === "procedure");

  assert(lexicons.length >= 84, `Expected >= 84 lexicons, got ${lexicons.length}`);
  assert(queries.length > 0, `Has query lexicons (got ${queries.length})`);
  assert(procedures.length > 0, `Has procedure lexicons (got ${procedures.length})`);

  console.log(`  total: ${lexicons.length} (${queries.length} query, ${procedures.length} procedure)`);
}

// ── Main ──

console.log("lexicon-codegen integration test");
console.log("================================");

const lexicons = collectLexicons(LEXICON_DIR);
assert(lexicons.length > 0, "Found lexicon files");

testSchemaCompleteness(lexicons);
testLexiconFormat(lexicons);
testNsidPathConsistency(lexicons);
testCodegenIntegration(lexicons);
testRegressionStructure();
testCountCheck(lexicons);

console.log("\n================================");
console.log(`Results: ${passed} passed, ${failed} failed`);

if (failures.length > 0) {
  console.log("\nFailures:");
  for (const f of failures) {
    console.log(`  FAIL: ${f}`);
  }
  process.exit(1);
}

console.log("\nAll tests passed.");
