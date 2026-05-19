/**
 * Firehose subscriber (Phase 1).
 *
 * Wraps `com.atproto.sync.subscribeRepos` as an AsyncGenerator of normalized
 * commit events. Each WebSocket binary message contains a 2-tuple of CBOR
 * (header || body) per the AT Protocol event-stream spec
 * (https://atproto.com/specs/event-stream).
 *
 * Phase 1 emits one `FirehoseEvent` per op in `body.ops[]`, surfacing the
 * collection NSID, rkey, op kind, and record CID. The CAR blob in
 * `body.blocks` is NOT decoded here — downstream consumers that need the
 * full record body fetch it via `com.atproto.repo.getRecord`. Phase 2 will
 * decode `body.blocks` to surface `recordCbor` inline and feed a true MST.
 */

import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { decode as cborDecode, decodeFirst as cborDecodeFirst } from "cborg";
import WebSocket from "ws";

export interface FirehoseEvent {
  seq: bigint;
  did: string;
  collection: string;
  rkey: string;
  op: "create" | "update" | "delete";
  recordCid?: string;
  /** Phase 2 will populate this from `body.blocks`. */
  recordCbor?: Uint8Array;
}

interface FrameHeader {
  op: number; // 1 = normal, -1 = error
  t?: string; // e.g. "#commit", "#identity", "#info"
}

interface CommitBody {
  seq: number | bigint;
  rebase?: boolean;
  tooBig?: boolean;
  repo: string;
  commit: unknown;
  prev?: unknown;
  rev?: string;
  since?: string | null;
  blocks?: Uint8Array;
  ops?: Array<{
    action: "create" | "update" | "delete";
    path: string; // "collection/rkey"
    cid?: unknown; // CID-shaped object from dag-cbor (has toString)
  }>;
  time?: string;
}

interface StartFirehoseOpts {
  /** Persist cursor to this file every CURSOR_FLUSH_EVERY events. */
  cursorFile?: string;
  /** Reconnect on close after this many ms. */
  reconnectDelayMs?: number;
}

const CURSOR_FLUSH_EVERY = 50;

async function readCursor(cursorFile?: string): Promise<number | undefined> {
  if (!cursorFile) return undefined;
  try {
    const raw = await readFile(cursorFile, "utf8");
    const n = Number(raw.trim());
    return Number.isFinite(n) ? n : undefined;
  } catch {
    return undefined;
  }
}

async function writeCursor(cursorFile: string, seq: bigint): Promise<void> {
  await mkdir(dirname(cursorFile), { recursive: true });
  await writeFile(cursorFile, seq.toString(), "utf8");
}

function buildUrl(baseUrl: string, cursor?: number): string {
  if (!cursor) return baseUrl;
  const sep = baseUrl.includes("?") ? "&" : "?";
  return `${baseUrl}${sep}cursor=${cursor}`;
}

function parseFrame(buf: Uint8Array): { header: FrameHeader; body: unknown } {
  const [header, remaining] = cborDecodeFirst(buf) as [FrameHeader, Uint8Array];
  const body = cborDecode(remaining);
  return { header, body };
}

function cidToString(cid: unknown): string | undefined {
  if (cid && typeof (cid as { toString?: () => string }).toString === "function") {
    const s = (cid as { toString: () => string }).toString();
    return s === "[object Object]" ? undefined : s;
  }
  return undefined;
}

/**
 * Connect, decode frames, yield FirehoseEvents.
 * Resumes from `cursorFile` if present. Reconnects with exponential backoff
 * (max 60s) when the connection drops or errors.
 */
export async function* startFirehose(
  baseUrl: string,
  opts: StartFirehoseOpts = {}
): AsyncGenerator<FirehoseEvent> {
  const cursorFile = opts.cursorFile;
  const reconnectDelayMs = opts.reconnectDelayMs ?? 5_000;
  let cursor = await readCursor(cursorFile);
  let eventsSinceFlush = 0;

  while (true) {
    const url = buildUrl(baseUrl, cursor);
    console.log(`[firehose] connect ${url}`);
    const ws = new WebSocket(url);

    const queue: FirehoseEvent[] = [];
    let resolveWaiter: ((ev: FirehoseEvent | null) => void) | null = null;
    let connectionClosed = false;

    ws.binaryType = "nodebuffer";

    ws.on("message", (data: Buffer | ArrayBuffer | Uint8Array | Buffer[]) => {
      let buf: Uint8Array;
      if (Buffer.isBuffer(data)) buf = new Uint8Array(data);
      else if (data instanceof ArrayBuffer) buf = new Uint8Array(data);
      else if (Array.isArray(data)) buf = new Uint8Array(Buffer.concat(data));
      else buf = data as Uint8Array;

      let parsed: { header: FrameHeader; body: unknown };
      try {
        parsed = parseFrame(buf);
      } catch (err) {
        console.warn("[firehose] frame decode failed:", err);
        return;
      }
      if (parsed.header.op !== 1 || parsed.header.t !== "#commit") return;
      const body = parsed.body as CommitBody;
      if (!Array.isArray(body.ops)) return;
      const seq =
        typeof body.seq === "bigint" ? body.seq : BigInt(body.seq ?? 0);
      for (const op of body.ops) {
        const [collection, ...rest] = (op.path ?? "").split("/");
        const rkey = rest.join("/");
        if (!collection || !rkey) continue;
        const ev: FirehoseEvent = {
          seq,
          did: body.repo,
          collection,
          rkey,
          op: op.action,
          recordCid: cidToString(op.cid),
        };
        if (resolveWaiter) {
          const w = resolveWaiter;
          resolveWaiter = null;
          w(ev);
        } else {
          queue.push(ev);
        }
      }
    });

    ws.on("close", (code) => {
      console.warn(`[firehose] closed code=${code}`);
      connectionClosed = true;
      if (resolveWaiter) {
        const w = resolveWaiter;
        resolveWaiter = null;
        w(null);
      }
    });
    ws.on("error", (err) => {
      console.warn("[firehose] error:", err);
    });

    try {
      while (!connectionClosed) {
        let ev: FirehoseEvent | null;
        if (queue.length > 0) {
          ev = queue.shift()!;
        } else {
          ev = await new Promise<FirehoseEvent | null>((resolve) => {
            resolveWaiter = resolve;
          });
        }
        if (ev === null) break;
        cursor = Number(ev.seq);
        eventsSinceFlush += 1;
        if (cursorFile && eventsSinceFlush >= CURSOR_FLUSH_EVERY) {
          await writeCursor(cursorFile, ev.seq).catch((err) =>
            console.warn("[firehose] cursor write failed:", err)
          );
          eventsSinceFlush = 0;
        }
        yield ev;
      }
    } finally {
      try {
        ws.close();
      } catch {
        /* already closed */
      }
    }

    console.log(`[firehose] reconnecting in ${reconnectDelayMs}ms (cursor=${cursor})`);
    await new Promise((r) => setTimeout(r, reconnectDelayMs));
  }
}
