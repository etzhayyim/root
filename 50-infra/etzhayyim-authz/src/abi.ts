/**
 * EtzhayyimAuthz contract ABI subset — only the functions and events the
 * XRPC handler reads / encodes. Keep this hand-curated; do not import the
 * full Foundry-generated ABI to avoid pulling 20+ unused entries.
 */
export const ETZHAYYIM_AUTHZ_ABI = [
  // Storage struct used by reads.
  // struct Root {
  //   bytes32 dwebHandleHash;
  //   address activeKey;
  //   address predecessorVendorAddr;
  //   bytes32 predecessorVendorRootHash;
  //   uint96 createdBlock;
  //   uint96 lastRotatedBlock;
  //   bool active;
  // }
  {
    type: "function",
    name: "resolveDwebHandle",
    inputs: [{ name: "dwebHandleHash", type: "bytes32" }],
    outputs: [
      { name: "rootId", type: "bytes32" },
      {
        name: "data",
        type: "tuple",
        components: [
          { name: "dwebHandleHash", type: "bytes32" },
          { name: "activeKey", type: "address" },
          { name: "predecessorVendorAddr", type: "address" },
          { name: "predecessorVendorRootHash", type: "bytes32" },
          { name: "createdBlock", type: "uint96" },
          { name: "lastRotatedBlock", type: "uint96" },
          { name: "active", type: "bool" },
        ],
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "roots",
    inputs: [{ name: "rootId", type: "bytes32" }],
    outputs: [
      { name: "dwebHandleHash", type: "bytes32" },
      { name: "activeKey", type: "address" },
      { name: "predecessorVendorAddr", type: "address" },
      { name: "predecessorVendorRootHash", type: "bytes32" },
      { name: "createdBlock", type: "uint96" },
      { name: "lastRotatedBlock", type: "uint96" },
      { name: "active", type: "bool" },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "isActive",
    inputs: [{ name: "rootId", type: "bytes32" }],
    outputs: [{ type: "bool" }],
    stateMutability: "view",
  },
  // Mutations (used for encoding Council Safe proposal calldata only;
  // the Worker never submits these directly).
  {
    type: "function",
    name: "provisionRoot",
    inputs: [
      { name: "dwebHandleHash", type: "bytes32" },
      { name: "activeKey", type: "address" },
    ],
    outputs: [{ name: "rootId", type: "bytes32" }],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "mirrorVendorRoot",
    inputs: [
      { name: "dwebHandleHash", type: "bytes32" },
      { name: "newActiveKey", type: "address" },
      { name: "predecessorVendorRootHash", type: "bytes32" },
      { name: "predecessorVendorAddr", type: "address" },
    ],
    outputs: [{ name: "rootId", type: "bytes32" }],
    stateMutability: "nonpayable",
  },
  // Events used by getProvenance event scan (Phase α P1 follow-up).
  {
    type: "event",
    name: "RootProvisioned",
    inputs: [
      { name: "rootId", type: "bytes32", indexed: true },
      { name: "dwebHandleHash", type: "bytes32", indexed: true },
      { name: "activeKey", type: "address", indexed: false },
    ],
  },
  {
    type: "event",
    name: "VendorRootMirrored",
    inputs: [
      { name: "rootId", type: "bytes32", indexed: true },
      { name: "predecessorVendorRootHash", type: "bytes32", indexed: true },
      { name: "predecessorVendorAddr", type: "address", indexed: false },
    ],
  },
  {
    type: "event",
    name: "RootKeyRotated",
    inputs: [
      { name: "rootId", type: "bytes32", indexed: true },
      { name: "oldKey", type: "address", indexed: false },
      { name: "newKey", type: "address", indexed: false },
    ],
  },
] as const;
