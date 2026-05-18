/**
 * In-process mock checkpointer sidecar — TCP-on-localhost flavour.
 *
 * Speaks the same 4-byte big-endian length-prefix + msgpack envelope
 * declared in ADR-2605171800 §Stage 1, so anchor-cron's sidecarClient
 * can talk to it unmodified. Records every received request so tests
 * can assert on the wire payload.
 *
 * sidecarClient currently `connect(socketPath)`s a Unix domain socket
 * by default. For tests we point its `socketPath` at the temp Unix
 * socket this mock binds to.
 */
import {createServer, type Server, type Socket} from "node:net";
import {tmpdir} from "node:os";
import {mkdtempSync, rmSync} from "node:fs";
import {join} from "node:path";
import {
  encode as msgpackEncode,
  decode as msgpackDecode,
} from "@msgpack/msgpack";

import type {CommitEntry, SaverIndexRow} from "../src/sidecarClient.js";

const PROTOCOL_VERSION = 1 as const;

export interface MockResponse {
  ok: boolean;
  mst_root_cid?: string | null;
  data?: Uint8Array | null;
  error?: string | null;
}

export type Handler = (
  req: Record<string, unknown>,
  ctx: MockSidecar,
) => MockResponse | Promise<MockResponse>;

export class MockSidecar {
  socketPath: string;
  requests: Array<Record<string, unknown>> = [];
  pendingRows: SaverIndexRow[] = [];
  commits: CommitEntry[] = [];

  #server?: Server;
  #handlers: Record<string, Handler> = {};
  #tmp: string;
  #failNextOp: string | null = null;

  constructor() {
    this.#tmp = mkdtempSync(join(tmpdir(), "etz-anchor-cron-mock-"));
    this.socketPath = join(this.#tmp, "sidecar.sock");
    this.#installDefaultHandlers();
  }

  async start(): Promise<void> {
    this.#server = createServer((sock) => this.#handle(sock));
    await new Promise<void>((resolve) => {
      this.#server!.listen(this.socketPath, () => resolve());
    });
  }

  async stop(): Promise<void> {
    if (!this.#server) return;
    await new Promise<void>((resolve) =>
      this.#server!.close(() => resolve()),
    );
    this.#server = undefined;
    try {
      rmSync(this.#tmp, {recursive: true, force: true});
    } catch {
      /* best-effort */
    }
  }

  /** Make the next call to `op` return ok=false with the given error. */
  failNext(op: string, error = "injected failure"): void {
    this.#failNextOp = op;
    this.#errorMessage = error;
  }
  #errorMessage = "injected failure";

  /** Override the handler for an op. Use sparingly in tests. */
  on(op: string, handler: Handler): void {
    this.#handlers[op] = handler;
  }

  // ── private ─────────────────────────────────────────────────────────────

  #installDefaultHandlers(): void {
    this.#handlers.health = () => ({ok: true});

    this.#handlers.anchor_pending = (_req, ctx) => ({
      ok: true,
      data: msgpackEncode(ctx.pendingRows),
    });

    this.#handlers.anchor_commit = (req, ctx) => {
      const payload = req.payload;
      if (payload instanceof Uint8Array) {
        const arr = msgpackDecode(payload) as CommitEntry[];
        ctx.commits.push(...arr);
      }
      return {ok: true};
    };
  }

  #handle(sock: Socket): void {
    let buf = Buffer.alloc(0);
    sock.on("data", async (chunk: Buffer) => {
      buf = Buffer.concat([buf, chunk]);
      while (buf.length >= 4) {
        const len = buf.readUInt32BE(0);
        if (buf.length < 4 + len) break;
        const frame = buf.subarray(4, 4 + len);
        buf = buf.subarray(4 + len);
        const req = msgpackDecode(frame) as Record<string, unknown>;
        this.requests.push(req);
        const op = String(req.op);
        let res: MockResponse;
        if (op === this.#failNextOp) {
          this.#failNextOp = null;
          res = {ok: false, error: this.#errorMessage};
        } else if (this.#handlers[op]) {
          res = await this.#handlers[op](req, this);
        } else {
          res = {ok: false, error: `unknown op ${op}`};
        }
        this.#writeFrame(sock, res);
      }
    });
    sock.on("error", () => sock.destroy());
  }

  #writeFrame(sock: Socket, res: MockResponse): void {
    const out = msgpackEncode({
      ok: res.ok,
      mst_root_cid: res.mst_root_cid ?? null,
      data: res.data ?? null,
      error: res.error ?? null,
    });
    const prefix = Buffer.alloc(4);
    prefix.writeUInt32BE(out.length, 0);
    sock.write(Buffer.concat([prefix, Buffer.from(out)]));
  }
}

export function makeIndexRow(over: Partial<SaverIndexRow> = {}): SaverIndexRow {
  return {
    cell_did: "did:test:cell",
    thread_id: "t-1",
    checkpoint_ns: "",
    checkpoint_id: "ckp001",
    mst_root_cid: "bafy-test-cid",
    car_size_bytes: 1024,
    car_blob_count: 0,
    mst_projected_at: Date.now(),
    ipfs_pinned_at: Date.now(),
    ipfs_pin_service: "local-kubo",
    ipfs_pin_id: "bafy-test-cid",
    anchor_tx_hash: null,
    anchor_block_number: null,
    anchor_log_index: null,
    anchor_chain_id: 8453,
    anchored_at: null,
    ...over,
  };
}

// Unused PROTOCOL_VERSION reference to keep parity with sidecarClient.
void PROTOCOL_VERSION;
