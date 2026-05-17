export async function web3storage(
  _carPath: string
): Promise<{ cid: string; receipt: unknown }> {
  throw new Error(
    "[ipfs-pinner/web3storage] TODO: use @web3-storage/w3up-client with " +
      "ETZ_WEB3STORAGE_TOKEN, uploadCar(carPath)."
  );
}
