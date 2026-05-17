export async function pinata(
  _carPath: string
): Promise<{ cid: string; receipt: unknown }> {
  throw new Error(
    "[ipfs-pinner/pinata] TODO: read CAR file, POST to api.pinata.cloud/pinning/pinFileToIPFS " +
      "with Bearer ETZ_PINATA_JWT, parse IpfsHash from response."
  );
}
