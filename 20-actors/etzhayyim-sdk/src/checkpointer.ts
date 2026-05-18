/**
 * @etzhayyim/sdk/checkpointer — TypeScript sidecar implementing the
 * LangGraph MstCheckpointSaver wire protocol over a Unix socket.
 *
 * Per ADR-2605171800 (revise) Stages 1-2:
 *   - Python `MstCheckpointSaver` sends msgpack-framed requests here.
 *   - We project each checkpoint payload to an atproto-shaped MST,
 *     build a deterministic CAR, return the root CID synchronously,
 *     and enqueue the CAR for IPFS pin + L2 anchor.
 *
 * All MST / IPFS / viem dependencies stay TS-side per ADR-2605172100
 * ("Substrate client imports | Only via @etzhayyim/sdk").
 */
import {createServer, type Server, type Socket} from "node:net";
import {
  mkdir,
  readFile,
  writeFile,
  rename,
  readdir,
  unlink,
} from "node:fs/promises";
import {existsSync} from "node:fs";
import {dirname, join} from "node:path";
import {homedir} from "node:os";
import {
  encode as msgpackEncode,
  decode as msgpackDecode,
} from "@msgpack/msgpack";
import {
  BlockMap,
  MemoryBlockstore,
  MST,
  blocksToCarFile,
} from "@atproto/repo";

import {pinBlob} from "./ipfs.js";

// ─── Wire protocol (ADR-2605171800 § Stage 1) ───────────────────────

export const PROTOCOL_VERSION = 1 as const;

export type Op =
  | "put"
  | "get_tuple"
  | "list"
  | "put_writes"
  | "anchor_pending"
  | "anchor_commit"
  | "health";

export interface Request {
  v: typeof PROTOCOL_VERSION;
  op: Op;
  cell_did: string;
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string | null;
  payload: Uint8Array | null;
  meta: Record<string, unknown>;
}

export interface Response {
  ok: boolean;
  mst_root_cid: string | null;
  data: Uint8Array | null;
  error: string | null;
}

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

interface AnchorCommitRow {
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string;
  anchor_tx_hash: `0x${string}`;
  anchor_block_number: number;
  anchor_log_index: number;
}

export interface SidecarConfig {
  socketPath?: string;
  stateDir?: string;
  allowedDids: ReadonlySet<string>;
  ipfsApiUrl?: string;
  anchorChainId?: number;
  blobInlineThreshold?: number;
}

const DEFAULTS = {
  socketPath: "/run/etzhayyim/checkpointer.sock",
  stateDir: join(homedir(), ".etzhayyim", "checkpointer"),
  anchorChainId: 8453,
  blobInlineThreshold: 16 * 1024,
} as const;

type ResolvedConfig = Required<Omit<SidecarConfig, "ipfsApiUrl">> &
  Pick<SidecarConfig, "ipfsApiUrl">;

export class CheckpointerSidecar {
  readonly cfg: ResolvedConfig;
  #server?: Server;
  #indexCache = new Map<string, SaverIndexRow>();
  #indexLoaded = false;

  constructor(cfg: SidecarConfig) {
    this.cfg = {
      socketPath: cfg.socketPath ?? DEFAULTS.socketPath,
      stateDir: cfg.stateDir ?? DEFAULTS.stateDir,
      allowedDids: cfg.allowedDids,
      ipfsApiUrl: cfg.ipfsApiUrl,
      anchorChainId: cfg.anchorChainId ?? DEFAULTS.anchorChainId,
      blobInlineThreshold:
        cfg.blobInlineThreshold ?? DEFAULTS.blobInlineThreshold,
    };
  }

  async start(): Promise<void> {
    await mkdir(this.cfg.stateDir, {recursive: true});
    await mkdir(join(this.cfg.stateDir, "queue"), {recursive: true});
    await mkdir(dirname(this.cfg.socketPath), {recursive: true});
    if (existsSync(this.cfg.socketPath)) {
      await unlink(this.cfg.socketPath);
    }
    await this.#loadIndex();
    this.#server = createServer((sock) => this.#handleConnection(sock));
    await new Promise<void>((resolve, reject) => {
      this.#server!.once("error", reject);
      this.#server!.listen(this.cfg.socketPath, () => resolve());
    });
  }

  async stop(): Promise<void> {
    if (!this.#server) return;
    await new Promise<void>((resolve) => this.#server!.close(() => resolve()));
    this.#server = undefined;
  }

  // ─── Connection / framing ─────────────────────────────────────────

  #handleConnection(sock: Socket): void {
    let buf = Buffer.alloc(0);
    sock.on("data", async (chunk: Buffer) => {
      buf = Buffer.concat([buf, chunk]);
      while (buf.length >= 4) {
        const len = buf.readUInt32BE(0);
        if (buf.length < 4 + len) break;
        const frame = buf.subarray(4, 4 + len);
        buf = buf.subarray(4 + len);
        try {
          const req = decode(frame) as Request;
          const res = await this.#dispatch(req);
          this.#writeFrame(sock, res);
        } catch (cause) {
          this.#writeFrame(sock, {
            ok: false,
            mst_root_cid: null,
            data: null,
            error: cause instanceof Error ? cause.message : String(cause),
          });
        }
      }
    });
    sock.on("error", () => sock.destroy());
  }

  #writeFrame(sock: Socket, res: Response): void {
    const out = encode(res);
    const prefix = Buffer.alloc(4);
    prefix.writeUInt32BE(out.length, 0);
    sock.write(Buffer.concat([prefix, Buffer.from(out)]));
  }

  // ─── Op dispatch ──────────────────────────────────────────────────

  async #dispatch(req: Request): Promise<Response> {
    if (req.v !== PROTOCOL_VERSION) {
      return err(`unsupported protocol version ${req.v}`);
    }
    if (req.op === "health") return ok({data: encode({status: "ok"})});
    if (!this.cfg.allowedDids.has(req.cell_did)) {
      return err(`cell_did not provisioned: ${req.cell_did}`);
    }
    switch (req.op) {
      case "put":
        return this.#put(req);
      case "get_tuple":
        return this.#getTuple(req);
      case "list":
        return this.#list(req);
      case "put_writes":
        return this.#putWrites(req);
      case "anchor_pending":
        return this.#anchorPending(req);
      case "anchor_commit":
        return this.#anchorCommit(req);
      default:
        return err(`unknown op: ${req.op as string}`);
    }
  }

  async #put(req: Request): Promise<Response> {
    if (!req.payload || !req.checkpoint_id) {
      return err("put requires payload + checkpoint_id");
    }
    const {rootCid, carBytes, blobCount} = await this.#commitMst(req);
    const row: SaverIndexRow = {
      cell_did: req.cell_did,
      thread_id: req.thread_id,
      checkpoint_ns: req.checkpoint_ns,
      checkpoint_id: req.checkpoint_id,
      mst_root_cid: rootCid,
      car_size_bytes: carBytes.length,
      car_blob_count: blobCount,
      mst_projected_at: Date.now(),
      ipfs_pinned_at: null,
      ipfs_pin_service: null,
      ipfs_pin_id: null,
      anchor_tx_hash: null,
      anchor_block_number: null,
      anchor_log_index: null,
      anchor_chain_id: this.cfg.anchorChainId,
      anchored_at: null,
    };
    await this.#spoolCar(row, carBytes);
    await this.#spoolPayload(row, req.payload);
    this.#indexCache.set(indexKey(row), row);
    await this.#persistIndex();
    void this.#pinSoon(row, carBytes);
    return ok({mst_root_cid: rootCid});
  }

  async #getTuple(req: Request): Promise<Response> {
    const row = req.checkpoint_id
      ? this.#indexCache.get(
          indexKey({
            cell_did: req.cell_did,
            thread_id: req.thread_id,
            checkpoint_ns: req.checkpoint_ns,
            checkpoint_id: req.checkpoint_id,
          })
        )
      : this.#latestFor(req.cell_did, req.thread_id, req.checkpoint_ns);
    if (!row) return ok({data: null});
    const payload = await this.#loadPayload(row);
    return ok({mst_root_cid: row.mst_root_cid, data: payload});
  }

  async #list(req: Request): Promise<Response> {
    const rows = [...this.#indexCache.values()]
      .filter(
        (r) =>
          r.cell_did === req.cell_did &&
          r.thread_id === req.thread_id &&
          r.checkpoint_ns === req.checkpoint_ns
      )
      .sort((a, b) => {
        if (b.mst_projected_at !== a.mst_projected_at) {
          return b.mst_projected_at - a.mst_projected_at;
        }
        return b.checkpoint_id.localeCompare(a.checkpoint_id);
      });
    return ok({data: encode(rows)});
  }

  async #putWrites(req: Request): Promise<Response> {
    // LangGraph pending-writes — fold as a meta-tagged put.
    return this.#put({...req, meta: {...req.meta, kind: "writes"}});
  }

  async #anchorPending(req: Request): Promise<Response> {
    const rows = [...this.#indexCache.values()].filter(
      (r) =>
        r.cell_did === req.cell_did &&
        r.ipfs_pinned_at !== null &&
        r.anchor_tx_hash === null
    );
    return ok({data: encode(rows)});
  }

  async #anchorCommit(req: Request): Promise<Response> {
    if (!req.payload) return err("anchor_commit requires payload");
    const commits = decode(req.payload) as AnchorCommitRow[];
    for (const c of commits) {
      const row = this.#indexCache.get(
        indexKey({
          cell_did: req.cell_did,
          thread_id: c.thread_id,
          checkpoint_ns: c.checkpoint_ns,
          checkpoint_id: c.checkpoint_id,
        })
      );
      if (!row) continue;
      row.anchor_tx_hash = c.anchor_tx_hash;
      row.anchor_block_number = c.anchor_block_number;
      row.anchor_log_index = c.anchor_log_index;
      row.anchored_at = Date.now();
    }
    await this.#persistIndex();
    return ok({});
  }

  // ─── MST commit (determinism contract) ────────────────────────────

  /**
   * Same (cell_did, checkpoint_id, payload bytes) → same rootCid,
   * bit-for-bit. Do NOT introduce non-deterministic sources here.
   */
  async #commitMst(req: Request): Promise<{
    rootCid: string;
    carBytes: Uint8Array;
    blobCount: number;
  }> {
    if (!req.checkpoint_id) throw new Error("commitMst requires checkpoint_id");
    if (!req.payload) throw new Error("commitMst requires payload");
    // Payload is opaque msgpack from the saver. BlockMap.add stores it as
    // dag-cbor; the cast satisfies the typed entry point — the JS impl
    // accepts arbitrary objects identically.
    const payload = decode(req.payload) as Parameters<BlockMap["add"]>[0];
    const blocks = new BlockMap();
    const payloadCid = await blocks.add(payload);
    const payloadBytes = blocks.get(payloadCid);
    if (!payloadBytes)
      throw new Error("BlockMap.add did not retain encoded payload");
    let recordCid = payloadCid;
    let blobCount = 0;
    if (payloadBytes.byteLength > this.cfg.blobInlineThreshold) {
      const ref = {
        $type: "magatama.cell.checkpoint.ref",
        blob: payloadCid,
        checkpoint_id: req.checkpoint_id,
        cell_did: req.cell_did,
        thread_id: req.thread_id,
        checkpoint_ns: req.checkpoint_ns,
      };
      recordCid = await blocks.add(ref);
      blobCount = 1;
    }
    const storage = new MemoryBlockstore();
    await storage.putMany(blocks);
    let mst = await MST.create(storage);
    mst = await mst.add(
      `magatama.cell.checkpoint/${req.checkpoint_id}`,
      recordCid
    );
    const unstored = await mst.getUnstoredBlocks();
    await storage.putMany(unstored.blocks);
    const carBlocks = blocks.addMap(unstored.blocks);
    const rootCid = await mst.getPointer();
    const carBytes = await blocksToCarFile(rootCid, carBlocks);
    return {rootCid: rootCid.toString(), carBytes, blobCount};
  }

  // ─── Spool + index ────────────────────────────────────────────────

  async #spoolCar(row: SaverIndexRow, carBytes: Uint8Array): Promise<void> {
    const dir = join(
      this.cfg.stateDir,
      "queue",
      encodeURIComponent(row.cell_did)
    );
    await mkdir(dir, {recursive: true});
    const path = join(dir, `${row.checkpoint_id}.car`);
    await writeFile(`${path}.tmp`, carBytes);
    await rename(`${path}.tmp`, path);
  }

  async #spoolPayload(row: SaverIndexRow, payload: Uint8Array): Promise<void> {
    const dir = join(
      this.cfg.stateDir,
      "queue",
      encodeURIComponent(row.cell_did)
    );
    const path = join(dir, `${row.checkpoint_id}.payload`);
    await writeFile(`${path}.tmp`, payload);
    await rename(`${path}.tmp`, path);
  }

  async #loadPayload(row: SaverIndexRow): Promise<Uint8Array> {
    const path = join(
      this.cfg.stateDir,
      "queue",
      encodeURIComponent(row.cell_did),
      `${row.checkpoint_id}.payload`
    );
    return new Uint8Array(await readFile(path));
  }

  async #pinSoon(row: SaverIndexRow, carBytes: Uint8Array): Promise<void> {
    if (!this.cfg.ipfsApiUrl) return;
    try {
      const res = await pinBlob(this.cfg.ipfsApiUrl, carBytes);
      row.ipfs_pinned_at = Date.now();
      row.ipfs_pin_service = "local-kubo";
      row.ipfs_pin_id = res.cid;
      await this.#persistIndex();
    } catch (e) {
      console.error("[checkpointer] pin failed (will retry):", e);
    }
  }

  #latestFor(
    cell_did: string,
    thread_id: string,
    checkpoint_ns: string
  ): SaverIndexRow | undefined {
    let best: SaverIndexRow | undefined;
    for (const r of this.#indexCache.values()) {
      if (
        r.cell_did === cell_did &&
        r.thread_id === thread_id &&
        r.checkpoint_ns === checkpoint_ns
      ) {
        if (
          !best ||
          r.mst_projected_at > best.mst_projected_at ||
          (r.mst_projected_at === best.mst_projected_at &&
            r.checkpoint_id.localeCompare(best.checkpoint_id) > 0)
        ) {
          best = r;
        }
      }
    }
    return best;
  }

  async #loadIndex(): Promise<void> {
    const path = join(this.cfg.stateDir, "index.json");
    if (!existsSync(path)) {
      this.#indexLoaded = true;
      return;
    }
    const rows = JSON.parse(await readFile(path, "utf8")) as SaverIndexRow[];
    for (const r of rows) this.#indexCache.set(indexKey(r), r);
    this.#indexLoaded = true;
  }

  async #persistIndex(): Promise<void> {
    if (!this.#indexLoaded) return;
    const path = join(this.cfg.stateDir, "index.json");
    await writeFile(
      `${path}.tmp`,
      JSON.stringify([...this.#indexCache.values()])
    );
    await rename(`${path}.tmp`, path);
  }
}

// ─── msgpack codec ──────────────────────────────────────────────────

export function encode(value: unknown): Uint8Array {
  return msgpackEncode(value, {useBigInt64: true});
}

export function decode(bytes: Uint8Array): unknown {
  return msgpackDecode(bytes, {useBigInt64: true});
}

// ─── Helpers ────────────────────────────────────────────────────────

function indexKey(r: {
  cell_did: string;
  thread_id: string;
  checkpoint_ns: string;
  checkpoint_id: string;
}): string {
  return `${r.cell_did}\x00${r.thread_id}\x00${r.checkpoint_ns}\x00${r.checkpoint_id}`;
}

function ok(partial: Partial<Response> = {}): Response {
  return {
    ok: true,
    mst_root_cid: partial.mst_root_cid ?? null,
    data: partial.data ?? null,
    error: null,
  };
}

function err(message: string): Response {
  return {ok: false, mst_root_cid: null, data: null, error: message};
}

// ─── CLI entrypoint ─────────────────────────────────────────────────

export async function runFromEnv(): Promise<CheckpointerSidecar> {
  const allowed = (process.env.ETZ_CHECKPOINTER_ALLOWED_DIDS ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (allowed.length === 0) {
    throw new Error(
      "ETZ_CHECKPOINTER_ALLOWED_DIDS must list at least one DID"
    );
  }
  const sidecar = new CheckpointerSidecar({
    socketPath: process.env.ETZ_CHECKPOINTER_SOCKET,
    stateDir: process.env.ETZ_CHECKPOINTER_STATE_DIR,
    allowedDids: new Set(allowed),
    ipfsApiUrl: process.env.ETZ_IPFS_API_URL,
    anchorChainId: process.env.ETZ_ANCHOR_CHAIN_ID
      ? Number(process.env.ETZ_ANCHOR_CHAIN_ID)
      : undefined,
  });
  await sidecar.start();
  return sidecar;
}

export const _internal = {readdir};
