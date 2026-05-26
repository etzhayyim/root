// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Minimal IERC5192 interface (EIP-5192 — Minimal Soulbound NFTs).
// Used by etzhayyim Land Trust contracts to signal constitutional inalienability.
// Per ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment).
//
// EIP-5192 Interface ID: 0xb45a3c0e

pragma solidity 0.8.27;

/// @title IERC5192 — Minimal Soulbound NFTs
/// @dev EIP-5192. Signals that an NFT is locked (non-transferable).
///      etzhayyim Land Trust uses this to enforce constitutional inalienability
///      of donated land (per ADR-2605192245 Global Land Sovereignty).
interface IERC5192 {
    /// @notice Emitted when the locking status is changed to locked.
    /// @dev Constitutional invariant: this MUST emit on mint (donation) only.
    /// @param tokenId The identifier for a token.
    event Locked(uint256 tokenId);

    /// @notice Emitted when the locking status is changed to unlocked.
    /// @dev CONSTITUTIONAL: this event MUST NEVER be emitted for etzhayyim Land Trust.
    ///      Donated land is permanently locked. Implementations MUST NOT expose
    ///      any function that emits Unlocked for land NFTs.
    /// @param tokenId The identifier for a token.
    event Unlocked(uint256 tokenId);

    /// @notice Returns the locking status of a Soulbound Token.
    /// @dev For etzhayyim Land Trust: MUST return true for all valid tokenIds.
    /// @param tokenId The identifier for an SBT.
    function locked(uint256 tokenId) external view returns (bool);
}
