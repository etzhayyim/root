#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { transform } from "esbuild";

const cwd = process.cwd();
const args = new Set(process.argv.slice(2));
const write = args.has("--write");
const verify = args.has("--verify");
const actorsOnly = !args.has("--all");

function walk(dir, out) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name === ".git") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, out);
      continue;
    }
    if (entry.isFile() && full.endsWith(path.join("src", "app.ts"))) {
      out.push(full);
    }
  }
}

function normalize(source) {
  const lines = source.split("\n");
  let changed = false;
  let inJsonDispatch = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Repair a known broken pattern accidentally introduced in invokeRemote.
    if (
      line.includes("sdk.hostImports.invoke(targetDid, method, JSON.stringify(params)) });")
    ) {
      const fixed = line.replace(
        "sdk.hostImports.invoke(targetDid, method, JSON.stringify(params)) });",
        "sdk.hostImports.invoke(targetDid, method, JSON.stringify(params)));",
      );
      if (fixed !== line) {
        line = fixed;
        changed = true;
      }
    }

    const malformedPayload = line.replace(
      /payload:\s*[^,\n]+,\s*JSON\.stringify\(/,
      "payload: JSON.stringify(",
    );
    if (malformedPayload !== line) {
      line = malformedPayload;
      changed = true;
      inJsonDispatch = true;
    }

    if (line.includes("sdk.pds.dispatch({") && line.includes("payload: JSON.stringify(")) {
      inJsonDispatch = true;
    }

    if (inJsonDispatch && line.includes("));")) {
      const fixed = line.replace("));", ") });");
      if (fixed !== line) {
        line = fixed;
        changed = true;
      }
      inJsonDispatch = false;
    }

    if (
      line.includes('sdk.pds.dispatch({ type: "app.bsky.feed.post", payload: { text:')
    ) {
      const fixed = line
        .replace(/\}\s*\}\s*\}\s*\);\s*$/, " } });")
        .replace(/\}\s*\}\s*\);\s*$/, " } });")
        .replace(/\}\s*\);\s*$/, " } });");
      if (fixed !== line) {
        line = fixed;
        changed = true;
      }
    }

    if ((line.includes(".query(") || line.includes(".command(")) && line.includes(") });")) {
      const fixed = line.replace(/\) \}\);/g, "));");
      if (fixed !== line) {
        line = fixed;
        changed = true;
      }
    }

    lines[i] = line;
  }

  for (let i = 0; i < lines.length; i++) {
    if (!/^\s*\.(query|command)\(/.test(lines[i])) continue;
    if (!lines[i].trimEnd().endsWith(";")) continue;
    let j = i + 1;
    while (j < lines.length && lines[j].trim() === "") j++;
    if (j < lines.length && /^\s*\./.test(lines[j])) {
      lines[i] = lines[i].replace(/;\s*$/, "");
      changed = true;
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!/^function\s+\w+\s*\(/.test(line)) continue;
    if (/^async\s+function/.test(line)) continue;
    let needsAsync = false;
    for (let j = i + 1; j < Math.min(lines.length, i + 40); j++) {
      if (lines[j].includes("return await ")) {
        needsAsync = true;
        break;
      }
      if (lines[j].trim() === "}") break;
    }
    if (needsAsync) {
      lines[i] = `async ${line}`;
      changed = true;
    }
  }

  return { changed, source: lines.join("\n") };
}

async function verifySyntax(filePath, source) {
  const rel = path.relative(cwd, filePath);
  try {
    await transform(source, { loader: "ts", format: "esm" });
  } catch (err) {
    return `syntax: ${rel}: ${err?.message ?? String(err)}`;
  }
  if (/payload:\s*[^,\n]+,\s*JSON\.stringify\(/.test(source)) {
    return `pattern: ${rel}: malformed dispatch payload`;
  }
  if (/\.query\([^\n]*\)\s*\}\);/.test(source) || /\.command\([^\n]*\)\s*\}\);/.test(source)) {
    return `pattern: ${rel}: malformed chain closure`;
  }
  return null;
}

const allFiles = [];
walk(path.join(cwd, "projects"), allFiles);
const targets = actorsOnly
  ? allFiles.filter((f) => f.includes("sys-etzhayyim-actors"))
  : allFiles;

let changedCount = 0;
const verifyErrors = [];

for (const filePath of targets) {
  const before = fs.readFileSync(filePath, "utf8");
  const normalized = normalize(before);
  if (write && normalized.changed) {
    fs.writeFileSync(filePath, normalized.source);
  }
  if (normalized.changed) changedCount++;
  if (verify) {
    const current = write ? normalized.source : before;
    const err = await verifySyntax(filePath, current);
    if (err) verifyErrors.push(err);
  }
}

const mode = actorsOnly ? "actors-only" : "all";
console.log(`stabilize-app-ts: mode=${mode} files=${targets.length} changed=${changedCount} write=${write} verify=${verify}`);
if (verifyErrors.length > 0) {
  console.error(`stabilize-app-ts: verify failed (${verifyErrors.length})`);
  for (const err of verifyErrors.slice(0, 100)) console.error(err);
  process.exit(1);
}
