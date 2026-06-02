/**
 * @etzhayyim/sdk-mock
 *
 * In-memory mock implementation of the Etzhayyim SDK for testing
 * rw-free reference implementations without PDS/IPFS/L2 dependencies.
 *
 * Simulates:
 * - `write<T>(params)` → persists to in-memory store, returns URI
 * - `read<T>(params)` → retrieves with optional pagination
 * - Collection namespace isolation
 * - Record ordering by insertion sequence (TID-like ordering)
 *
 * Usage:
 * ```ts
 * const mock = new MockEtzhayyim({ did: "did:web:example.com" });
 * await mock.write({ collection: "com.etzhayyim.apps.example.record", record: {...}, rkey: "key-1" });
 * const result = await mock.read({ collection: "com.etzhayyim.apps.example.record", rkey: "key-1" });
 * ```
 */

export interface MockReadResult<T> {
  records: Array<{ uri: string; value: T }>;
  cursor?: string;
}

export interface MockWriteReceipt {
  uri: string;
}

export interface MockReadParams {
  collection: string;
  rkey?: string;
  cursor?: string;
  limit?: number;
}

export interface MockWriteParams<T = unknown> {
  collection: string;
  record: T;
  rkey: string;
}

/**
 * In-memory Etzhayyim SDK mock.
 *
 * Stores records in nested maps: collection → rkey → { uri, value, writtenAt, seq }.
 * Pagination is ordered by insertion sequence (ascending).
 * Idempotent writes (same collection + rkey) overwrite the previous value.
 */
export class MockEtzhayyim {
  public did: string;
  /** collection → rkey → { uri, value, writtenAt, seq } */
  private store = new Map<
    string,
    Map<string, { uri: string; value: unknown; writtenAt: number; seq: bigint }>
  >();
  private nextSeq = 1n;

  constructor(opts: { did: string }) {
    this.did = opts.did;
  }

  /**
   * Write (create or update) a record.
   * Returns the AT URI in format: at://{did}/{collection}/{rkey}
   */
  async write<T>(params: MockWriteParams<T>): Promise<MockWriteReceipt> {
    let col = this.store.get(params.collection);
    if (!col) {
      col = new Map();
      this.store.set(params.collection, col);
    }
    const uri = `at://${this.did}/${params.collection}/${params.rkey}`;
    const seq = this.nextSeq++;
    col.set(params.rkey, { uri, value: params.record, writtenAt: Date.now(), seq });
    return { uri };
  }

  /**
   * Read records from a collection.
   *
   * If `rkey` is supplied, fetch that single record only.
   * Otherwise, list all records ordered by insertion sequence (ascending),
   * with optional cursor (encoded as the rkey of the last item) and limit.
   */
  async read<T>(params: MockReadParams): Promise<MockReadResult<T>> {
    const col = this.store.get(params.collection);
    if (!col) return { records: [] };

    // Single record fetch
    if (params.rkey) {
      const r = col.get(params.rkey);
      if (!r) return { records: [] };
      return { records: [{ uri: r.uri, value: r.value as T }] };
    }

    // List path: sort by insertion sequence (ascending), apply cursor and limit.
    const all = [...col.values()].sort((a, b) => {
      if (a.seq < b.seq) return -1;
      if (a.seq > b.seq) return 1;
      return 0;
    });

    let startIdx = 0;
    if (params.cursor) {
      // Cursor is the rkey of the last item in the previous page.
      // Find it and start after it.
      const cursorRkey = params.cursor;
      const foundIdx = [...col.entries()].findIndex(
        ([rkey]) => rkey === cursorRkey
      );
      if (foundIdx >= 0) {
        // Find the position in the sorted array
        const foundRecord = col.get(cursorRkey);
        const sortedIdx = all.findIndex((r) => r.seq === foundRecord!.seq);
        startIdx = sortedIdx >= 0 ? sortedIdx + 1 : 0;
      }
    }

    const limit = params.limit ?? 50;
    const page = all.slice(startIdx, startIdx + limit);
    const nextCursor =
      page.length === limit && startIdx + limit < all.length
        ? ([...col.entries()].find(([, r]) => r.seq === all[startIdx + limit]?.seq)?.[0] ?? undefined)
        : undefined;

    return {
      records: page.map((r) => ({ uri: r.uri, value: r.value as T })),
      cursor: nextCursor,
    };
  }

  /**
   * Test helper: dump all records in a collection in insertion order.
   */
  dump(collection: string): unknown[] {
    const col = this.store.get(collection);
    if (!col) return [];
    return [...col.values()]
      .sort((a, b) => {
        if (a.seq < b.seq) return -1;
        if (a.seq > b.seq) return 1;
        return 0;
      })
      .map((r) => r.value);
  }

  /**
   * Test helper: get record count in a collection.
   */
  count(collection: string): number {
    return this.store.get(collection)?.size ?? 0;
  }

  /**
   * Test helper: reset all collections and sequence counter.
   */
  clear(): void {
    this.store.clear();
    this.nextSeq = 1n;
  }
}
