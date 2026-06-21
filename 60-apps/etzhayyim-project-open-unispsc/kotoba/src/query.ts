/**
 * Query: MST prefix traversal via @etzhayyim/sdk.read().
 *
 * Phase 1 ships only the segment layer (50 records, rkey = 2-digit code),
 * so the only meaningful prefix is a single digit (e.g. "1" = segments
 * 10–19). Future PRs will add family/class/commodity layers under
 * separate record lexicons; their queries will use longer prefixes.
 *
 * Usage:
 *   pnpm tsx src/query.ts --code=43               # one segment
 *   pnpm tsx src/query.ts --prefix=1 --limit=20   # all 1x segments
 *   pnpm tsx src/query.ts                          # full list
 */

import { Etzhayyim } from "@etzhayyim/sdk";
import type { SegmentDef } from "./types.js";

const COLLECTION = "com.etzhayyim.apps.openUnispsc.segmentDef";

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
    const { records } = await e.read<SegmentDef>({
      collection: COLLECTION,
      rkey: args.code,
      fetchBlobs: args.fetchBlobs ?? false,
    });
    console.log(JSON.stringify(records[0] ?? null, null, 2));
    return;
  }

  const prefix = args.prefix ?? "";
  const { records, cursor } = await e.read<SegmentDef>({
    collection: COLLECTION,
    prefix,
    limit: args.limit ?? 100,
    fetchBlobs: args.fetchBlobs ?? false,
  });
  console.log(`[query] prefix=${JSON.stringify(prefix)} → ${records.length} records`);
  for (const r of records) {
    console.log(`  ${r.value.code}  ${r.value.slug.padEnd(28)}  ${r.value.name}`);
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
