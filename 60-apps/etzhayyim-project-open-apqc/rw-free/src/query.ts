/**
 * Query: MST prefix traversal via @etzhayyim/sdk.read().
 *
 * Phase 1 ships only the L1 layer (13 records, rkey = "1.0".."13.0"),
 * so the only meaningful prefix is a single digit (e.g. "1" matches
 * both "1.0" and "10.0"..."13.0"). Single-record lookup by exact code
 * works at any layer once L2–L5 land in future PRs.
 *
 * Usage:
 *   pnpm tsx src/query.ts --code=7.0           # one L1 category
 *   pnpm tsx src/query.ts --prefix=1           # 1.0 + 10.0–13.0 prefix-match
 *   pnpm tsx src/query.ts                       # all 13 L1 categories
 */

import { Etzhayyim } from "@etzhayyim/sdk";
import type { ProcessCategory } from "./types.js";

const COLLECTION = "com.etzhayyim.apqc.processCategory";

const e = new Etzhayyim({
  did: process.env.ETZ_READER_DID ?? "did:web:etzhayyim.com",
  pdsUrl: process.env.ETZ_PDS_URL ?? "https://pds.etzhayyim.com",
  ipfsGateway: process.env.ETZ_IPFS_GATEWAY ?? "https://ipfs.etzhayyim.com",
  l2RpcUrl: process.env.ETZ_L2_RPC_URL ?? "https://mainnet.base.org",
});

interface Args {
  prefix?: string;
  code?: string;
  limit?: number;
  fetchBlobs?: boolean;
}

function parseArgs(argv: string[]): Args {
  const out: Args = {};
  for (const a of argv) {
    const m = a.match(/^--(\w+)(?:=(.*))?$/);
    if (!m) continue;
    const [, k, v] = m;
    if (k === "limit") out.limit = Number(v);
    else if (k === "fetchBlobs") out.fetchBlobs = v !== "false";
    else (out as Record<string, unknown>)[k] = v;
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.code) {
    const { records } = await e.read<ProcessCategory>({
      collection: COLLECTION,
      rkey: args.code,
      fetchBlobs: args.fetchBlobs ?? false,
    });
    console.log(JSON.stringify(records[0] ?? null, null, 2));
    return;
  }

  const prefix = args.prefix ?? "";
  const { records, cursor } = await e.read<ProcessCategory>({
    collection: COLLECTION,
    prefix,
    limit: args.limit ?? 50,
    fetchBlobs: args.fetchBlobs ?? false,
  });
  console.log(`[query] prefix=${JSON.stringify(prefix)} → ${records.length} records`);
  for (const r of records) {
    console.log(`  ${r.value.code.padStart(5)}  ${r.value.name}`);
  }
  if (cursor) console.log(`[query] next cursor: ${cursor}`);
}

const isMainModule =
  import.meta.url.startsWith("file:") &&
  process.argv[1] &&
  import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));
if (isMainModule) {
  main().catch((err) => {
    console.error("[query] fatal:", err);
    process.exit(2);
  });
}
