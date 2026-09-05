// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Minimal ECDSA signature recovery implementation for secp256k1.
// Adapted from OpenZeppelin Contracts (Apache-2.0) for zero-dependency deployment.
// Per ADR-2605172300 §8: zero external dependencies.
//
// This version returns address(0) on failure instead of reverting,
// allowing callers to handle errors with custom error types.

pragma solidity 0.8.27;

library ECDSA {
    /// @dev The signature's `v` parameter uses either:
    /// - Legacy format: 27 or 28 (no chain ID replay protection)
    /// - EIP-155 format: chainId * 2 + 35 or chainId * 2 + 36
    ///
    /// This implementation supports BOTH legacy and EIP-155 signatures.
    /// Returns address(0) if the signature is invalid.
    function tryRecover(bytes32 digest, bytes memory signature) internal pure returns (address) {
        if (signature.length != 65) {
            return address(0);
        }

        // Split the signature into r, s, and v (the standard 65-byte format)
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 0x20))
            s := mload(add(signature, 0x40))
            v := byte(0, mload(add(signature, 0x60)))
        }

        // Verify that s is in the lower half order to prevent signature
        // malleability (EIP-2). The secp256k1 curve order is:
        // 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        // Half order is:
        // 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B2070
        if (
            uint256(s) >
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B2070
        ) {
            return address(0);
        }

        // Verify that r is not zero and is less than the curve order
        if (uint256(r) == 0 || uint256(r) >= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141) {
            return address(0);
        }

        // Verify v is valid: either legacy (27, 28) or EIP-155 (>= 35)
        if (v != 27 && v != 28 && v < 35) {
            return address(0);
        }

        // Recover the address from the signature
        address recovered = ecrecover(digest, v, r, s);
        return recovered;
    }

    /// @dev Same as `tryRecover` but accepts r, s, v as separate parameters.
    ///      Returns address(0) if the signature is invalid.
    function tryRecover(bytes32 digest, bytes32 r, bytes32 s, uint8 v) internal pure returns (address) {
        if (
            uint256(s) >
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B2070
        ) {
            return address(0);
        }
        if (uint256(r) == 0 || uint256(r) >= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141) {
            return address(0);
        }
        if (v != 27 && v != 28 && v < 35) {
            return address(0);
        }
        address recovered = ecrecover(digest, v, r, s);
        return recovered;
    }

    /// @dev Legacy recover function that reverts on failure (for backward compatibility).
    function recover(bytes32 digest, bytes memory signature) internal pure returns (address) {
        address recovered = tryRecover(digest, signature);
        if (recovered == address(0)) {
            revert ECDSAInvalidSignature();
        }
        return recovered;
    }

    /// @dev Legacy recover function that reverts on failure (for backward compatibility).
    function recover(bytes32 digest, bytes32 r, bytes32 s, uint8 v) internal pure returns (address) {
        address recovered = tryRecover(digest, r, s, v);
        if (recovered == address(0)) {
            revert ECDSAInvalidSignature();
        }
        return recovered;
    }

    // -----------------------------------------------------------------------
    // Errors
    // -----------------------------------------------------------------------

    error ECDSAInvalidSignature();
    error ECDSAInvalidSignatureS();
    error ECDSAInvalidSignatureR();
    error ECDSAInvalidSignatureV();
}// CI trigger
