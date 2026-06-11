/**
 * Seeder: APQC PCF v7.4 Level-1 categories → AT Records.
 *
 * The 13 L1 categories ship inline (the v7.4 cross-industry framework is
 * a public well-known list, not vendor data). Idempotent: rkey derives
 * from `code` so re-running is a no-op past the first run. Future PRs
 * for L2–L5 will load from a CSV / JSON source under
 * `60-apps/etzhayyim-project-open-apqc/data/` once that catalog is
 * checked in; Phase 1 stays inline because the cardinality is trivial
 * and locks down the structure.
 *
 * Usage:
 *   pnpm tsx src/seed.ts            # all 13 L1 categories
 *   pnpm tsx src/seed.ts --only=7.0 # one specific category
 */

import { Etzhayyim } from "@etzhayyim/sdk";
import {
  APQC_PCF_VERSION,
  APQC_PUBLISHED_AT_DEFAULT,
  isValidL1Code,
  l1Ordinal,
  type ProcessCategory,
} from "./types.js";

const COLLECTION = "com.etzhayyim.apqc.processCategory";

const e = new Etzhayyim({
  did: process.env.ETZ_SEEDER_DID ?? "did:web:etzhayyim.com",
  pdsUrl: process.env.ETZ_PDS_URL ?? "https://pds.etzhayyim.com",
  ipfsApiUrl: process.env.ETZ_IPFS_API_URL,
  l2RpcUrl: process.env.ETZ_L2_RPC_URL ?? "https://mainnet.base.org",
  anchorContract:
    (process.env.ETZ_ANCHOR_CONTRACT as `0x${string}` | undefined) ?? undefined,
});

/**
 * APQC PCF v7.4 Cross-Industry framework — the 13 L1 categories.
 *
 * Source: APQC's published PCF v7.4 (public taxonomy, freely usable
 * under APQC's open-license terms). The full L2–L5 detail will land in
 * future PRs as separate record lexicons.
 */
export const PCF_V74_L1_CATEGORIES: ReadonlyArray<{
  code: string;
  name: string;
}> = [
  {code: "1.0", name: "Develop Vision and Strategy"},
  {code: "2.0", name: "Develop and Manage Products and Services"},
  {code: "3.0", name: "Market and Sell Products and Services"},
  {code: "4.0", name: "Deliver Physical Products"},
  {code: "5.0", name: "Deliver Services"},
  {code: "6.0", name: "Manage Customer Service"},
  {code: "7.0", name: "Develop and Manage Human Capital"},
  {code: "8.0", name: "Manage Information Technology (IT)"},
  {code: "9.0", name: "Manage Financial Resources"},
  {code: "10.0", name: "Acquire, Construct, and Manage Assets"},
  {
    code: "11.0",
    name: "Manage Enterprise Risk, Compliance, Remediation, and Resiliency",
  },
  {code: "12.0", name: "Manage External Relationships"},
  {code: "13.0", name: "Develop and Manage Business Capabilities"},
];

interface Args {
  only?: string;
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

/** Pure: build the typed record body from the inline catalog entry. */
export function toProcessCategory(src: {
  code: string;
  name: string;
}): ProcessCategory {
  if (!isValidL1Code(src.code)) {
    throw new Error(`invalid APQC L1 code (expected 1.0–13.0): "${src.code}"`);
  }
  if (!src.name.trim()) {
    throw new Error(`empty name for code ${src.code}`);
  }
  return {
    code: src.code,
    name: src.name.trim(),
    level: 1,
    version: APQC_PCF_VERSION,
    publishedAt: APQC_PUBLISHED_AT_DEFAULT,
  };
}

async function seedOne(src: {code: string; name: string}): Promise<void> {
  const record = toProcessCategory(src);
  await e.write({
    collection: COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey: record.code,
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const filtered = PCF_V74_L1_CATEGORIES.filter((c) =>
    args.only ? c.code === args.only : true,
  );
  if (filtered.length === 0) {
    console.error("[seed] no categories match filter");
    process.exit(1);
  }
  console.log(`[seed] writing ${filtered.length} APQC L1 records (v${APQC_PCF_VERSION})`);

  // Stable sort by ordinal so MST insertion is deterministic.
  const sorted = [...filtered].sort(
    (a, b) => l1Ordinal(a.code) - l1Ordinal(b.code),
  );

  let okCount = 0;
  let errCount = 0;
  for (const src of sorted) {
    try {
      await seedOne(src);
      okCount += 1;
      console.log(`[seed]   ${src.code.padStart(4)}  ${src.name}`);
    } catch (err) {
      errCount += 1;
      console.error(`[seed] FAILED code=${src.code}: ${(err as Error).message}`);
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
