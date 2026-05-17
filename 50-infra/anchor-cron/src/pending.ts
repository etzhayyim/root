export interface PendingRoot {
  mstRootUri: string;       // AT URI of the source mstRoot record
  rootHash: `0x${string}`;  // sha256 of ipfsCid bytes
  ipfsCid: string;          // multibase-encoded CID
  batchSize: number;
}

export async function readPending(_opts: { limit: number }): Promise<PendingRoot[]> {
  throw new Error(
    "[anchor-cron/pending] TODO: query PDS for ai.gftd.apps.substrate.mstRoot " +
      "records that have a matching ipfsPin but no matching anchored record yet. " +
      "Compute rootHash = sha256(ipfsCid as bytes)."
  );
}
