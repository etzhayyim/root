#!/usr/bin/env node
/**
 * R2 → B2 codemod for `wrangler.jsonc` configs (ADR-0048).
 *
 * Surgical text edits that preserve the repo's compact inline JSONC
 * convention (e.g. `"compatibility_flags": ["nodejs_compat",...]`,
 * `{ "binding": "X", "id": "..." }` on one line). Does NOT parse+
 * restringify — that would explode inline arrays into multi-line and
 * blow up the diff.
 *
 * For a given Worker config file:
 *   1. Removes the `CDN_R2` entry from `r2_buckets`. Other R2 bindings
 *      (YATA_R2, CACHE_R2, TILES, GRAPH_R2, etc.) are preserved.
 *      If r2_buckets becomes empty, drops the section entirely.
 *   2. Adds B2 vars (`B2_BUCKET` / `B2_REGION` / `B2_ENDPOINT`) to
 *      the `vars` object (before its closing brace).
 *   3. Adds B2 secrets (`B2_KEY_ID` / `B2_APPLICATION_KEY`) to
 *      `secrets_store_secrets` (creates the section if absent).
 *
 * Usage:
 *   node 70-tools/scripts/migration/r2-to-b2-wrangler.mjs \
 *     --bucket etzhayyim-yuubin \
 *     60-apps/etzhayyim-project-yuubin/.../wrangler.jsonc
 *
 * Optional flags:
 *   --region <region>      default: us-east-005
 *   --endpoint <url>       default: https://s3.us-east-005.backblazeb2.com
 *   --store-id <id>        default: 1824561668fe47cc9127d493961885af
 *   --apply                write the file (default: dry-run preview)
 *   --no-secrets           skip B2_KEY_ID / B2_APPLICATION_KEY
 *
 * Defaults match the convention used by yuubin / ongakuka.
 */
import fs from "node:fs";
import path from "node:path";

const DEFAULTS = {
  region: "us-east-005",
  endpoint: "https://s3.us-east-005.backblazeb2.com",
  storeId: "1824561668fe47cc9127d493961885af",
};

function parseArgs(argv) {
  const out = {
    bucket: null,
    region: DEFAULTS.region,
    endpoint: DEFAULTS.endpoint,
    storeId: DEFAULTS.storeId,
    apply: false,
    addSecrets: true,
    files: [],
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--bucket") out.bucket = argv[++i];
    else if (a === "--region") out.region = argv[++i];
    else if (a === "--endpoint") out.endpoint = argv[++i];
    else if (a === "--store-id") out.storeId = argv[++i];
    else if (a === "--apply") out.apply = true;
    else if (a === "--no-secrets") out.addSecrets = false;
    else if (a === "--help" || a === "-h") {
      console.error("Usage: r2-to-b2-wrangler.mjs --bucket <name> [--region X] [--endpoint URL] [--store-id ID] [--apply] [--no-secrets] <wrangler.jsonc>...");
      process.exit(0);
    } else if (a.startsWith("-")) {
      console.error(`Unknown flag: ${a}`);
      process.exit(1);
    } else out.files.push(a);
  }
  return out;
}

// Find the bracket/brace span of a top-level key (`"key": [` or `"key": {`).
// Returns { start, end, openIdx, closeIdx, openCh, closeCh } or null.
// Bracket-balanced; respects string literals and JSONC comments.
function findKeySpan(text, key) {
  const re = new RegExp(`"${key}"\\s*:\\s*([\\[\\{])`, "g");
  const m = re.exec(text);
  if (!m) return null;
  const openIdx = m.index + m[0].length - 1;
  const openCh = m[1];
  const closeCh = openCh === "[" ? "]" : "}";
  let depth = 0;
  let i = openIdx;
  let inStr = false;
  let strCh = "";
  while (i < text.length) {
    const c = text[i];
    if (inStr) {
      if (c === "\\") { i += 2; continue; }
      if (c === strCh) inStr = false;
      i++;
      continue;
    }
    if (c === '"' || c === "'") { inStr = true; strCh = c; i++; continue; }
    if (c === "/" && text[i + 1] === "/") {
      while (i < text.length && text[i] !== "\n") i++;
      continue;
    }
    if (c === "/" && text[i + 1] === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i++;
      i += 2;
      continue;
    }
    if (c === "[" || c === "{") depth++;
    else if (c === "]" || c === "}") {
      depth--;
      if (depth === 0) return { start: m.index, end: i + 1, openIdx, closeIdx: i, openCh, closeCh };
    }
    i++;
  }
  return null;
}

// Within an array's [...] body, find the (start, end, leadingWs) span of
// the FIRST object element matching `"binding": "<binding>"`.
// Returns null if not found.
function findArrayObjectByBinding(text, arrSpan, binding) {
  const body = text.slice(arrSpan.openIdx + 1, arrSpan.closeIdx);
  const bodyOff = arrSpan.openIdx + 1;
  const re = new RegExp(`"binding"\\s*:\\s*"${binding}"`, "g");
  const m = re.exec(body);
  if (!m) return null;
  // Walk back from m.index to find the opening `{`.
  let i = m.index;
  let depth = 0;
  while (i >= 0) {
    const c = body[i];
    if (c === "}") depth++;
    else if (c === "{") {
      if (depth === 0) break;
      depth--;
    }
    i--;
  }
  if (i < 0) return null;
  const objStart = i;
  // Now walk forward from objStart to find the matching `}`.
  let j = objStart;
  let d = 0;
  let inStr = false;
  let strCh = "";
  while (j < body.length) {
    const c = body[j];
    if (inStr) {
      if (c === "\\") { j += 2; continue; }
      if (c === strCh) inStr = false;
      j++;
      continue;
    }
    if (c === '"' || c === "'") { inStr = true; strCh = c; j++; continue; }
    if (c === "{") d++;
    else if (c === "}") {
      d--;
      if (d === 0) { j++; break; }
    }
    j++;
  }
  // Expand to absorb leading whitespace + an optional trailing `,` and the
  // trailing whitespace/newline up to the next non-whitespace character.
  let absStart = bodyOff + objStart;
  let absEnd = bodyOff + j;
  while (absStart > arrSpan.openIdx + 1 && /[ \t]/.test(text[absStart - 1])) absStart--;
  if (absStart > arrSpan.openIdx + 1 && text[absStart - 1] === "\n") absStart--;
  // Trailing comma + same-line trailing space.
  while (absEnd < arrSpan.closeIdx && /[ \t]/.test(text[absEnd])) absEnd++;
  if (text[absEnd] === ",") absEnd++;
  while (absEnd < arrSpan.closeIdx && /[ \t]/.test(text[absEnd])) absEnd++;
  return { start: absStart, end: absEnd };
}

// Detect whether an empty range looks like an "empty container":
// `"key": []` or `"key": [\n]` or `"key": [ \n  \n ]` etc.
function isContainerEffectivelyEmpty(text, span) {
  const body = text.slice(span.openIdx + 1, span.closeIdx);
  return /^[\s,]*$/.test(body);
}

// Extend a top-level key span to include leading whitespace + one
// preceding `,` or `\n`, and trailing comma — for clean removal.
function extendForRemoval(text, span) {
  let start = span.start;
  let end = span.end;
  // Walk back to absorb the leading newline + indent.
  while (start > 0 && /[ \t]/.test(text[start - 1])) start--;
  if (start > 0 && text[start - 1] === "\n") start--;
  // Trailing comma on same line.
  while (end < text.length && /[ \t]/.test(text[end])) end++;
  if (text[end] === ",") end++;
  return { start, end };
}

function detectIndent(text) {
  // 2-space is the convention in this repo.
  const m = text.match(/^( +)"/m);
  return m ? m[1] : "  ";
}

function rewrite(text, args) {
  const changes = [];
  const indent = detectIndent(text);

  // 1. Remove CDN_R2 from r2_buckets (preserve other bindings).
  const r2Span = findKeySpan(text, "r2_buckets");
  if (r2Span && r2Span.openCh === "[") {
    const cdnEntry = findArrayObjectByBinding(text, r2Span, "CDN_R2");
    if (cdnEntry) {
      const before = text;
      text = text.slice(0, cdnEntry.start) + text.slice(cdnEntry.end);
      // Re-locate the array (offsets shifted).
      const r2Span2 = findKeySpan(text, "r2_buckets");
      if (r2Span2 && isContainerEffectivelyEmpty(text, r2Span2)) {
        const removal = extendForRemoval(text, r2Span2);
        text = text.slice(0, removal.start) + text.slice(removal.end);
        changes.push("drop CDN_R2 from r2_buckets (removed empty section)");
      } else {
        const remaining = (r2Span2 ? text.slice(r2Span2.openIdx + 1, r2Span2.closeIdx).match(/"binding"\s*:/g)?.length ?? 0 : 0);
        changes.push(`drop CDN_R2 from r2_buckets (${remaining} kept)`);
      }
      void before;
    }
  }

  // 2. Add B2_BUCKET / B2_REGION / B2_ENDPOINT to vars.
  const varsSpan = findKeySpan(text, "vars");
  if (!varsSpan || varsSpan.openCh !== "{") {
    throw new Error(`'vars' object not found in ${args.file}`);
  }
  const varsBody = text.slice(varsSpan.openIdx + 1, varsSpan.closeIdx);
  const have = (k) => new RegExp(`"${k}"\\s*:`).test(varsBody);
  const additions = [];
  if (!have("B2_BUCKET")) additions.push(["B2_BUCKET", args.bucket]);
  if (!have("B2_REGION")) additions.push(["B2_REGION", args.region]);
  if (!have("B2_ENDPOINT")) additions.push(["B2_ENDPOINT", args.endpoint]);
  if (additions.length > 0) {
    // Inject before the closing `}` of vars. Match the indent level of
    // existing keys inside vars.
    const innerIndent = (varsBody.match(/^([ \t]+)"/m) || ["", indent.repeat(2)])[1];
    const lines = additions.map(([k, v]) => `${innerIndent}"${k}": ${JSON.stringify(v)}`);
    // Find the last non-whitespace char before closeIdx.
    let insertAt = varsSpan.closeIdx;
    let trailingWs = "";
    while (insertAt > varsSpan.openIdx + 1 && /\s/.test(text[insertAt - 1])) {
      trailingWs = text[insertAt - 1] + trailingWs;
      insertAt--;
    }
    const lastChar = text[insertAt - 1];
    const sep = lastChar === "{" ? "" : ",";
    const insertText = sep + "\n" + lines.join(",\n") + trailingWs;
    text = text.slice(0, insertAt) + insertText + text.slice(insertAt + trailingWs.length);
    for (const [k, v] of additions) changes.push(`set vars.${k} = ${v}`);
  }

  // 3. Add B2_KEY_ID / B2_APPLICATION_KEY to secrets_store_secrets.
  if (args.addSecrets) {
    const newSecrets = [];
    const checkAndAdd = (binding, secretName) => {
      const span = findKeySpan(text, "secrets_store_secrets");
      const body = span ? text.slice(span.openIdx + 1, span.closeIdx) : "";
      if (!new RegExp(`"binding"\\s*:\\s*"${binding}"`).test(body)) {
        newSecrets.push({ binding, secretName });
      }
    };
    checkAndAdd("B2_KEY_ID", "b2_key_id");
    checkAndAdd("B2_APPLICATION_KEY", "b2_application_key");
    if (newSecrets.length > 0) {
      const span = findKeySpan(text, "secrets_store_secrets");
      const lines = newSecrets.map(
        (s) => `${indent.repeat(2)}{ "binding": "${s.binding}", "store_id": "${args.storeId}", "secret_name": "${s.secretName}" }`,
      );
      if (span) {
        // Inject before `]`. Walk back from closeIdx to find last non-ws.
        let insertAt = span.closeIdx;
        let trailingWs = "";
        while (insertAt > span.openIdx + 1 && /\s/.test(text[insertAt - 1])) {
          trailingWs = text[insertAt - 1] + trailingWs;
          insertAt--;
        }
        const lastChar = text[insertAt - 1];
        const sep = lastChar === "[" ? "" : ",";
        const insertText = sep + "\n" + lines.join(",\n") + trailingWs;
        text = text.slice(0, insertAt) + insertText + text.slice(insertAt + trailingWs.length);
      } else {
        // Append a new top-level `secrets_store_secrets`. Insert before
        // the final `}` of the document.
        const lastBrace = text.lastIndexOf("}");
        if (lastBrace < 0) throw new Error("could not find closing `}` of root object");
        // Walk back to the last non-whitespace char to decide on `,`.
        let i = lastBrace - 1;
        while (i >= 0 && /\s/.test(text[i])) i--;
        const sep = text[i] === "{" || text[i] === "," ? "" : ",";
        const block = `${sep}\n${indent}"secrets_store_secrets": [\n${lines.join(",\n")}\n${indent}]\n`;
        text = text.slice(0, lastBrace) + block + text.slice(lastBrace);
      }
      for (const s of newSecrets) changes.push(`add secrets_store_secrets.${s.binding}`);
    }
  }

  return { text, changes };
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.bucket) {
    console.error("Error: --bucket <name> is required");
    process.exit(1);
  }
  if (args.files.length === 0) {
    console.error("Error: at least one wrangler.jsonc path is required");
    process.exit(1);
  }

  let touched = 0;
  for (const file of args.files) {
    const abs = path.resolve(file);
    if (!fs.existsSync(abs)) {
      console.error(`skip   ${file} (not found)`);
      continue;
    }
    const orig = fs.readFileSync(abs, "utf8");
    let result;
    try {
      result = rewrite(orig, { ...args, file });
    } catch (e) {
      console.error(`error  ${file}: ${e.message}`);
      continue;
    }
    if (result.changes.length === 0 || result.text === orig) {
      console.log(`skip   ${file} (no changes)`);
      continue;
    }
    touched++;
    if (args.apply) {
      fs.writeFileSync(abs, result.text, "utf8");
      console.log(`apply  ${file}`);
    } else {
      console.log(`dry    ${file}`);
    }
    for (const c of result.changes) console.log(`         - ${c}`);
    if (!args.apply) console.log("         (run with --apply to write)");
  }

  console.log(`\nFiles changed: ${touched}/${args.files.length}`);
  if (touched > 0 && args.apply) {
    console.log("\nNext steps:");
    console.log("  1. mirror blob data to B2 (per bucket):");
    console.log(`       AWS_ACCESS_KEY_ID=$B2_KEY_ID AWS_SECRET_ACCESS_KEY=$B2_APPLICATION_KEY \\`);
    console.log(`       aws s3 sync --endpoint-url=${args.endpoint} \\`);
    console.log(`         s3://<src-r2-bucket>/ s3://${args.bucket}/`);
    console.log("  2. wrangler secret put B2_KEY_ID and B2_APPLICATION_KEY");
    console.log("  3. update src/app.ts CDN_R2.{get,put,head,delete} via");
    console.log("     70-tools/scripts/migration/r2-to-b2-codemod.mjs");
    console.log("  4. etzhayyim build && etzhayyim deploy && smoke-test");
  }
}

main();
