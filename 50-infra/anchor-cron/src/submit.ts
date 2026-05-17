export interface SubmitOpts {
  contract: `0x${string}`;
  rpcUrl: string;
  signerKey: string;
  confirmations: number;
  rootHash: `0x${string}`;
  ipfsCid: string;
  batchSize: number;
}

export interface SubmitResult {
  txHash: `0x${string}`;
  blockNumber: bigint;
}

export async function submitAnchor(_opts: SubmitOpts): Promise<SubmitResult> {
  throw new Error(
    "[anchor-cron/submit] TODO: viem walletClient.writeContract({\n" +
      "  address: contract,\n" +
      "  abi: EtzhayyimAnchor ABI,\n" +
      "  functionName: 'anchor',\n" +
      "  args: [rootHash, ipfsCid as bytes, batchSize],\n" +
      "}).\n" +
      "Wait for `confirmations` blocks via publicClient.waitForTransactionReceipt."
  );
}
