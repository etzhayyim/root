/**
 * anchor-cron sidecar IPC client.
 *
 * Talks the checkpointer sidecar wire protocol (ADR-2605171800 §Stage 1)
 * for the two ops anchor-cron needs:
 *
 *   - anchor_pending → list SaverIndexRow that are ipfs_pinned_at != null
 *                      AND anchor_tx_hash == null. These are the roots
 *                      waiting to be anchored on Base L2.
 *
 *   - anchor_commit  → after a successful anchor() tx lands, tell the
 *                      sidecar so it stamps the row with tx_hash etc.
 *
 * Framing: 4-byte big-endian length prefix + msgpack body. Same on both
 * sides, identical to kotodama.checkpointer.mst_saver.
 */

import {connect, type Socket} from "node:net";
import {
  encode as msgpackEncode,
  decode as msgpackDecode,
} from "@msgpack/msgpack";

export const PROTOCOL_VERSION = 1 as const;

export interface SaverIndexRow {
  cell_did: string;
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string;
  mst_root_cid: string;
  car_size_bytes: number;
  car_blob_count: number;
  mst_projected_at: number;
  ipfs_pinned_at: number | null;
  ipfs_pin_service: string | null;
  ipfs_pin_id: string | null;
  anchor_tx_hash: `0x${string}` | null;
  anchor_block_number: number | null;
  anchor_log_index: number | null;
  anchor_chain_id: number;
  anchored_at: number | null;
}

export interface CommitEntry {
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string;
  anchor_tx_hash: `0x${string}`;
  anchor_block_number: number;
  anchor_log_index: number;
}

interface WireResponse {
  ok: boolean;
  mst_root_cid: string | null;
  data: Uint8Array | null;
  error: string | null;
}

interface WireRequest {
  v: typeof PROTOCOL_VERSION;
  op: "anchor_pending" | "anchor_commit" | "health";
  cell_did: string;
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string | null;
  payload: Uint8Array | null;
  meta: Record<string, unknown>;
}

function encode(v: unknown): Uint8Array {
  return msgpackEncode(v, {useBigInt64: true});
}
function decode(b: Uint8Array): unknown {
  return msgpackDecode(b, {useBigInt64: true});
}

/** Send one framed request, receive one framed response. Opens a fresh
 *  connection per call — anchor-cron runs as a short CronJob tick, so
 *  the persistent-connection optimisation in `kotodama` is unnecessary
 *  here. */
async function call(
  socketPath: string,
  req: WireRequest,
  timeoutMs = 30_000
): Promise<WireResponse> {
  const sock: Socket = connect(socketPath);
  return new Promise((resolve, reject) => {
    let buf = Buffer.alloc(0);
    let settled = false;

    const settle = (err: Error | null, res?: WireResponse): void => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      sock.destroy();
      if (err) reject(err);
      else if (res) resolve(res);
    };

    const timer = setTimeout(
      () => settle(new Error(`anchor-cron sidecar call timed out after ${timeoutMs}ms`)),
      timeoutMs
    );

    sock.on("error", (cause) =>
      settle(cause instanceof Error ? cause : new Error(String(cause)))
    );
    sock.on("close", () => {
      if (!settled)
        settle(new Error("anchor-cron sidecar closed before response"));
    });
    sock.on("data", (chunk: Buffer) => {
      buf = Buffer.concat([buf, chunk]);
      if (buf.length < 4) return;
      const len = buf.readUInt32BE(0);
      if (buf.length < 4 + len) return;
      const body = buf.subarray(4, 4 + len);
      const decoded = decode(body);
      if (
        typeof decoded !== "object" ||
        decoded === null ||
        !("ok" in decoded)
      ) {
        settle(new Error("anchor-cron: malformed sidecar response"));
        return;
      }
      settle(null, decoded as WireResponse);
    });

    const body = encode(req);
    const prefix = Buffer.alloc(4);
    prefix.writeUInt32BE(body.length, 0);
    sock.write(Buffer.concat([prefix, Buffer.from(body)]));
  });
}

function envelope(
  op: WireRequest["op"],
  cellDid: string,
  payload?: Uint8Array,
  threadId = "",
  checkpointNs = ""
): WireRequest {
  return {
    v: PROTOCOL_VERSION,
    op,
    cell_did: cellDid,
    thread_id: threadId,
    checkpoint_ns: checkpointNs,
    checkpoint_id: null,
    payload: payload ?? null,
    meta: {},
  };
}

/** List rows that have been IPFS-pinned but not yet anchored. */
export async function anchorPending(
  socketPath: string,
  cellDid: string
): Promise<SaverIndexRow[]> {
  const res = await call(socketPath, envelope("anchor_pending", cellDid));
  if (!res.ok) {
    throw new Error(
      `[anchor-cron] anchor_pending failed: ${res.error ?? "unknown"}`
    );
  }
  if (!res.data) return [];
  const rows = decode(res.data);
  if (!Array.isArray(rows)) {
    throw new Error("[anchor-cron] anchor_pending returned non-array data");
  }
  return rows as SaverIndexRow[];
}

/** Tell the sidecar an anchor tx has landed for one or more checkpoints. */
export async function anchorCommit(
  socketPath: string,
  cellDid: string,
  commits: CommitEntry[]
): Promise<void> {
  if (commits.length === 0) return;
  const payload = encode(commits);
  const res = await call(
    socketPath,
    envelope("anchor_commit", cellDid, payload)
  );
  if (!res.ok) {
    throw new Error(
      `[anchor-cron] anchor_commit failed: ${res.error ?? "unknown"}`
    );
  }
}

/** Sanity ping. Useful at startup. */
export async function health(socketPath: string): Promise<void> {
  const res = await call(socketPath, envelope("health", "_health_"));
  if (!res.ok) {
    throw new Error(`[anchor-cron] sidecar health: ${res.error ?? "unknown"}`);
  }
}
