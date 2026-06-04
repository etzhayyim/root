#!/usr/bin/env node
// ADR-0039 Phase A.5 migration — move BPMN / DMN / Form JSON files from filesystem
// into vertex_repository_blob (content-addressed, per ADR-0039 §1).
//
// Input : 60-apps/**/{bpmn,dmn,forms}/*.{bpmn,dmn,form.json} on disk
// Action: POST com.etzhayyim.repository.createBlob → sha256-keyed INSERT into graph
// Output: JSON mapping array on stdout
//          [{ path, ownerDid, hash, sizeBytes, tier, deduplicated, contentType }]
//
// Next step (not this script): update the owning actor's manifest `val` to
// reference `bpmnBlobHash` / `dmnBlobHash` / `formsTreeHash` instead of inline.
//
// Env:
//   REPOSITORY_URL  — default https://repository.etzhayyim.com
//   DRY_RUN=1       — skip HTTP POST, only compute hash + emit mapping
//   VERBOSE=1       — per-file status to stderr

import { readdir, readFile, stat } from "node:fs/promises";
import { join, relative, dirname, basename } from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const APPS_ROOT = join(REPO_ROOT, "60-apps");
const ENDPOINT = process.env.REPOSITORY_URL ?? "https://repository.etzhayyim.com";
const DRY_RUN = process.env.DRY_RUN === "1";
const VERBOSE = process.env.VERBOSE === "1";

// Actor DID is derived from the 60-apps/etzhayyim-project-<slug>/ folder name.
// Slug → did:web:<slug>.etzhayyim.com (root case). Sub-actors keep root DID as owner
// for the initial migration pass; actor-scoped blob ownership is Phase E.
function deriveOwnerDid(absPath) {
  const rel = relative(APPS_ROOT, absPath);
  const m = rel.match(/^etzhayyim-project-([^/]+)\//);
  if (!m) return null;
  return `did:web:${m[1]}.etzhayyim.com`;
}

function classify(path) {
  if (path.endsWith(".bpmn") || path.endsWith(".bpmn.xml")) {
    return { kind: "bpmn", mimeType: "application/xml" };
  }
  if (path.endsWith(".dmn") || path.endsWith(".dmn.xml")) {
    return { kind: "dmn", mimeType: "application/xml" };
  }
  if (path.endsWith(".form.json")) {
    return { kind: "form", mimeType: "application/json" };
  }
  return null;
}

async function* walk(dir) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const ent of entries) {
    if (ent.name === "node_modules" || ent.name === ".git" || ent.name.startsWith(".etzhayyim-")) continue;
    const full = join(dir, ent.name);
    if (ent.isDirectory()) {
      yield* walk(full);
    } else if (ent.isFile()) {
      yield full;
    }
  }
}

function toB64Url(bytes) {
  return Buffer.from(bytes).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function createBlob(ownerDid, content, mimeType) {
  const res = await fetch(`${ENDPOINT}/xrpc/com.etzhayyim.repository.createBlob`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ownerDid, content: toB64Url(content), mimeType }),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`createBlob ${res.status}: ${text.slice(0, 200)}`);
  return JSON.parse(text);
}

const results = [];
let scanned = 0;
let migrated = 0;
let errored = 0;

for await (const file of walk(APPS_ROOT)) {
  const cls = classify(file);
  if (!cls) continue;
  scanned++;
  const owner = deriveOwnerDid(file);
  if (!owner) {
    if (VERBOSE) process.stderr.write(`[skip] no owner DID: ${file}\n`);
    continue;
  }

  try {
    const bytes = await readFile(file);
    const hash = createHash("sha256").update(bytes).digest("hex");
    const sizeBytes = bytes.length;
    const entry = {
      path: relative(REPO_ROOT, file),
      ownerDid: owner,
      kind: cls.kind,
      hash,
      sizeBytes,
      tier: sizeBytes > 16 * 1024 ? "r2" : "inline",
      mimeType: cls.mimeType,
    };

    if (!DRY_RUN) {
      const resp = await createBlob(owner, bytes, cls.mimeType);
      entry.hash = resp.hash;
      entry.tier = resp.tier;
      entry.deduplicated = resp.deduplicated;
      if (resp.hash !== hash) {
        entry.warning = `hash mismatch: local=${hash} remote=${resp.hash}`;
      }
    } else {
      entry.deduplicated = null;
      entry.dryRun = true;
    }

    migrated++;
    results.push(entry);
    if (VERBOSE) {
      process.stderr.write(
        `[${DRY_RUN ? "dry" : "ok"}] ${entry.kind} ${sizeBytes}B → ${hash.slice(0, 12)}… ${entry.deduplicated ? "(dedup)" : ""} ${entry.path}\n`,
      );
    }
  } catch (e) {
    errored++;
    const entry = { path: relative(REPO_ROOT, file), ownerDid: owner, kind: cls.kind, error: String(e.message ?? e) };
    results.push(entry);
    process.stderr.write(`[err] ${entry.path}: ${entry.error}\n`);
  }
}

process.stderr.write(
  `\nADR-0039 Phase A.5 scan: scanned=${scanned} migrated=${migrated} errored=${errored} endpoint=${ENDPOINT} dryRun=${DRY_RUN}\n`,
);

process.stdout.write(JSON.stringify({ endpoint: ENDPOINT, dryRun: DRY_RUN, scanned, migrated, errored, entries: results }, null, 2) + "\n");
