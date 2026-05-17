export async function kubo(
  _carPath: string
): Promise<{ cid: string; receipt: unknown }> {
  throw new Error(
    "[ipfs-pinner/kubo] TODO: POST CAR to ETZ_KUBO_API /api/v0/dag/import, " +
      "follow with /api/v0/pin/add for the root CID."
  );
}
