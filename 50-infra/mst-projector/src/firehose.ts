/**
 * Firehose subscriber. Wraps com.atproto.sync.subscribeRepos as an
 * AsyncGenerator of normalized commit events.
 */

export interface FirehoseEvent {
  seq: bigint;
  did: string;
  collection: string;
  rkey: string;
  op: "create" | "update" | "delete";
  recordCid?: string;
  recordCbor?: Uint8Array;
}

export async function* startFirehose(_url: string): AsyncGenerator<FirehoseEvent> {
  throw new Error(
    "[mst-projector/firehose] TODO: open WebSocket to subscribeRepos, " +
      "decode CBOR commit frames, yield FirehoseEvent. Persist cursor every N events."
  );
  // unreachable — keeps TS happy
  yield {} as FirehoseEvent;
}
