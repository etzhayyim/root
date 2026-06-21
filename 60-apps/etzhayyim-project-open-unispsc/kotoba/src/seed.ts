/**
 * Seeder: segments.csv → AT Records via @etzhayyim/sdk.
 *
 * Replaces the RW seed path (was `vertex_open_unispsc_segment` migration)
 * with a straight-line PDS write loop. Idempotent: rkey derives from
 * `code` so re-running is a no-op past the first run. The CSV ships
 * three columns (code, slug, name) and the converter fills in the
 * derived `cpcSection` + default `publishedAt`.
 *
 * Usage:
 *   pnpm tsx src/seed.ts                 # all 50 segments from ../segments.csv
 *   pnpm tsx src/seed.ts --only=43       # one specific segment
 *   pnpm tsx src/seed.ts --since=80      # resume from a code
 */

import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Etzhayyim } from "@etzhayyim/sdk";
import {
  cpcSectionFor,
  isValidCode,
  isValidSlug,
  UNSPSC_PUBLISHED_AT_DEFAULT,
  type SegmentDef,
} from "./types.js";

const COLLECTION = "com.etzhayyim.apps.openUnispsc.segmentDef";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CSV_PATH = join(__dirname, "..", "..", "segments.csv");

const e = new Etzhayyim({
  did: process.env.ETZ_SEEDER_DID ?? "did:web:etzhayyim.com",
  pdsUrl: process.env.ETZ_PDS_URL ?? "https://pds.etzhayyim.com",
  ipfsApiUrl: process.env.ETZ_IPFS_API_URL,
  l2RpcUrl: process.env.ETZ_L2_RPC_URL ?? "https://mainnet.base.org",
  anchorContract:
    (process.env.ETZ_ANCHOR_CONTRACT as `0x${string}` | undefined) ?? undefined,
});

export interface SegmentCsvRow {
  code: string;
  slug: string;
  name: string;
}

interface Args {
  csv?: string;
  only?: string;
  since?: string;
}

function parseArgs(argv: string[]): Args {
  const out: Args = {};
  for (const a of argv) {
    const m = a.match(/^--(\w+)(?:=(.*))?$/);
    if (!m) continue;
    const [, k, v] = m;
    (out as Record<string, string | undefined>)[k] = v;
  }
  return out;
}

/** Pure: convert a CSV row to a typed SegmentDef record body. */
export function csvRowToSegmentDef(row: SegmentCsvRow): SegmentDef {
  if (!isValidCode(row.code)) {
    throw new Error(`invalid UNSPSC segment code (must be 2 digits): "${row.code}"`);
  }
  if (!isValidSlug(row.slug)) {
    throw new Error(`invalid slug for code ${row.code}: "${row.slug}"`);
  }
  if (!row.name.trim()) {
    throw new Error(`empty name for code ${row.code}`);
  }
  const cpcSection = cpcSectionFor(row.code);
  const out: SegmentDef = {
    code: row.code,
    slug: row.slug,
    name: row.name.trim(),
    publishedAt: UNSPSC_PUBLISHED_AT_DEFAULT,
  };
  if (cpcSection) out.cpcSection = cpcSection;
  return out;
}

/**
 * Parse the 3-column CSV. Tolerant of trailing whitespace, blank lines,
 * and the header row (which is dropped). Returns rows in code order so
 * downstream MST writes hit the tree in a deterministic sequence.
 */
export function parseCsv(text: string): SegmentCsvRow[] {
  const lines = text.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
  if (lines.length === 0) return [];
  const [header, ...rest] = lines;
  const cols = header.split(",").map((s) => s.trim());
  const idxCode = cols.indexOf("code");
  const idxSlug = cols.indexOf("slug");
  const idxName = cols.indexOf("name");
  if (idxCode < 0 || idxSlug < 0 || idxName < 0) {
    throw new Error(`CSV header missing required columns; got: ${cols.join(",")}`);
  }
  const out: SegmentCsvRow[] = [];
  for (const line of rest) {
    // Most rows have no commas inside the name field; for the rare
    // rows that do (e.g. "Chemicals, including …"), we cut the line at
    // the (idxName)-th comma and keep everything after it raw so commas
    // + the leading whitespace inside the name survive the split.
    const rawCells = line.split(",");
    if (rawCells.length < 3) continue;
    const tailFromName = rawCells.slice(idxName).join(",");
    out.push({
      code: rawCells[idxCode].trim(),
      slug: rawCells[idxSlug].trim(),
      name: tailFromName.trim(),
    });
  }
  out.sort((a, b) => a.code.localeCompare(b.code));
  return out;
}

async function loadCsv(path: string): Promise<SegmentCsvRow[]> {
  return parseCsv(await readFile(path, "utf8"));
}

async function seedOne(row: SegmentCsvRow): Promise<void> {
  const record = csvRowToSegmentDef(row);
  await e.write({
    collection: COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey: record.code,
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const csvPath = args.csv ?? DEFAULT_CSV_PATH;
  const rows = await loadCsv(csvPath);
  console.log(`[seed] loaded ${rows.length} UNSPSC segments from ${csvPath}`);

  const filtered = rows.filter((r) => {
    if (args.only) return r.code === args.only;
    if (args.since) return r.code >= args.since;
    return true;
  });
  if (filtered.length === 0) {
    console.error("[seed] no segments match filter");
    process.exit(1);
  }
  console.log(`[seed] writing ${filtered.length} records (filter: ${JSON.stringify(args)})`);

  let okCount = 0;
  let errCount = 0;
  for (const row of filtered) {
    try {
      await seedOne(row);
      okCount += 1;
      if (okCount % 10 === 0) console.log(`[seed] ${okCount}/${filtered.length} …`);
    } catch (err) {
      errCount += 1;
      console.error(`[seed] FAILED code=${row.code}: ${(err as Error).message}`);
    }
  }
  console.log(`[seed] DONE  ok=${okCount}  err=${errCount}`);
}

const isMainModule =
  import.meta.url.startsWith("file:") &&
  process.argv[1] &&
  import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));
if (isMainModule) {
  main().catch((err) => {
    console.error("[seed] fatal:", err);
    process.exit(2);
  });
}
