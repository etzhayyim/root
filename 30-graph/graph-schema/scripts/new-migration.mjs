#!/usr/bin/env node

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const migrationsDir = path.resolve(__dirname, "..", "migrations");

function usage() {
  console.error("usage: node scripts/new-migration.mjs <name>");
  console.error("example: node scripts/new-migration.mjs legal_entity_statement_relations");
  process.exit(2);
}

function slugify(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function utcTimestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return [
    d.getUTCFullYear(),
    pad(d.getUTCMonth() + 1),
    pad(d.getUTCDate()),
    pad(d.getUTCHours()),
    pad(d.getUTCMinutes()),
    pad(d.getUTCSeconds()),
  ].join("");
}

const rawName = process.argv[2];
if (!rawName) usage();

const name = slugify(rawName);
if (!name) usage();

const filename = `${utcTimestamp()}_${name}.ts`;
const fullpath = path.join(migrationsDir, filename);

if (!existsSync(migrationsDir)) mkdirSync(migrationsDir, { recursive: true });
if (existsSync(fullpath)) {
  console.error(`migration already exists: ${fullpath}`);
  process.exit(1);
}

const template = `// tier: C   // ADR-0040: A=actor DID / B=sub-path did:etzhayyim / C=no DID (default).
//             If creating any \`vertex_*\` table, also add it to
//             \`30-graph/deps.toml [vertex_tier.tier_*.tables]\`.
import { Kysely, sql } from 'kysely';

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql\`\`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql\`\`.execute(db);
}
`;

writeFileSync(fullpath, template);
console.log(fullpath);
