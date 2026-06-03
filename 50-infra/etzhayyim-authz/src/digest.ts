import { encodeAbiParameters, keccak256, toBytes, type Address, type Hex, concat } from "viem";

/**
 * Off-chain provisioning digest — issued by beginRootProvision, signed by
 * the activeKey holder, verified by completeRootProvision. The shape is
 * NOT the same as the on-chain rotation digest (provisionRoot is Council-
 * only on-chain, so the contract does not verify a user signature).
 *
 * inner = keccak256(abi.encode(
 *           "etzhayyim-authz-provision",
 *           chainId,
 *           authzContractAddress,
 *           dwebHandleHash,
 *           activeKey,
 *           nonceBytes32
 *         ))
 * digest = keccak256("\x19Ethereum Signed Message:\n32" || inner)
 */
export function provisionDigest(args: {
  chainId: number;
  authzContractAddress: Address;
  dwebHandleHash: Hex;
  activeKey: Address;
  nonce: Hex;
}): Hex {
  const inner = keccak256(
    encodeAbiParameters(
      [
        { type: "string" },
        { type: "uint256" },
        { type: "address" },
        { type: "bytes32" },
        { type: "address" },
        { type: "bytes32" },
      ],
      [
        "etzhayyim-authz-provision",
        BigInt(args.chainId),
        args.authzContractAddress,
        args.dwebHandleHash,
        args.activeKey,
        args.nonce,
      ],
    ),
  );
  return keccak256(concat([toBytes("\x19Ethereum Signed Message:\n32"), toBytes(inner)]));
}

/**
 * Vendor continuity proof digest — signed by the vendor key (predecessorVendorAddr)
 * to attest that the new etzhayyim activeKey is the legitimate successor.
 *
 * inner = keccak256("etzhayyim-vendor-continuity" || vendorRootDid || dwebHandleHash || newActiveKey)
 * digest = keccak256("\x19Ethereum Signed Message:\n32" || inner)
 *
 * The vendorRootDid is a string (e.g. "did:erc725:etzhayyim:260425:0x..."), encoded as UTF-8 bytes.
 */
export function vendorContinuityDigest(args: {
  vendorRootDid: string;
  dwebHandleHash: Hex;
  newActiveKey: Address;
}): Hex {
  const inner = keccak256(
    concat([
      toBytes("etzhayyim-vendor-continuity"),
      toBytes(args.vendorRootDid),
      toBytes(args.dwebHandleHash),
      toBytes(args.newActiveKey),
    ]),
  );
  return keccak256(concat([toBytes("\x19Ethereum Signed Message:\n32"), toBytes(inner)]));
}

/**
 * Hash a dweb handle ("alice.etzhayyim.com") to the bytes32 used by the
 * contract — keccak256 of the UTF-8 bytes of the handle.
 */
export function dwebHandleHash(handle: string): Hex {
  return keccak256(toBytes(handle));
}
