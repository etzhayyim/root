export type { SegmentDef } from "./types.js";
export { cpcSectionFor, isValidCode, isValidSlug } from "./types.js";

// Programmatic entry points (in addition to the CLI bins). Apps that
// embed open-unispsc segment-catalog read access can import from here:
//   import { queryByPrefix, getByCode } from "@etzhayyim/open-unispsc-kotoba";

import { Etzhayyim } from "@etzhayyim/sdk";
import type { SegmentDef } from "./types.js";

const COLLECTION = "com.etzhayyim.apps.openUnispsc.segmentDef";

function defaultClient() {
  return new Etzhayyim({
    did: "did:web:etzhayyim.com",
    pdsUrl: "https://pds.etzhayyim.com",
    ipfsGateway: "https://ipfs.etzhayyim.com",
    l2RpcUrl: "https://mainnet.base.org",
  });
}

export async function queryByPrefix(
  prefix: string,
  opts: { limit?: number; client?: Etzhayyim } = {},
): Promise<SegmentDef[]> {
  const e = opts.client ?? defaultClient();
  const { records } = await e.read<SegmentDef>({
    collection: COLLECTION,
    prefix,
    limit: opts.limit ?? 100,
    fetchBlobs: false,
  });
  return records.map((r) => r.value);
}

export async function getByCode(
  code: string,
  opts: { client?: Etzhayyim } = {},
): Promise<SegmentDef | null> {
  const e = opts.client ?? defaultClient();
  const { records } = await e.read<SegmentDef>({
    collection: COLLECTION,
    rkey: code,
    fetchBlobs: false,
  });
  return records[0]?.value ?? null;
}
