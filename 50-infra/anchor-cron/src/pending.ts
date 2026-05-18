/**
 * Pending-roots discovery.
 *
 * Talks to the checkpointer sidecar over its Unix socket and returns the
 * rows that have been IPFS-pinned but not yet L2-anchored. The sidecar's
 * in-process index is authoritative; we never go to PDS here.
 */
import {sha256} from "@noble/hashes/sha256";
import {bytesToHex} from "@noble/hashes/utils";

import {
  anchorPending as wireAnchorPending,
  type SaverIndexRow,
} from "./sidecarClient.js";

export interface PendingRoot {
  /** Source SaverIndexRow — passed through so submit.ts can size batchSize. */
  row: SaverIndexRow;
  /** sha256 over the UTF-8 bytes of `mst_root_cid`. Used as the on-chain
   *  primary key in EtzhayyimAnchor.anchors mapping. */
  rootHash: `0x${string}`;
  /** Raw bytes of mst_root_cid string — passed as the `ipfsCid` calldata
   *  to EtzhayyimAnchor.anchor(). */
  ipfsCidBytes: Uint8Array;
  /** Informational batchSize for the on-chain event. We anchor one MST
   *  root per call so batchSize == car_blob_count + 1 (the inline record). */
  batchSize: number;
}

export interface ReadPendingOpts {
  socketPath: string;
  cellDid: string;
  limit: number;
}

export async function readPending(
  opts: ReadPendingOpts
): Promise<PendingRoot[]> {
  const rows = await wireAnchorPending(opts.socketPath, opts.cellDid);
  const sliced = rows.slice(0, opts.limit);
  return sliced.map(toPendingRoot);
}

function toPendingRoot(row: SaverIndexRow): PendingRoot {
  const ipfsCidBytes = new TextEncoder().encode(row.mst_root_cid);
  const rootHash = ("0x" + bytesToHex(sha256(ipfsCidBytes))) as `0x${string}`;
  return {
    row,
    rootHash,
    ipfsCidBytes,
    batchSize: row.car_blob_count + 1,
  };
}
