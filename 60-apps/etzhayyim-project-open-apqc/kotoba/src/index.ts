export type { ProcessCategory } from "./types.js";
export {
  APQC_PCF_VERSION,
  APQC_PUBLISHED_AT_DEFAULT,
  isValidL1Code,
  l1Ordinal,
} from "./types.js";
export { PCF_V74_L1_CATEGORIES, toProcessCategory } from "./seed.js";

// Programmatic entry points (in addition to the CLI bins). Apps that
// embed open-apqc L1-catalog read access can import from here:
//   import { queryAll, getByCode } from "@etzhayyim/open-apqc-kotoba";

import { Etzhayyim } from "@etzhayyim/sdk";
import type { ProcessCategory } from "./types.js";

const COLLECTION = "com.etzhayyim.apqc.processCategory";

function defaultClient() {
  return new Etzhayyim({
    did: "did:web:etzhayyim.com",
    pdsUrl: "https://pds.etzhayyim.com",
    ipfsGateway: "https://ipfs.etzhayyim.com",
    l2RpcUrl: "https://mainnet.base.org",
  });
}

export async function queryAll(
  opts: { client?: Etzhayyim } = {},
): Promise<ProcessCategory[]> {
  const e = opts.client ?? defaultClient();
  const { records } = await e.read<ProcessCategory>({
    collection: COLLECTION,
    prefix: "",
    limit: 50,
    fetchBlobs: false,
  });
  return records.map((r) => r.value);
}

export async function getByCode(
  code: string,
  opts: { client?: Etzhayyim } = {},
): Promise<ProcessCategory | null> {
  const e = opts.client ?? defaultClient();
  const { records } = await e.read<ProcessCategory>({
    collection: COLLECTION,
    rkey: code,
    fetchBlobs: false,
  });
  return records[0]?.value ?? null;
}
