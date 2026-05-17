/**
 * Emit mstRoot records. After a shard flush, the projector publishes
 * an AT record under its own DID announcing the new root CID for that
 * shard. Downstream (ipfs-pinner + anchor-cron) subscribes to these.
 */

export interface MstRootEmitOpts {
  did: string;
  shardKey: string;
  rootCid: string;
  carPath: string;
}

export async function emitMstRoot(_opts: MstRootEmitOpts): Promise<void> {
  throw new Error(
    "[mst-projector/emit] emitMstRoot TODO: AtpAgent.com.atproto.repo.createRecord " +
      "with collection=ai.gftd.apps.substrate.mstRoot, body={shardKey, rootCid, " +
      "carPath, recordCount, byteSize, flushedAt}."
  );
}
