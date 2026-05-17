export interface EmitOpts {
  did: string;
  mstRootUri: string;
  txHash: `0x${string}`;
  blockNumber: bigint;
}

export async function emitAnchoredReceipt(_opts: EmitOpts): Promise<void> {
  throw new Error(
    "[anchor-cron/emit] TODO: AtpAgent.createRecord under " +
      "ai.gftd.apps.substrate.anchored with {mstRootUri, txHash, blockNumber, anchoredAt}."
  );
}
