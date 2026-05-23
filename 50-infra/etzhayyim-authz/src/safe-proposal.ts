import { encodeFunctionData, type Address, type Hex } from "viem";
import { ETZHAYYIM_AUTHZ_ABI } from "./abi";

/**
 * Build the encoded payload a Council Safe operator pastes into the
 * https://app.safe.global UI "Contract interaction" form.
 *
 * The Worker never submits this transaction itself — Council multisig
 * authority is the SoT. We return all the values the operator needs to
 * propose the transaction in Safe UI per docs/council-multisig-sop.md.
 */

export interface SafeProposal {
  /** Target contract — always EtzhayyimAuthz. */
  to: Address;
  /** ABI-encoded function call. */
  data: Hex;
  /** Always 0 (no ETH transfer). */
  value: "0";
  /** Function name being called, for human readability in Safe UI. */
  method: "provisionRoot" | "mirrorVendorRoot" | "deactivateRoot";
  /** Decoded args, for human readability in Safe UI / audit log. */
  args: Record<string, string>;
  /** Council Safe address (from env). */
  councilSafe: Address;
  /** Chain id for the target network. */
  chainId: number;
  /** Safe UI deep link to pre-fill the proposal (best-effort; falls
   *  back to "open Safe and paste data" SOP if not supported). */
  safeUiUrl: string;
}

export function buildProvisionRootProposal(args: {
  authzContractAddress: Address;
  councilSafe: Address;
  chainId: number;
  dwebHandleHash: Hex;
  activeKey: Address;
}): SafeProposal {
  const data = encodeFunctionData({
    abi: ETZHAYYIM_AUTHZ_ABI,
    functionName: "provisionRoot",
    args: [args.dwebHandleHash, args.activeKey],
  });
  return {
    to: args.authzContractAddress,
    data,
    value: "0",
    method: "provisionRoot",
    args: {
      dwebHandleHash: args.dwebHandleHash,
      activeKey: args.activeKey,
    },
    councilSafe: args.councilSafe,
    chainId: args.chainId,
    safeUiUrl: `https://app.safe.global/transactions/queue?safe=${chainPrefix(args.chainId)}:${args.councilSafe}`,
  };
}

export function buildMirrorVendorRootProposal(args: {
  authzContractAddress: Address;
  councilSafe: Address;
  chainId: number;
  dwebHandleHash: Hex;
  newActiveKey: Address;
  predecessorVendorRootHash: Hex;
  predecessorVendorAddr: Address;
}): SafeProposal {
  const data = encodeFunctionData({
    abi: ETZHAYYIM_AUTHZ_ABI,
    functionName: "mirrorVendorRoot",
    args: [
      args.dwebHandleHash,
      args.newActiveKey,
      args.predecessorVendorRootHash,
      args.predecessorVendorAddr,
    ],
  });
  return {
    to: args.authzContractAddress,
    data,
    value: "0",
    method: "mirrorVendorRoot",
    args: {
      dwebHandleHash: args.dwebHandleHash,
      newActiveKey: args.newActiveKey,
      predecessorVendorRootHash: args.predecessorVendorRootHash,
      predecessorVendorAddr: args.predecessorVendorAddr,
    },
    councilSafe: args.councilSafe,
    chainId: args.chainId,
    safeUiUrl: `https://app.safe.global/transactions/queue?safe=${chainPrefix(args.chainId)}:${args.councilSafe}`,
  };
}

function chainPrefix(chainId: number): string {
  switch (chainId) {
    case 8453:
      return "base";
    case 84532:
      return "basesep";
    default:
      return String(chainId);
  }
}
