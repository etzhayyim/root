import { createPublicClient, http, type Address, type Hex } from "viem";
import { base, baseSepolia } from "viem/chains";
import { ETZHAYYIM_AUTHZ_ABI } from "./abi";

export interface ChainConfig {
  contractAddress: Address;
  rpcUrl: string;
  chainId: number;
}

export function loadChainConfig(env: {
  AUTHZ_CONTRACT_ADDRESS?: string;
  BASE_RPC_URL?: string;
  CHAIN_ID?: string;
}): ChainConfig | null {
  const addr = env.AUTHZ_CONTRACT_ADDRESS;
  const rpc = env.BASE_RPC_URL;
  const chainIdStr = env.CHAIN_ID;
  if (!addr || !/^0x[0-9a-fA-F]{40}$/.test(addr)) return null;
  if (!rpc) return null;
  if (!chainIdStr) return null;
  const chainId = Number.parseInt(chainIdStr, 10);
  if (!Number.isFinite(chainId)) return null;
  return { contractAddress: addr as Address, rpcUrl: rpc, chainId };
}

function client(cfg: ChainConfig) {
  const chain = cfg.chainId === 8453 ? base : baseSepolia;
  return createPublicClient({ chain, transport: http(cfg.rpcUrl) });
}

export interface OnChainRoot {
  dwebHandleHash: Hex;
  activeKey: Address;
  predecessorVendorAddr: Address;
  predecessorVendorRootHash: Hex;
  createdBlock: bigint;
  lastRotatedBlock: bigint;
  active: boolean;
}

const ZERO_BYTES32 = "0x0000000000000000000000000000000000000000000000000000000000000000" as const;
const ZERO_ADDR = "0x0000000000000000000000000000000000000000" as const;

function rootExists(r: OnChainRoot): boolean {
  // Created block 0 means storage default → root does not exist. Block numbers
  // in EtzhayyimAuthz are always positive at provision time.
  return r.createdBlock !== 0n;
}

export async function resolveByDwebHash(
  cfg: ChainConfig,
  dwebHandleHash: Hex,
): Promise<{ rootId: Hex; data: OnChainRoot } | null> {
  const c = client(cfg);
  const result = (await c.readContract({
    address: cfg.contractAddress,
    abi: ETZHAYYIM_AUTHZ_ABI,
    functionName: "resolveDwebHandle",
    args: [dwebHandleHash],
  })) as readonly [Hex, {
    dwebHandleHash: Hex;
    activeKey: Address;
    predecessorVendorAddr: Address;
    predecessorVendorRootHash: Hex;
    createdBlock: bigint;
    lastRotatedBlock: bigint;
    active: boolean;
  }];
  const rootId = result[0];
  const data: OnChainRoot = {
    dwebHandleHash: result[1].dwebHandleHash,
    activeKey: result[1].activeKey,
    predecessorVendorAddr: result[1].predecessorVendorAddr,
    predecessorVendorRootHash: result[1].predecessorVendorRootHash,
    createdBlock: result[1].createdBlock,
    lastRotatedBlock: result[1].lastRotatedBlock,
    active: result[1].active,
  };
  if (rootId === ZERO_BYTES32 || !rootExists(data)) return null;
  return { rootId, data };
}

export async function getRootById(
  cfg: ChainConfig,
  rootId: Hex,
): Promise<OnChainRoot | null> {
  const c = client(cfg);
  const result = (await c.readContract({
    address: cfg.contractAddress,
    abi: ETZHAYYIM_AUTHZ_ABI,
    functionName: "roots",
    args: [rootId],
  })) as readonly [Hex, Address, Address, Hex, bigint, bigint, boolean];
  const data: OnChainRoot = {
    dwebHandleHash: result[0],
    activeKey: result[1],
    predecessorVendorAddr: result[2],
    predecessorVendorRootHash: result[3],
    createdBlock: result[4],
    lastRotatedBlock: result[5],
    active: result[6],
  };
  if (!rootExists(data)) return null;
  return data;
}

export function isZeroAddress(a: Address | string): boolean {
  return a.toLowerCase() === ZERO_ADDR;
}

export function isZeroBytes32(b: Hex | string): boolean {
  return b.toLowerCase() === ZERO_BYTES32;
}
