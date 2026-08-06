// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Minimal EIP-712 typed data hashing implementation.
// Adapted from OpenZeppelin Contracts (Apache-2.0) for zero-dependency deployment.
// Per ADR-2605172300 §8: zero external dependencies.

pragma solidity 0.8.27;

library EIP712 {
    // keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
    bytes32 private constant DOMAIN_TYPEHASH = 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f;

    /// @notice Computes the domain separator for the current contract.
    ///         Domain separator binds the signature to a specific chain and
    ///         contract address to prevent cross-chain and cross-contract replay.
    function _buildDomainSeparator(
        string memory name,
        string memory version
    ) internal view returns (bytes32) {
        return keccak256(abi.encode(
            DOMAIN_TYPEHASH,
            keccak256(bytes(name)),
            keccak256(bytes(version)),
            block.chainid,
            address(this)
        ));
    }

    /// @notice Hashes an EIP-712 typed data struct.
    /// @param domainSeparator The domain separator for this contract/chain
    /// @param structHash The hash of the typed struct (typehash + encoded data)
    /// @return The final digest to be signed (prefixed with "\x19\x01")
    function _hashTypedDataV4(
        bytes32 domainSeparator,
        bytes32 structHash
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash));
    }

    /// @notice Hashes a struct according to its EIP-712 type definition.
    ///         This is a generic helper; specific type hashes should be
    ///         defined as constants in the consuming contract.
    function _hashStruct(bytes32 typeHash, bytes memory encodedData) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(typeHash, encodedData));
    }
}