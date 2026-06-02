#!/usr/bin/env node

/**
 * infer-lexicon-schemas.mjs — F-Plan F2 lexicon expansion (2026-04-13)
 *
 * For each stub lexicon (marked `"x-bootstrap": true`), scan the app handler body
 * where it's registered and infer an input schema from:
 *   - decodeJson(body, { foo: "", bar: 0 }) fallback literal shapes
 *   - str(args.foo) / num(args.bar) / Array.isArray(args.items) / Boolean(args.active) patterns
 *   - (args.X as string[]) / String(args.X) coercions
 *
 * Updates the lexicon's main.input.schema (or main.parameters for query) with the
 * inferred properties. Never overwrites hand-authored lexicons (only touches those
 * with `x-bootstrap: true`).
 *
 * Modes:
 *   --dry-run : print what would be updated, don't write
 *   --apply   : write updated lexicon files
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";

const ROOT = process.cwd();
const args = process.argv.slice(2);
const isDryRun = args.includes("--dry-run");
const isApply = args.includes("--apply");
// --refine: apply D3 heuristics to ALREADY-populated stubs (tighten string → number/bool/array/object)
const isRefine = args.includes("--refine");

if (!isDryRun && !isApply) {
  console.error("usage: infer-lexicon-schemas.mjs [--dry-run | --apply] [--refine]");
  process.exit(1);
}

// List all app.ts files under 60-apps
function listAppFiles() {
  const out = execFileSync(
    "rg",
    ["-l", "-U", String.raw`\.(?:command|query|lexiconCommand|lexiconQuery)\(\s*nsid\(`, "-g", "app.ts", "60-apps/"],
    { cwd: ROOT, encoding: "utf8", maxBuffer: 20 * 1024 * 1024 },
  ).trim();
  return out ? out.split("\n").sort() : [];
}

// Resolve a named function body by grep-style lookup in the source. Supports:
//   - `async function cmdFoo(sdk: HostSDK, body: Uint8Array): Promise<unknown> { ... }`
//   - `function cmdFoo(sdk, body) { ... }`
//   - `const cmdFoo = async (sdk, body) => { ... }`
function findNamedFunctionBody(src, name) {
  const patterns = [
    new RegExp(`async\\s+function\\s+${name}\\s*\\([^)]*\\)\\s*(?::[^{]+)?\\{`, "g"),
    new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*(?::[^{]+)?\\{`, "g"),
    new RegExp(`const\\s+${name}\\s*=\\s*async\\s*\\([^)]*\\)\\s*(?::[^{]+)?=>\\s*\\{`, "g"),
    new RegExp(`const\\s+${name}\\s*=\\s*\\([^)]*\\)\\s*(?::[^{]+)?=>\\s*\\{`, "g"),
  ];
  for (const re of patterns) {
    const m = re.exec(src);
    if (!m) continue;
    const bodyStart = re.lastIndex;
    let depth = 1;
    let i = bodyStart;
    while (i < src.length && depth > 0) {
      const c = src[i];
      if (c === "{") depth++;
      else if (c === "}") depth--;
      i++;
    }
    return src.slice(bodyStart, i - 1);
  }
  return null;
}

// Find `.command(nsid("NSID"), handler, ...)` or `.lexiconCommand(nsid("NSID"), handler, ...)` blocks.
// Extract { nsid, handlerBody } where handlerBody is the source text between the opening `{` and its matching `}`.
// Supports both inline `async (ctx, body) => { ... }` and indirect `(ctx, body) => cmdFoo(sdk, body)`.
function extractCommands(src) {
  const results = [];
  const re = /\.(?:lexiconCommand|lexiconQuery|command|query)\(\s*nsid\(\s*"(ai\.[a-zA-Z0-9._-]+)"\s*\)\s*,\s*(async\s*)?\(([^)]*)\)\s*=>\s*(\{|(\w+)\()/g;
  let m;
  while ((m = re.exec(src)) !== null) {
    const nsid = m[1];
    const params = m[3].split(",").map((p) => p.trim().split(/[:=\s]/)[0]).filter(Boolean);
    const bodyParamName = params[1] || params[0] || "body";

    if (m[4] === "{") {
      // Inline body — capture until matching brace using a naive brace counter.
      const bodyStart = re.lastIndex;
      let depth = 1;
      let i = bodyStart;
      while (i < src.length && depth > 0) {
        const c = src[i];
        if (c === "{") depth++;
        else if (c === "}") depth--;
        else if (c === "/" && src[i + 1] === "/") {
          while (i < src.length && src[i] !== "\n") i++;
        } else if (c === "/" && src[i + 1] === "*") {
          i += 2;
          while (i < src.length - 1 && !(src[i] === "*" && src[i + 1] === "/")) i++;
          i += 2;
          continue;
        } else if (c === '"' || c === "'" || c === "`") {
          const quote = c;
          i++;
          while (i < src.length) {
            if (src[i] === "\\") { i += 2; continue; }
            if (src[i] === quote) break;
            if (quote === "`" && src[i] === "$" && src[i + 1] === "{") {
              let d = 1;
              i += 2;
              while (i < src.length && d > 0) {
                if (src[i] === "{") d++;
                else if (src[i] === "}") d--;
                if (d > 0) i++;
              }
            }
            i++;
          }
        }
        i++;
      }
      const handlerBody = src.slice(bodyStart, i - 1);
      results.push({ nsid, bodyParamName, handlerBody });
    } else if (m[5]) {
      // Indirect handler: (ctx, body) => cmdFoo(sdk, body)
      const fnName = m[5];
      const resolvedBody = findNamedFunctionBody(src, fnName);
      if (resolvedBody) {
        // Inside the named fn, the body parameter is usually called `body`.
        results.push({ nsid, bodyParamName: "body", handlerBody: resolvedBody });
      }
    }
  }
  return results;
}

// Extract properties from a TS/JS object literal string. Handles nested braces/arrays
// by skipping their content. Returns a Map of key → guessed primitive type.
function parseLiteralProps(literal) {
  /** @type {Record<string, string>} */
  const out = {};
  // Strip outer braces
  const body = literal.replace(/^\s*\{/, "").replace(/\}\s*$/, "");
  let depth = 0;
  let cur = "";
  const entries = [];
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (c === "{" || c === "[" || c === "(") depth++;
    else if (c === "}" || c === "]" || c === ")") depth--;
    if (c === "," && depth === 0) {
      entries.push(cur);
      cur = "";
      continue;
    }
    cur += c;
  }
  if (cur.trim()) entries.push(cur);

  for (const entry of entries) {
    const colon = entry.indexOf(":");
    if (colon < 0) {
      // Shorthand { foo } — type unknown
      const m = entry.trim().match(/^['"]?(\w+)['"]?$/);
      if (m && !out[m[1]]) out[m[1]] = "string";
      continue;
    }
    const key = entry.slice(0, colon).trim().replace(/^['"]/, "").replace(/['"]$/, "");
    const val = entry.slice(colon + 1).trim();
    if (!/^\w+$/.test(key)) continue;
    if (out[key]) continue;
    if (/^""$|^''$|^String\(|^`/.test(val)) out[key] = "string";
    else if (/^\d+\.\d+$/.test(val)) out[key] = "number";
    else if (/^\d+$/.test(val)) out[key] = "integer";
    else if (/^(true|false)$/.test(val)) out[key] = "boolean";
    else if (/^\[/.test(val)) out[key] = "array";
    else if (/^\{/.test(val)) out[key] = "object";
    else if (/\.toString\(\)$/.test(val) || /^str\(/.test(val)) out[key] = "string";
    else if (/^Number\(|^num\(|^Math\./.test(val)) out[key] = "number";
    else if (/^Boolean\(|===|!==/.test(val)) out[key] = "boolean";
    else if (/^JSON\.stringify/.test(val)) out[key] = "string";
    else out[key] = "unknown";
  }
  return out;
}

// Find matching closing brace starting AT position of `{` (inclusive). Returns end index.
function findClosingBrace(src, openIdx) {
  let depth = 0;
  for (let i = openIdx; i < src.length; i++) {
    const c = src[i];
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return i;
    } else if (c === '"' || c === "'" || c === "`") {
      const quote = c;
      i++;
      while (i < src.length) {
        if (src[i] === "\\") { i += 2; continue; }
        if (src[i] === quote) break;
        i++;
      }
    }
  }
  return -1;
}

// Given a handler body, infer input/output schemas + required fields.
function inferSchemaFromHandler(bodyParamName, handlerBody) {
  /** @type {Record<string, string>} */
  const inputProps = {};
  /** @type {Set<string>} */
  const required = new Set();
  /** @type {Record<string, string>} */
  const outputProps = {};

  // ── 1. Find decodeJson(body, { literal }) OR parseLexiconInput(nsid, body) ──
  // Matches:
  //   `const args = decodeJson<{foo: string}>(body, { ... })`
  //   `const { foo, bar } = decodeJson(body, { ... })`
  //   `const args = decodeJson(body, {})`
  //   `const args = parseLexiconInput("com.etzhayyim.apps.foo.bar", body)`
  //   `const { foo, bar } = parseLexiconInput("com.etzhayyim.apps.foo.bar", body)`
  const decodeRe = /(?:const|let|var)\s+(\w+|\{[^}]+\})\s*=\s*decodeJson(?:<([^>]+)>)?\(\s*(\w+)\s*,\s*(\{[^{}]*\}|\{[\s\S]*?\n\s*\})/g;
  // New-form regex: parseLexiconInput("nsid", body)
  const parseRe = /(?:const|let|var)\s+(\w+|\{[^}]+\})\s*=\s*parseLexiconInput\(\s*(?:"[^"]+"|'[^']+')\s*,\s*(\w+)\s*\)/g;
  /** @type {Set<string>} */
  const argNames = new Set();
  let dm;
  while ((dm = decodeRe.exec(handlerBody)) !== null) {
    const lhs = dm[1];
    const generic = dm[2];
    const bodyRef = dm[3];
    const literal = dm[4];
    if (bodyRef !== bodyParamName) continue;

    // (a) Destructured LHS: `const { name, age } = decodeJson(...)`
    if (lhs.startsWith("{")) {
      const destrMatch = lhs.match(/\{([^}]+)\}/);
      if (destrMatch) {
        for (const part of destrMatch[1].split(",")) {
          const key = part.trim().split(/[:=\s]/)[0];
          if (key && /^\w+$/.test(key) && !inputProps[key]) inputProps[key] = "string";
        }
      }
    } else {
      argNames.add(lhs);
    }

    // (b) Generic type: decodeJson<{foo: string; bar: number}>(body, ...)
    if (generic && generic.includes("{")) {
      const genProps = parseTsTypeLiteral(generic);
      for (const [k, t] of Object.entries(genProps)) {
        if (!inputProps[k]) inputProps[k] = t;
      }
    }

    // (c) Fallback literal shape
    const litProps = parseLiteralProps(literal);
    for (const [k, t] of Object.entries(litProps)) {
      if (!inputProps[k]) inputProps[k] = t;
    }
  }

  // ── 1b. Also match parseLexiconInput(nsid, body) — the F-Plan F2 typed form ──
  let pm;
  while ((pm = parseRe.exec(handlerBody)) !== null) {
    const lhs = pm[1];
    const bodyRef = pm[2];
    if (bodyRef !== bodyParamName) continue;

    if (lhs.startsWith("{")) {
      // Destructured form: const { foo, bar } = parseLexiconInput(...)
      const destrMatch = lhs.match(/\{([^}]+)\}/);
      if (destrMatch) {
        for (const part of destrMatch[1].split(",")) {
          const key = part.trim().split(/[:=\s]/)[0];
          if (key && /^\w+$/.test(key) && !inputProps[key]) inputProps[key] = "string";
        }
      }
    } else {
      argNames.add(lhs);
    }
  }

  // ── 2. Scan args.X accesses for property inference ──
  const candidateArgNames = argNames.size > 0 ? [...argNames] : ["args", "input", "params", "req"];
  for (const argName of candidateArgNames) {
    // str(argName.prop) / str(argName?.prop ?? ...)
    const strRe = new RegExp(`str\\(\\s*${argName}\\??\\.(\\w+)`, "g");
    let mm;
    while ((mm = strRe.exec(handlerBody)) !== null) {
      const key = mm[1];
      if (!inputProps[key]) inputProps[key] = "string";
    }
    const numRe = new RegExp(`(?:num|Number)\\(\\s*${argName}\\??\\.(\\w+)`, "g");
    while ((mm = numRe.exec(handlerBody)) !== null) {
      const key = mm[1];
      if (!inputProps[key] || inputProps[key] === "unknown") inputProps[key] = "number";
    }
    const boolRe = new RegExp(`Boolean\\(\\s*${argName}\\??\\.(\\w+)`, "g");
    while ((mm = boolRe.exec(handlerBody)) !== null) {
      const key = mm[1];
      if (!inputProps[key] || inputProps[key] === "unknown") inputProps[key] = "boolean";
    }
    const arrRe = new RegExp(`Array\\.isArray\\(\\s*${argName}\\??\\.(\\w+)|${argName}\\??\\.(\\w+)\\s+as\\s+\\w+\\[\\]`, "g");
    while ((mm = arrRe.exec(handlerBody)) !== null) {
      const key = mm[1] || mm[2];
      if (!key) continue;
      if (!inputProps[key] || inputProps[key] === "unknown") inputProps[key] = "array";
    }

    // ── 3. Required detection: early-return guards ──
    // Patterns:
    //   if (!args.foo) return { error: "..." };
    //   if (!args.foo || !args.bar) return { error: "foo required" };
    //   if (args.foo == null) return ...
    const guardRe = new RegExp(`if\\s*\\(\\s*!\\s*${argName}\\??\\.(\\w+)`, "g");
    while ((mm = guardRe.exec(handlerBody)) !== null) {
      required.add(mm[1]);
    }
    // if (!X || !Y) pattern — capture both
    const guardRe2 = new RegExp(`\\|\\|\\s*!\\s*${argName}\\??\\.(\\w+)`, "g");
    while ((mm = guardRe2.exec(handlerBody)) !== null) {
      required.add(mm[1]);
    }
    // Also: `const foo = str(args.foo); if (!foo || !bar) ...`
    // Track local vars bound to args properties (via str/num/Number/Boolean wrappers).
    const localVarRe = new RegExp(`(?:const|let)\\s+(\\w+)\\s*=\\s*(?:str|num|Number|Boolean)\\(\\s*${argName}\\??\\.(\\w+)`, "g");
    const localToProp = new Map();
    while ((mm = localVarRe.exec(handlerBody)) !== null) {
      localToProp.set(mm[1], mm[2]);
    }
    // Scan every `if (...)` condition for `!\s*\w+` negations (multi-condition aware).
    const ifCondRe = /if\s*\(([^)]*)\)/g;
    while ((mm = ifCondRe.exec(handlerBody)) !== null) {
      const cond = mm[1];
      const negRe = /!\s*(\w+)/g;
      let nm;
      while ((nm = negRe.exec(cond)) !== null) {
        const prop = localToProp.get(nm[1]);
        if (prop) required.add(prop);
        // Direct argName.prop negation: `!args.foo`
        const directRe = new RegExp(`!\\s*${argName}\\??\\.(\\w+)`, "g");
        let dm2;
        while ((dm2 = directRe.exec(cond)) !== null) {
          required.add(dm2[1]);
        }
      }
    }
  }

  // ── 4. Output inference: return statements with object literals ──
  // Matches: `return { ok: true, id: foo };`
  // Scan sequentially; skip early-return error guards (return { error: "..." }) from primary output.
  const retRe = /return\s*(\{[\s\S]*?\n\s*\})\s*;/g;
  let rm;
  while ((rm = retRe.exec(handlerBody)) !== null) {
    const lit = rm[1];
    // Skip nested calls
    const props = parseLiteralProps(lit);
    for (const [k, t] of Object.entries(props)) {
      // Error guards — keep error as optional output property
      if (!outputProps[k]) outputProps[k] = t;
    }
  }
  // Also one-line: `return { ok: true };`
  const retSimpleRe = /return\s+(\{[^{}]*\})\s*;?/g;
  while ((rm = retSimpleRe.exec(handlerBody)) !== null) {
    const lit = rm[1];
    const props = parseLiteralProps(lit);
    for (const [k, t] of Object.entries(props)) {
      if (!outputProps[k]) outputProps[k] = t;
    }
  }

  // ── D3: post-pass heuristic refinement (2026-04-13) ──
  // Tighten string-typed properties using name-suffix + handler-evidence heuristics.
  applyD3Heuristics(inputProps, outputProps, candidateArgNames, handlerBody);

  return { inputProps, required: [...required], outputProps };
}

// ── D3 heuristics (2026-04-13) ──
// Post-pass refinement: tighten `string` properties to number/integer/boolean/array/object
// based on property name suffixes + handler code evidence. Applied after the primary pass.

/** Name-suffix heuristics for type promotion. Case-insensitive matching. */
const NUMERIC_SUFFIXES = /(score|rate|years?|number|count|percentage|height|width|amount|duration|lat|lng|lon|longitude|latitude|threshold|ppm|perminute|size|bytes|level|rank|price|qty|quantity|depth|radius|degree|ratio|delta|elapsed|ms|seconds|minutes|hours|days|weeks|months|total|avg|sum|min|max)$/i;
const INTEGER_SUFFIXES = /(count|number|year|age|offset|limit|index|page|id|floornumber|total|age|rank|level|qty|quantity)$/i;
const BOOLEAN_PREFIXES = /^(is|has|can|should|skip|force|use|enable|allow|auto|do|will|was|were|include|hide|show)[_A-Z0-9]/;
const BOOLEAN_NAMES = /^(confirm|enabled|active|visible|disabled|dry|dryrun|debug|verbose|silent|strict|valid|ok|locked|pinned|sticky|flag|public|private|anonymous)$/i;
const ARRAY_PLURALS = /(ids|dids|urls|uris|tags|photos|files|keys|values|names|items|rows|fields|docs|aliases|actors|profiles|certifications|roles|scopes|permissions|candidates|sources|targets|codes|labels|records|options|choices|results|outputs|inputs|hashtags|mentions|ttps|accounts|members|keywords|terms|patterns|rules|logs|events|messages|queries|metrics|layers|geometries|domains|prefectures|cities|sites|subjects|assets|attachments|citations|references|notes|steps|edges|nodes|vertices|topics)$/i;
const OBJECT_NAMES = /^(metadata|config|options|spec|address|coordinates|payment|profile|boundary|context|settings|attributes|params|data|payload|details|meta|scope|filter|acousticprofile|material)$/i;
const OBJECT_SUFFIXES = /(profile|config|metadata|spec|options|settings|params|context|attributes|payload)$/i;

function promoteTypeByName(propName, currentType) {
  if (currentType !== "string" && currentType !== "unknown") return currentType;
  // Integer first (subset of number). Note: INTEGER_SUFFIXES is a subset of NUMERIC_SUFFIXES.
  if (INTEGER_SUFFIXES.test(propName)) return "integer";
  if (NUMERIC_SUFFIXES.test(propName)) return "number";
  if (BOOLEAN_PREFIXES.test(propName) || BOOLEAN_NAMES.test(propName)) return "boolean";
  if (ARRAY_PLURALS.test(propName)) return "array";
  if (OBJECT_NAMES.test(propName) || OBJECT_SUFFIXES.test(propName)) return "object";
  return currentType;
}

/**
 * Second-pass property-type promotion from handler code evidence.
 * Detects patterns the primary pass missed:
 *   - `args.X.length` / `args.X.map(...)` / `args.X.push(...)` → array
 *   - `args.X > 0` / `args.X + 1` / `args.X - foo` / `Math.floor(args.X)` → number
 *   - `if (args.X)` truthiness in a boolean context → boolean
 */
function promoteTypeByHandlerPattern(propName, currentType, argNames, handlerBody) {
  if (currentType !== "string" && currentType !== "unknown") return currentType;
  for (const argName of argNames) {
    const esc = argName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    // Array: .length / .map / .push / .forEach / .filter / .reduce / .join / .some / .every
    const arrayRe = new RegExp(`${esc}\\??\\.${propName}\\??\\.(length|map|push|forEach|filter|reduce|join|some|every|includes|find|slice|concat)\\b`);
    if (arrayRe.test(handlerBody)) return "array";
    // Number: Math.*(args.X) / args.X > N / args.X + N / args.X - N / args.X * N / args.X / N
    const mathRe = new RegExp(`Math\\.(?:floor|ceil|round|min|max|abs|pow)\\(\\s*${esc}\\??\\.${propName}\\b`);
    if (mathRe.test(handlerBody)) return "number";
    const arithRe = new RegExp(`${esc}\\??\\.${propName}\\s*[<>+\\-*/]\\s*\\d`);
    if (arithRe.test(handlerBody)) return "number";
    // Boolean: `? args.X : ...` or `!args.X` isolated
    const ternRe = new RegExp(`${esc}\\??\\.${propName}\\s*\\?`);
    if (ternRe.test(handlerBody) && (BOOLEAN_PREFIXES.test(propName) || BOOLEAN_NAMES.test(propName))) return "boolean";
  }
  return currentType;
}

/** Refine input/output property types using D3 heuristics + handler code patterns. */
function applyD3Heuristics(inputProps, outputProps, argNames, handlerBody) {
  for (const [key, ty] of Object.entries(inputProps)) {
    const promoted = promoteTypeByHandlerPattern(key, promoteTypeByName(key, ty), argNames, handlerBody);
    if (promoted !== ty) inputProps[key] = promoted;
  }
  for (const [key, ty] of Object.entries(outputProps)) {
    // Output only gets name-suffix refinement (no handler evidence for returns)
    const promoted = promoteTypeByName(key, ty);
    if (promoted !== ty) outputProps[key] = promoted;
  }
}

// Parse a TS type literal like "{foo: string; bar: number}" into { foo: "string", bar: "number" }.
function parseTsTypeLiteral(typeStr) {
  /** @type {Record<string, string>} */
  const out = {};
  const m = typeStr.match(/\{([^}]+)\}/);
  if (!m) return out;
  const body = m[1];
  for (const entry of body.split(/[;,]/)) {
    const parts = entry.trim().match(/^(\w+)\??\s*:\s*(\w+)/);
    if (!parts) continue;
    const [, key, ty] = parts;
    if (/string/i.test(ty)) out[key] = "string";
    else if (/number|int/i.test(ty)) out[key] = "number";
    else if (/boolean|bool/i.test(ty)) out[key] = "boolean";
    else if (/\[\]|Array/i.test(ty)) out[key] = "array";
    else out[key] = "unknown";
  }
  return out;
}

// Convert inferred { key: type } map into Lexicon JSON schema properties block.
function toSchemaProps(typeMap) {
  const out = {};
  for (const [key, ty] of Object.entries(typeMap)) {
    if (ty === "array") out[key] = { type: "array", items: { type: "string" } };
    else if (ty === "object") out[key] = { type: "object" };
    else if (ty === "unknown") out[key] = { type: "string" };
    else out[key] = { type: ty };
  }
  return out;
}

// Walk lexicon tree and update stub schemas with input + output + required.
function updateLexicon(nsid, inferred) {
  const parts = nsid.split(".");
  const file = path.join(ROOT, "00-contracts/lexicons", ...parts.slice(0, -1), `${parts[parts.length - 1]}.json`);
  if (!existsSync(file)) return { status: "missing" };
  const src = readFileSync(file, "utf8");
  let lex;
  try {
    lex = JSON.parse(src);
  } catch {
    return { status: "parse-error" };
  }
  const main = lex?.defs?.main;
  if (!main) return { status: "no-main" };
  if (main["x-bootstrap"] !== true) return { status: "hand-authored" };

  const isQuery = main.type === "query";
  const inputTarget = isQuery ? main.parameters : main.input?.schema;
  const outputTarget = main.output?.schema;
  if (!inputTarget || !outputTarget) return { status: "no-target" };

  let changed = false;

  // Input: only populate if currently empty (preserve prior inference / manual tightening)
  const existingInput = inputTarget.properties || {};
  if (Object.keys(existingInput).length === 0 && Object.keys(inferred.inputProps).length > 0) {
    inputTarget.properties = toSchemaProps(inferred.inputProps);
    changed = true;
  }

  // Required: only set if currently empty and inference found required keys that exist in the properties
  if ((!inputTarget.required || inputTarget.required.length === 0) && inferred.required.length > 0) {
    const validRequired = inferred.required.filter((k) => inputTarget.properties && k in inputTarget.properties);
    if (validRequired.length > 0) {
      inputTarget.required = validRequired;
      changed = true;
    }
  }

  // Output: only populate if currently empty
  const existingOutput = outputTarget.properties || {};
  if (Object.keys(existingOutput).length === 0 && Object.keys(inferred.outputProps).length > 0) {
    outputTarget.properties = toSchemaProps(inferred.outputProps);
    outputTarget.required = [];
    changed = true;
  }

  // --refine: tighten ALREADY-populated `string`-typed properties via D3 heuristics.
  if (isRefine) {
    const refined = refineSchemaTypes(inputTarget.properties || {}, inferred);
    if (refined.changed) changed = true;
    const refinedOut = refineSchemaTypes(outputTarget.properties || {}, { outputProps: inferred.outputProps });
    if (refinedOut.changed) changed = true;
  }

  if (!changed) return { status: "no-inference" };

  if (isDryRun) return { status: "would-update" };

  writeFileSync(file, JSON.stringify(lex, null, 2) + "\n", "utf8");
  return { status: "updated" };
}

/**
 * Refine existing schema properties in-place: promote `{ type: "string" }` entries
 * based on name-suffix heuristics + any stronger type found by the current inference run.
 * Mutates `schemaProps` and returns { changed: boolean }.
 */
function refineSchemaTypes(schemaProps, inferred) {
  let changed = false;
  for (const [key, spec] of Object.entries(schemaProps)) {
    if (!spec || typeof spec !== "object") continue;
    const currentType = spec.type;
    if (currentType !== "string") continue;

    // 1. Check if the current inference run produced a stronger type for this property
    const inferredType = (inferred.inputProps && inferred.inputProps[key])
      || (inferred.outputProps && inferred.outputProps[key]);
    let promoted = currentType;
    if (inferredType && inferredType !== "string" && inferredType !== "unknown") {
      promoted = inferredType;
    }
    // 2. Apply name-suffix heuristic
    promoted = promoteTypeByName(key, promoted);
    if (promoted === currentType) continue;

    // Rewrite the spec in place
    if (promoted === "array") {
      schemaProps[key] = { type: "array", items: { type: "string" } };
    } else if (promoted === "object") {
      schemaProps[key] = { type: "object" };
    } else {
      schemaProps[key] = { type: promoted };
    }
    changed = true;
  }
  return { changed };
}

function main() {
  const appFiles = listAppFiles();
  console.error(`scanning ${appFiles.length} app.ts files`);

  /** @type {Map<string, { inputProps: Record<string,string>, required: string[], outputProps: Record<string,string> }>} */
  const schemaByNsid = new Map();

  for (const rel of appFiles) {
    const src = readFileSync(path.join(ROOT, rel), "utf8");
    const cmds = extractCommands(src);
    for (const { nsid, bodyParamName, handlerBody } of cmds) {
      const inferred = inferSchemaFromHandler(bodyParamName, handlerBody);
      const hasInput = Object.keys(inferred.inputProps).length > 0;
      const hasOutput = Object.keys(inferred.outputProps).length > 0;
      if (!hasInput && !hasOutput) continue;
      const existing = schemaByNsid.get(nsid) || { inputProps: {}, required: [], outputProps: {} };
      schemaByNsid.set(nsid, {
        inputProps: { ...existing.inputProps, ...inferred.inputProps },
        required: [...new Set([...existing.required, ...inferred.required])],
        outputProps: { ...existing.outputProps, ...inferred.outputProps },
      });
    }
  }

  console.error(`inferred schemas for ${schemaByNsid.size} NSIDs`);

  const stats = { updated: 0, "would-update": 0, "hand-authored": 0, missing: 0, "no-main": 0, "no-target": 0, "parse-error": 0, "no-inference": 0 };
  for (const [nsid, inferred] of schemaByNsid) {
    const res = updateLexicon(nsid, inferred);
    stats[res.status] = (stats[res.status] || 0) + 1;
  }

  console.log(`\n=== lexicon schema inference ${isDryRun ? "(dry-run)" : "(applied)"} ===`);
  for (const [k, v] of Object.entries(stats).sort((a, b) => b[1] - a[1])) {
    if (v > 0) console.log(`  ${k}: ${v}`);
  }
}

main();
