export async function filecoin(
  _carPath: string
): Promise<{ cid: string; receipt: unknown }> {
  throw new Error(
    "[ipfs-pinner/filecoin] TODO: use Storacha / @web3-storage/w3up-client " +
      "with ETZ_STORACHA_DID, upload CAR, wait for Filecoin deal proposal acceptance."
  );
}
