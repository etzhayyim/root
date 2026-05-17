/**
 * @etzhayyim/sdk/ipfs — IPFS pin/fetch helpers.
 *
 * Status: scaffold. Stubs only. See ADR-2605172000.
 */

/** Pin a blob to IPFS via the configured API. Returns CID. */
export async function pinBlob(
  _apiUrl: string,
  _blob: Blob
): Promise<string> {
  throw new Error(
    "[etzhayyim-sdk/ipfs] pinBlob() TODO: POST to apiUrl /api/v0/add " +
      "with multipart/form-data, parse {Hash} response."
  );
}

/** Fetch a blob from IPFS via the configured gateway. */
export async function fetchBlob(
  _gatewayUrl: string,
  _cid: string
): Promise<Blob> {
  throw new Error(
    "[etzhayyim-sdk/ipfs] fetchBlob() TODO: GET gatewayUrl /ipfs/<cid>, " +
      "return as Blob with content-type."
  );
}
