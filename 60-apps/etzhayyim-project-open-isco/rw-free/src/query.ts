/**
 * Query: MST prefix traversal via @etzhayyim/sdk.read().
 *
 * Replaces the old RW query path
// CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
 * (kysely.selectFrom('vertex_open_isco_occupation').where(...))
 * with a direct PDS read over MST. Key-prefix filter maps to ISCO
 * hierarchy (1-digit major / 2-digit subMajor / 3-digit minor / 4-digit code).
 *
 * Usage:
 *   pnpm tsx src/query.ts --prefix=2          # all 'Professionals'
 *   pnpm tsx src/query.ts --code=2511         # one specific occupation
 *   pnpm tsx src/query.ts --major=2 --limit=200
 */

import { Etzhayyim } from "@etzhayyim/sdk";
import type { Occupation } from "./types.js";

const COLLECTION = "com.etzhayyim.apps.openIsco.occupation";

const e = new Etzhayyim({
  did: process.env.ETZ_READER_DID ?? "did:web:etzhayyim.com",
  pdsUrl: process.env.ETZ_PDS_URL ?? "https://pds.etzhayyim.com",
  ipfsGateway: process.env.ETZ_IPFS_GATEWAY ?? "https://ipfs.etzhayyim.com",
  l2RpcUrl: process.env.ETZ_L2_RPC_URL ?? "https://mainnet.base.org",
});

interface Args {
  prefix?: string;
  code?: string;
  major?: string;
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

  // Single-record lookup
  if (args.code) {
    const { records } = await e.read<Occupation>({
      collection: COLLECTION,
      rkey: args.code,
      fetchBlobs: args.fetchBlobs ?? false,
    });
    console.log(JSON.stringify(records[0] ?? null, null, 2));
    return;
  }

  // Prefix scan
  const prefix = args.prefix ?? args.major ?? "";
  const { records, cursor } = await e.read<Occupation>({
    collection: COLLECTION,
    prefix,
    limit: args.limit ?? 50,
    fetchBlobs: args.fetchBlobs ?? false,
  });
  console.log(`[query] prefix=${JSON.stringify(prefix)} → ${records.length} records`);
  for (const r of records) {
    console.log(`  ${r.value.code}  ${r.value.name}`);
  }
  if (cursor) console.log(`[query] next cursor: ${cursor}`);
}

main().catch((err) => {
  console.error("[query] fatal:", err);
  process.exit(2);
});
