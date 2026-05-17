/**
 * @etzhayyim/sdk/l2 — Base L2 anchor helpers.
 *
 * Status: scaffold. Stubs only. See ADR-2605172000.
 */

/**
 * Submit a batched MST root anchor to the anchor contract on Base L2.
 * Returns the txHash on inclusion.
 */
export async function anchorMstRoot(
  _l2RpcUrl: string,
  _contract: `0x${string}`,
  _rootCid: string,
  _signer: unknown
): Promise<{ txHash: `0x${string}`; blockNumber: bigint }> {
  throw new Error(
    "[etzhayyim-sdk/l2] anchorMstRoot() TODO: viem walletClient.writeContract, " +
      "function anchor(bytes32 rootCidHash), wait for receipt."
  );
}

/**
 * Look up which L2 anchor tx contains a given MST root, or null if
 * not yet anchored.
 */
export async function findAnchorForRoot(
  _l2RpcUrl: string,
  _contract: `0x${string}`,
  _rootCid: string
): Promise<{ txHash: `0x${string}`; blockNumber: bigint } | null> {
  throw new Error(
    "[etzhayyim-sdk/l2] findAnchorForRoot() TODO: viem publicClient " +
      "getLogs({ contract, event: 'Anchored(bytes32)', args: { rootCidHash } })"
  );
}
