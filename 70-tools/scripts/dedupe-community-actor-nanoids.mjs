#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const cwd = process.cwd();
const write = process.argv.includes("--write");
const root = path.join(cwd, "projects");

const TARGET_ID_SET = new Set(["festival", "carnival"]);
const TARGET_PATH_RE = /etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-org-community-/;

function walk(dir, out) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.name === ".git" || ent.name === "node_modules") continue;
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(full, out);
    else if (ent.isFile() && ent.name === "kotodama.jsonld") out.push(full);
  }
}

function readJSON(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function getNanoid(obj) {
  return obj.nanoid ?? obj.app?.nanoid ?? obj.actor?.nanoid ?? obj.metadata?.nanoid;
}

function setNanoid(obj, val) {
  if (typeof obj.nanoid === "string") {
    obj.nanoid = val;
    return;
  }
  if (obj.app && typeof obj.app.nanoid === "string") {
    obj.app.nanoid = val;
    return;
  }
  if (obj.actor && typeof obj.actor.nanoid === "string") {
    obj.actor.nanoid = val;
    return;
  }
  if (obj.metadata && typeof obj.metadata.nanoid === "string") {
    obj.metadata.nanoid = val;
    return;
  }
  obj.nanoid = val;
}

function genUniqueNanoid(seed, used) {
  for (let i = 0; i < 1000; i++) {
    const h = crypto.createHash("sha1").update(`${seed}#${i}`).digest("hex").slice(0, 8);
    if (!used.has(h)) return h;
  }
  throw new Error(`failed to generate nanoid for ${seed}`);
}

const kotodamaFiles = [];
walk(root, kotodamaFiles);

const idToFiles = new Map();
const allUsed = new Set();
for (const f of kotodamaFiles) {
  const j = readJSON(f);
  const id = getNanoid(j);
  if (typeof id !== "string") continue;
  allUsed.add(id);
  if (!idToFiles.has(id)) idToFiles.set(id, []);
  idToFiles.get(id).push(f);
}

const updates = [];
for (const [id, files] of idToFiles.entries()) {
  if (files.length < 2) continue;
  if (!TARGET_ID_SET.has(id)) continue;
  for (const f of files) {
    if (!TARGET_PATH_RE.test(f)) continue;
    updates.push({ kotodamaPath: f, oldId: id });
  }
}

let changed = 0;
for (const u of updates) {
  const rel = path.relative(cwd, u.kotodamaPath);
  const dir = path.dirname(u.kotodamaPath);
  const appTs = path.join(dir, "src", "app.ts");
  const newId = genUniqueNanoid(rel, allUsed);
  allUsed.add(newId);

  const j = readJSON(u.kotodamaPath);
  setNanoid(j, newId);

  let appSrc = fs.readFileSync(appTs, "utf8");
  const re = new RegExp(`([\"'])${u.oldId}\\1`, "g");
  const nextSrc = appSrc.replace(re, `$1${newId}$1`);

  if (write) {
    fs.writeFileSync(u.kotodamaPath, JSON.stringify(j, null, 2) + "\n");
    fs.writeFileSync(appTs, nextSrc);
  }

  changed++;
  console.log(`${rel}: ${u.oldId} -> ${newId}`);
}

console.log(`dedupe-community-actor-nanoids: targets=${updates.length} changed=${changed} write=${write}`);
