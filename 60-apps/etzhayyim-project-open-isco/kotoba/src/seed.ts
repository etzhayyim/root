/**
 * Seeder: ISCO CSV → AT Records via @etzhayyim/sdk.
 *
 * Replaces the old RW seed migration
 * (30-graph/graph-schema/sql_migrations/*_open_isco_*.up.sql) with a
 * straight-line PDS write loop. Idempotent: rkey derives from `code`
 * so re-running with the same CSV is a no-op past the first run.
 *
 * Usage:
 *   pnpm tsx src/seed.ts data/isco08.full.csv
 */

import { readFile } from "node:fs/promises";
import { Etzhayyim } from "@etzhayyim/sdk";
import type { Occupation } from "./types.js";

const COLLECTION = "com.etzhayyim.apps.openIsco.occupation";

const e = new Etzhayyim({
  did: process.env.ETZ_SEEDER_DID ?? "did:web:etzhayyim.com",
  pdsUrl: process.env.ETZ_PDS_URL ?? "https://pds.etzhayyim.com",
  ipfsApiUrl: process.env.ETZ_IPFS_API_URL,
  l2RpcUrl: process.env.ETZ_L2_RPC_URL ?? "https://mainnet.base.org",
  anchorContract:
    (process.env.ETZ_ANCHOR_CONTRACT as `0x${string}` | undefined) ??
    undefined,
});

interface CsvRow {
  code: string;
  name: string;
  description?: string;
}

function parseHierarchy(code: string): Pick<Occupation, "major" | "subMajor" | "minor" | "unitGroup"> {
  const c = code.padStart(4, "0");
  return {
    major: c.slice(0, 1),
    subMajor: c.slice(0, 2),
    minor: c.slice(0, 3),
    unitGroup: c.slice(0, 4),
  };
}

async function loadCsv(path: string): Promise<CsvRow[]> {
  const txt = await readFile(path, "utf8");
  // Minimal CSV parse — production seeder should use a real parser. ISCO data
  // has no commas in names so naive splitting is safe for this dataset.
  const [header, ...rows] = txt.split("\n").filter((l) => l.trim().length > 0);
  const cols = header.split(",").map((s) => s.trim());
  return rows.map((line) => {
    const cells = line.split(",").map((s) => s.trim());
    const r: Record<string, string> = {};
    cols.forEach((col, i) => (r[col] = cells[i] ?? ""));
    return { code: r.code, name: r.name, description: r.description };
  });
}

async function seedOne(row: CsvRow): Promise<{ uri: string; skipped: boolean }> {
  const record: Occupation = {
    code: row.code,
    name: row.name,
    description: row.description,
    ...parseHierarchy(row.code),
    publishedAt: "2008-01-01T00:00:00Z", // ISCO-08 baseline
  };
  // rkey = code so re-runs are idempotent (PDS returns existing on duplicate)
  const receipt = await e.write({
    collection: COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey: row.code,
  });
  return { uri: receipt.uri, skipped: false };
}

async function main() {
  const path = process.argv[2];
  if (!path) {
    console.error("usage: pnpm tsx src/seed.ts <isco-csv-path>");
    process.exit(1);
  }
  const rows = await loadCsv(path);
  console.log(`[seed] loaded ${rows.length} ISCO rows from ${path}`);

  let okCount = 0;
  let errCount = 0;
  for (const row of rows) {
    try {
      const r = await seedOne(row);
      okCount += 1;
      if (okCount % 50 === 0) console.log(`[seed] ${okCount}/${rows.length}  …`);
    } catch (err) {
      errCount += 1;
      console.error(`[seed] FAILED code=${row.code}: ${(err as Error).message}`);
    }
  }
  console.log(`[seed] DONE  ok=${okCount}  err=${errCount}`);
}

main().catch((err) => {
  console.error("[seed] fatal:", err);
  process.exit(2);
});
