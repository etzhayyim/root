/**
 * In-memory MST per shard. apply/lookup/root.
 *
 * MST shape follows AT Protocol spec
 * (https://atproto.com/specs/repository#data-structure). Uses base32 keys
 * (collection-prefixed) and dag-cbor leaf encoding.
 */

import type { FirehoseEvent } from "./firehose.js";

export function applyCommit(_shardKey: string, _ev: FirehoseEvent): void {
  throw new Error(
    "[mst-projector/mst] applyCommit TODO: insert/update/delete on the " +
      "per-shard MST tree. Use @atproto/repo's MST helpers."
  );
}

export function currentRoot(_shardKey: string): string {
  throw new Error(
    "[mst-projector/mst] currentRoot TODO: return CIDv1 of the MST root node."
  );
}
