#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const PRIMARY_TYPES = new Set(["query", "procedure", "subscription", "record", "permission-set"]);
const CONCRETE_TYPES = new Set(["boolean", "integer", "number", "float", "string", "bytes", "cid-link", "blob"]);
const CONTAINER_TYPES = new Set(["array", "object"]);
const SUB_TYPES = new Set(["params", "permission"]);
const META_TYPES = new Set(["token", "ref", "union", "unknown"]);
const LEXICON_ROOTS = ["00-contracts/lexicons", "projects", "packages"].filter((dir) =>
  existsSync(path.join(ROOT, dir)),
);
const ALLOWED_TYPES = new Set([
  ...PRIMARY_TYPES,
  ...CONCRETE_TYPES,
  ...CONTAINER_TYPES,
  ...SUB_TYPES,
  ...META_TYPES,
]);

function listLexiconFiles() {
  let out = "";
  try {
    out = execFileSync(
      "rg",
      ["-l", String.raw`"lexicon"\s*:\s*1`, "-g", "*.json", ...LEXICON_ROOTS],
      { cwd: ROOT, encoding: "utf8" },
    );
  } catch (error) {
    // rg exits with code 1 when there are no matches; treat that as empty input.
    if (error && typeof error === "object" && "status" in error && error.status === 1) {
      return [];
    }
    throw error;
  }
  out = out.trim();
  if (!out) return [];
  return out
    .split("\n")
    .filter(Boolean)
    .filter((file) => file.startsWith("00-contracts/lexicons/com/etzhayyim/"))
    .sort();
}

function gatherTypeNodes(value, nodePath = "$", out = []) {
  if (!value || typeof value !== "object") return out;
  if (!Array.isArray(value) && typeof value.type === "string") {
    out.push({ type: value.type, path: `${nodePath}.type` });
  }
  if (Array.isArray(value)) {
    value.forEach((v, i) => gatherTypeNodes(v, `${nodePath}[${i}]`, out));
    return out;
  }
  for (const [k, v] of Object.entries(value)) {
    gatherTypeNodes(v, `${nodePath}.${k}`, out);
  }
  return out;
}

function validateLexicon(file) {
  const json = JSON.parse(readFileSync(path.join(ROOT, file), "utf8"));
  const errors = [];

  if (json.lexicon !== 1) {
    errors.push("lexicon must be 1");
    return errors;
  }

  const mainType = json?.defs?.main?.type;
  if (!PRIMARY_TYPES.has(mainType)) {
    errors.push(`defs.main.type must be one of primary types, got: ${String(mainType)}`);
  }

  const typeNodes = gatherTypeNodes(json);
  for (const node of typeNodes) {
    if (!ALLOWED_TYPES.has(node.type)) {
      errors.push(`disallowed type "${node.type}" at ${node.path}`);
    }
  }

  if (mainType === "record") {
    if (!json?.defs?.main?.record) {
      errors.push("record must define defs.main.record");
    }
  }

  return errors;
}

function main() {
  const files = listLexiconFiles();
  if (files.length === 0) {
    console.log("lexicon-primary-types: no lexicon files found");
    return;
  }

  const allErrors = [];
  for (const file of files) {
    const errs = validateLexicon(file);
    for (const e of errs) allErrors.push(`${file}: ${e}`);
  }

  if (allErrors.length > 0) {
    console.error("lexicon-primary-types: violations found");
    for (const e of allErrors) console.error(`- ${e}`);
    process.exit(1);
  }

  console.log(`lexicon-primary-types: OK (${files.length} files)`);
}

main();
